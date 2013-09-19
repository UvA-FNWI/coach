import random
import json
import pytz
import dateutil.parser
from datetime import datetime, timedelta
from pprint import pformat

from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.db import transaction
from django.template import RequestContext, loader



from models import Activity, Recommendation, LogEvent, GroupAssignment
from recommendation import recommend
from tincan_api import TinCan
from helpers import *

USERNAME = settings.TINCAN['username']
PASSWORD = settings.TINCAN['password']
ENDPOINT = settings.TINCAN['endpoint']
COMPLETED = TinCan.VERBS['completed']['id']
ANSWERED = TinCan.VERBS['answered']['id']

PROGRESS_T = "http://uva.nl/coach/progress"

BARCODE_HEIGHT = 35
DEBUG_USER = {'email': 'm.cohen@sowiso.nl'}

## Decorators
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
                group = random.choice(['A', 'B'])
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
                    last_group = GroupAssignment.objects.order_by('-id')[0].group
                except:
                    last_group = random.choice(['A', 'B'])
                if last_group == 'A':
                    ga = GroupAssignment(user=user, group='B')
                    ga.save()
                    return HttpResponse()
                else:
                    ga = GroupAssignment(user=user, group='A')
                    ga.save()
                    return func(*args, **kwargs)
    return inner

## Bootstrap
def bootstrap(request):
    return render(request, 'dashboard/bootstrap.html',
                  {'host': request.get_host()})

def bootstrap_recommend(request, milestones):
    max_recs = int(request.GET.get('max', False))
    return render(request, 'dashboard/bootstrap_recommend.html',
                  {'milestones': milestones,
                   'max_recs': max_recs,
                   'host': request.get_host()})

## Interface
@check_group
def barcode(request, default_width=170):
    """Return an svg representing progress of an individual vs the group."""

    email = request.GET.get('email', DEBUG_USER['email'])
    mbox = 'mailto:%s' % (email,)

    width = int(request.GET.get('width', default_width))
    data = {'width': width, 'height': BARCODE_HEIGHT}

    # Add values
    people = {}
    activities = Activity.objects.all.filter(
            type=TinCan.ACTIVITY_TYPES['assessment'])
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

@check_group
def index(request):
    email = request.GET.get('email', DEBUG_USER['email'])
    activities = Activity.objects
    statements = map(lambda x: x._dict(),
                     activities.filter(
                         user="mailto:%s" % (email,)).order_by('-time'))
    statements = aggregate_statements(statements)

    for statement in statements:
        statement['activity'] = fix_url(statement['activity'],request)

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
        'video': video,
        'host': request.get_host()
    })
    response = HttpResponse(template.render(context))
    response['Access-Control-Allow-Origin'] = "*"

    event = LogEvent(type='D', user=email, data="{}")
    event.save()

    return response

@check_group
def get_recommendations(request, milestones, max_recs=False):
    rec_objs = Recommendation.objects
    result = []

    # Exclude completed items from recommendations
    email = request.GET.get('email', DEBUG_USER['email'])
    max_recs = int(request.GET.get('max', max_recs))
    seen_objs = Activity.objects.filter(user='mailto:%s' % (email,))
    ex_objs = seen_objs.exclude(verb=COMPLETED, value__gte=.8)
    ex = set(map(lambda x: x.activity, ex_objs))

    for milestone in milestones.split(','):
        recommendations = rec_objs.filter(milestone=milestone)
        for rec in recommendations:
            if rec.url not in ex:
                score = f_score(rec.confidence, rec.support, beta=1.5)
                result.append({'milestone': rec.milestone,
                             'url': rec.url,
                             'id': rand_id(),
                             'name': rec.name,
                             'desc': rec.description,
                             'm_name': rec.m_name,
                             'confidence': rec.confidence,
                             'support': rec.support,
                             'score': score})

    # Normalise support
    if len(result) > 0:
        max_sup = max(map(lambda x: x['score'], result))
        for rec in result:
            rec['score'] /= max_sup

        result.sort(key=lambda x: x['score'], reverse=True)

        if max_recs:
            result = result[:max_recs]

    # Log Recommendations viewed
    email = request.GET.get('email', '')
    user = email
    data = json.dumps({
            "recs": map(lambda x: x['url'],result),
            "path": request.path,
            "milestone_n": len(milestones.split(',')),
            "milestones": milestones,
            "seen_n": len(seen_objs),
            "rec_objs_n": rec_objs.count()})
    event = LogEvent(type='V', user=user, data=data)
    event.save()

    return render(request, 'dashboard/recommend.html',
                  {'recommendations': result,
                   'context': event.id,
                   'email': email,
                   'host': request.get_host()})

## Background processes
def cache_activities(request):
    """Create a cache of the Learning Record Store by getting all items since
    the most recent one in the cache.
    """
    # Dynamic interval retrieval settings
    INTERVAL = timedelta(days=1)
    EPOCH = datetime(2013,9,3,0,0,0,0,pytz.utc)

    aggregate = request.GET.get("aggregate","0") == "0"

    # Find most recent date
    try:
        t1 = Activity.objects.latest('time').time
    except:
        t1 = EPOCH

    # Get new data
    tincan = TinCan(USERNAME, PASSWORD, ENDPOINT)
    statements = tincan.dynamicIntervalStatementRetrieval(t1,INTERVAL)
    for statement in statements:
        type = statement['object']['definition']['type']
        user = statement['actor']['mbox']
        activity = statement['object']['id']
        verb = statement['verb']['id']
        name = statement['object']['definition']['name']['en-US']
        description = statement['object']['definition']['description']['en-US']
        time = dateutil.parser.parse(statement['timestamp'])
        try:
            raw = statement['result']['score']['raw']
            min = statement['result']['score']['min']
            max = statement['result']['score']['max']
            value = 100 * (raw - min) / max
        except KeyError:
            try:
                value = 100 * float(statement['result']['extensions'][PROGRESS_T])
            except KeyError:
                value = 0
        if aggregate:
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
        else:
            a, created = Activity.objects.get_or_create(user=user,
                                                        verb=verb,
                                                        activity=activity,
                                                        time=time)
            if created:
                a.verb = verb
                a.type = type
                a.value = value
                a.name = name
                a.description = description
                a.time = time
                a.save()
    return HttpResponse()

def generate_recommendations(request):
    minsup = int(request.GET.get('minsup', 2))
    minconf = int(request.GET.get('minconf', .3))
    gamma = int(request.GET.get('gamma', .8))

    # Mine recommendations
    recommendations, names = recommend(minsup=2, minconf=.3, gamma=.8)

    # Add recommendations to database
    Recommendation.objects.all().delete()
    for r in recommendations:
        item_hash = hash(r['antecedent'])
        rec = Recommendation(item_hash=item_hash,
                             confidence=r['confidence'],
                             support=r['support'],
                             milestone=r['milestone'],
                             m_name=names[r['milestone']][0],
                             name=names[r['consequent']][0],
                             url=r['consequent'],
                             description=names[r['consequent']][1])
        rec.save()

    event = LogEvent(type='G', user='all', data=json.dumps(recommendations))
    event.save()
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

    return redirect(fix_url(target, request))
