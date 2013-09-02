from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.db import transaction
from django.template import RequestContext, loader
from recommendation import recommend
from models import Activity, Recommendation, LogEvent, rand_id, GroupAssignment
from tincan_api import TinCan
import random
import json
import re
import dateutil.parser

from pprint import pformat, pprint

DEBUG_USER = {'email': 'm.cohen@sowiso.nl'}


# Create tincan object
USERNAME = settings.TINCAN['username']
PASSWORD = settings.TINCAN['password']
ENDPOINT = settings.TINCAN['endpoint']

COMPLETED = TinCan.VERBS['completed']['id']
ANSWERED = TinCan.VERBS['answered']['id']
QUESTION = TinCan.ACTIVITY_TYPES['question']
ASSESSMENT = TinCan.ACTIVITY_TYPES['assessment']
PROGRESS_T = "http://uva.nl/coach/progress"

# To ensure iktel login
PRE_URL = "https://www.google.com/accounts/ServiceLogin?service=ah" +\
          "&passive=true&continue=https://appengine.google.com/_ah/" +\
          "conflogin%3Fcontinue%3Dhttp://www.iktel.nl/postlogin%253F" +\
          "continue%253D"

BARCODE_HEIGHT = 35


def parse_statements(objects):
    """Get data from statements necessary for displaying."""
    r = {}
    for s in objects:
        try:
            type = s['object']['definition']['type']
        except KeyError:
            type = ''
        try:        # Assessment    - score
            raw = s['result']['score']['raw']
            min = s['result']['score']['min']
            max = s['result']['score']['max']
            value = 100 * (raw - min) / max
        except KeyError:
            try:    # Question      - result
                value = float(s['result']['extensions'][PROGRESS_T]) * 100
            except KeyError:
                value = None
        try:
            verb_t = s['verb']['id']
            d = s['object']['definition']
            name = d['name']['en-US']
            desc = d['description']['en-US']
            url = s['object']['id']
            if not verb_t == ANSWERED and ((url not in r) or
                                           verb_t == COMPLETED):
                r[url] = {'user': s['actor']['mbox'],
                          'type': type,
                          'url': url,
                          'value': value,
                          'name': name,
                          'desc': desc,
                          'id': rand_id()}
        except KeyError as e:
            print('Error:', e)
    return r.values()


def split_statements(statements):
    """Split statements by type:
        assignments
        exercises
        video
        rest
    """
    result = {}
    result['assignments'] = []
    result['exercises'] = []
    result['video'] = []
    result['rest'] = []
    for statement in statements:
        try:
            type = statement['type']
        except KeyError:
            continue
        if type == TinCan.ACTIVITY_TYPES['assessment']:
            result['assignments'].append(statement)
        elif type == TinCan.ACTIVITY_TYPES['question']:
            result['exercises'].append(statement)
        elif type == TinCan.ACTIVITY_TYPES['media']:
            result['video'].append(statement)
        else:
            result['rest'].append(statement)
    return result


# TODO: Remove. This is just for testing
def getallen(request):
    return render(request, 'dashboard/getallen.html',
                  {'host': request.get_host()})


def barcode(request, default_width=170):
    """Return an svg representing progress of an individual vs the group."""

    email = request.GET.get('email', DEBUG_USER['email'])
    mbox = 'mailto:%s' % (email,)

    width = int(request.GET.get('width', default_width))

    all = Activity.objects
    data = {'width': width, 'height': BARCODE_HEIGHT}

    # Add values
    people = {}
    activities = all.filter(type=TinCan.ACTIVITY_TYPES['assessment'])
    for activity in activities:
        if activity.user in people:
            people[activity.user] += min(80, activity.value)
        else:
            people[activity.user] = min(80, activity.value)
    if mbox in people:
        data['user'] = people[mbox]
        del people[mbox]
    else:
        data['user'] = 0
    data['people'] = people.values()

    # Normalise
    if len(people) > 0:
        maximum = max(max(people.values()), data['user'])
        data['user'] /= maximum
        data['user'] *= width
        data['user'] = int(data['user'])
        for i, person in enumerate(data['people']):
            data['people'][i] /= maximum
            data['people'][i] *= width
            data['people'][i] = int(data['people'][i])
    else:
        # if no other persons have been active
        # then user is assumed to be in the lead.
        # This is regardless if the user has done anything at all.
        data['user'] = width

    return render(request, 'dashboard/barcode.svg', data)


# user+activity is unique, update
@transaction.commit_manually
def cache_activities(request):
    """Create a cache of the Learning Record Store by getting all items since
    the most recent one in the cache.
    Save only latest completed actions and only progress for uncompleted items
    per user.
    """
    # Find most recent date
    try:
        most_recent_time = Activity.objects.latest('time').time
    except:
        most_recent_time = None

    # Get new data
    tincan = TinCan(USERNAME, PASSWORD, ENDPOINT)
    if most_recent_time:
        tc_resp = tincan.getFilteredStatements({'since': most_recent_time})
    else:
        tc_resp = tincan.getAllStatements()

    for resp in tc_resp:
        type = resp['object']['definition']['type']
        user = resp['actor']['mbox']
        activity = resp['object']['id']
        verb = resp['verb']['id']
        name = resp['object']['definition']['name']['en-US']
        description = resp['object']['definition']['description']['en-US']
        time = dateutil.parser.parse(resp['timestamp'])
        try:
            raw = resp['result']['score']['raw']
            min = resp['result']['score']['min']
            max = resp['result']['score']['max']
            value = 100 * (raw - min) / max
        except KeyError:
            try:
                value = 100 * float(resp['result']['extensions'][PROGRESS_T])
            except KeyError:
                value = 0
        a, created = Activity.objects.get_or_create(user=user,
                                                    activity=activity)
        # Don't overwrite completed except with other completed events
        # and only overwite with more recent timestamp
        if created or (time > a.time and
                       (verb == COMPLETED or a.verb != COMPLETED)):
            a.verb = verb
            a.type = type
            a.value = value
            a.name = name
            a.description = description
            a.time = time
            a.save()
    transaction.commit()
    return HttpResponse()


def fix_url(url):
    """Make sure the iktel lings go through the appengine login first."""
    if re.search('www.iktel.nl', url):
        return PRE_URL + url
    return url


def check_group(func):
    """Decorator to check the group for A/B testing.
    Users in group A see the dashboard and users in group B do not.
    Users that are in no group will be assigned one, so that both groups differ
    at most 1 in size. If both groups are the same size, the group will be
    assigned pseudorandomly.
    """
    def inner(*args, **kwargs):
        email = args[0].GET.get('email', '')
        user = email
        # Existing user
        try:
            assignment = GroupAssignment.objects.get(user=user)
            if assignment.group == 'A':
                return func(*args, **kwargs)
            else:
                return HttpResponse()
        # New user
        except ObjectDoesNotExist:
            # First half of new pair
            if GroupAssignment.objects.count() % 2 == 0:
                group = bool(random.choice(['A', 'B']))
                if group == 'A':
                    ga = GroupAssignment(user=user, group='A')
                    ga.save()
                    return func(*args, **kwargs)
                else:
                    ga = GroupAssignment(user=user, group='B')
                    ga.save()
                    return HttpResponse()
            # Second half of new pair
            else:
                try:
                    last_group = GroupAssignment.objects.revers()[0].group
                except:
                    last_group = bool(random.choice(['A', 'B']))
                if last_group == 'A':
                    ga = GroupAssignment(user=user, group='B')
                    ga.save()
                    return HttpResponse()
                else:
                    ga = GroupAssignment(user=user, group='A')
                    ga.save()
                    return func(*args, **kwargs)
    return inner


@check_group
def index(request, cached=True):
    email = request.GET.get('email', DEBUG_USER['email'])
    activities = Activity.objects
    if cached:
        statements = map(lambda x: Activity._dict(x),
                         activities.filter(
                             user="mailto:%s" % (email,)).order_by('-time'))
    else:
        tincan = TinCan(USERNAME, PASSWORD, ENDPOINT)
        obj = {'agent': {'mbox': 'mailto:%s' % email}}
        tc_resp = tincan.getFilteredStatements(obj)
        statements = parse_statements(tc_resp)

    for statement in statements:
        statement['url'] = fix_url(statement['url'])

    statements = split_statements(statements)

    assignments = statements['assignments']
    exercises = statements['exercises']
    video = statements['video']

    template = loader.get_template('dashboard/index.html')
    context = RequestContext(request, {
        'barcode_height': BARCODE_HEIGHT,
        'email': email,
        'assignments': assignments,
        'exercises': exercises,
        'video': video
    })
    response = HttpResponse(template.render(context))
    response['Access-Control-Allow-Origin'] = "*"
    return response


def bootstrap_recommend(request, milestones):
    return render(request, 'dashboard/bootstrap_recommend.html',
                  {'milestones': milestones,
                   'host': request.get_host()})


def bootstrap(request):
    return render(request, 'dashboard/bootstrap.html',
                  {'host': request.get_host()})


def f_score(confidence, support, beta=1):
    return (1 + beta ** 2) * ((confidence * support) /
                              (beta ** 2 * confidence + support))


@check_group
def get_recommendations(request, milestones, max_recs=False):
    rec_objs = Recommendation.objects
    recs = []

    # Exclude completed items from recommendations
    email = request.GET.get('email', DEBUG_USER['email'])
    seen_objs = Activity.objects.filter(user='mailto:%s' % (email,))
    ex_objs = seen_objs.exclude(verb=COMPLETED, value__gte=.8)
    ex = set(map(lambda x: x.activity, seen_objs))

    for milestone in milestones.split(','):
        tmp = rec_objs.filter(milestone=milestone)
        for rec in tmp:
            if rec.url not in ex:
                score = f_score(rec.confidence, rec.support, beta=1.5)
                recs.append({'milestone': rec.milestone,
                             'url': rec.url,
                             'id': rand_id(),
                             'name': rec.get_name(),
                             'desc': rec.get_desc(),
                             'm_name': rec.get_m_name(),
                             'confidence': rec.confidence,
                             'support': rec.support,
                             'score': score})

    # Normalise support
    max_sup = max(map(lambda x: x['score'], recs))
    for rec in recs:
        rec['score'] /= max_sup

    recs.sort(key=lambda x: x['score'], reverse=True)

    if max_recs:
        recs = recs[:max_recs]

    # Log Recommendations viewed
    email = request.GET.get('email', '')
    user = email
    data = json.dumps(map(lambda x: x['url'], recs))
    event = LogEvent(type='V', user=user, data=data)
    event.save()

    return render(request, 'dashboard/recommend.html',
                  {'recommendations': recs,
                   'context': event.id,
                   'email': email,
                   'host': request.get_host()})


@transaction.commit_manually
def generate_recommendations(request):
    from_cache = int(request.GET.get('c', False))
    if from_cache:
        cache_activities(request)
        # TODO: proper data
        activities = Activity.objects.filter()
        recommendations, names = recommend(activities=activities,
                                           recommendationfunction='trail',
                                           minsup=2, minconf=.3, gamma=.8)
    else:
        recommendations, names = recommend(recommendationfunction='trail',
                                           minsup=2, minconf=.3, gamma=.8)
    # Add recommendations to database
    Recommendation.objects.all().delete()
    i = 0
    for r in recommendations:
        item_hash = hash(r['antecedent'])
        confidence = r['confidence']
        support = r['support']
        milestone = r['milestone']
        # Store each recommendation separately
        url = r['consequent']
        name = names[url][0]
        description = names[url][1]
        i += 1
        rec = Recommendation(item_hash=item_hash,
                             confidence=confidence,
                             support=support,
                             milestone=milestone,
                             m_name=names[milestone],
                             name=name,
                             url=url,
                             description=description)
        rec.save()

    event = LogEvent(type='G', user='all', data=json.dumps(recommendations))
    event.save()

    transaction.commit()
    return HttpResponse(pformat(recommendations))


def track(request, defaulttarget='index.html'):
    """Track user clicks so that we may be able to improve recommendation
    relevance in the future.
    """
    target = request.GET.get('target', defaulttarget)
    context = int(request.GET.get('context', ''))
    email = request.GET.get('email', '')
    user = email

    try:
        context = LogEvent.objects.get(pk=context)
    except LogEvent.DoesNotExist:
        #do something
        pass

    event = LogEvent(type='C', user=user, data=target, context=context)
    event.save()

    return redirect(fix_url(target))
