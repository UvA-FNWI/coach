from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.db import transaction
from recommendation import recommend
from models import Activity, Recommendation, rand_id
from tincan_api import TinCan
import json
import re
import dateutil.parser


from pprint import pformat, pprint


# Create tincan object
USERNAME = settings.TINCAN['username']
PASSWORD = settings.TINCAN['password']
ENDPOINT = settings.TINCAN['endpoint']

COMPLETED = TinCan.VERBS['completed']['id']
ANSWERED = TinCan.VERBS['answered']['id']
QUESTION = TinCan.ACTIVITY_TYPES['question']
ASSESSMENT = TinCan.ACTIVITY_TYPES['assessment']
PROGRESS_T = "http://uva.nl/coach/progress"
pre_url = "https://www.google.com/accounts/ServiceLogin?service=ah" +\
          "&passive=true&continue=https://appengine.google.com/_ah/" +\
          "conflogin%3Fcontinue%3Dhttp://www.iktel.nl/postlogin%253F" +\
          "continue%253D"

BARCODE_HEIGHT = 30

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
            # TODO: make less ugly
            # HARDCODE LOGIN HACK FOR PERCEPTUM
            if re.search('www.iktel.nl', url):
                url = pre_url + url
            if not verb_t == ANSWERED and ((url not in r) or verb_t == COMPLETED):
                r[url] = {'user': s['actor']['mbox'],
                          'type': type,
                          'url': url,
                          'value': value,
                          'name': name,
                          'desc': desc,
                          'id': rand_id()}
        except KeyError as e:
            print 'Error:', e
    return r.values()


def split_statements(statements):
    """Split statements by type:
        assignments
        exercises
        video
        rest
    """
    r = {}
    r['assignments'] = []
    r['exercises'] = []
    r['video'] = []
    r['rest'] = []
    for s in statements:
        try:
            type = s['type']
        except:
            continue
        if type == TinCan.ACTIVITY_TYPES['assessment']:
            r['assignments'].append(s)
        elif type == TinCan.ACTIVITY_TYPES['question']:
            r['exercises'].append(s)
        elif type == TinCan.ACTIVITY_TYPES['media']:
            r['video'].append(s)
        else:
            r['rest'].append(s)
    return r


# TODO: Remove. This is just for testing
def getallen(request):
    return render(request, 'dashboard/getallen.html', {})


def barcode(request, width=170):
    """Return an svg representing progress of an individual vs the group."""

    email = request.GET.get('email','m.cohen@sowiso.nl');
    mbox = 'mailto:%s' % (email,)

    all = Activity.objects
    data = {'width': width, 'height':BARCODE_HEIGHT}

    # Add values
    people = {}
    activities = all.filter(type=TinCan.ACTIVITY_TYPES['assessment'])
    for activity in activities:
        if activity.user in people:
            people[activity.user] += min(80, activity.value)
        else:
            people[activity.user] = min(80, activity.value)
    data['user'] = people[mbox]
    data['people'] = people.values()

    # Normalise
    maximum = max(people.values())
    data['user'] /= maximum
    data['user'] *= width
    data['user'] = int(data['user'])
    for i, person in enumerate(data['people']):
        data['people'][i] /= maximum
        data['people'][i] *= width
        data['people'][i] = int(data['people'][i])

    return render(request, 'dashboard/barcode.svg', data)


# user+activity is unique, update
@transaction.commit_manually
def cache_activities(request):
    """Create a cache of the Learning Record Store by getting all items since
    the most recent one in the cache.
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
        if type == ASSESSMENT:
            try:
                raw = resp['result']['score']['raw']
                min = resp['result']['score']['min']
                max = resp['result']['score']['max']
                value = 100 * (raw - min) / max
            except KeyError:
                value = 0
        else:
            try:
                value = 100 * float(resp['result']['extensions'][PROGRESS_T])
            except KeyError:
                value = 0
        a, created = Activity.objects.get_or_create(user=user,
                                                    activity=activity)
        # Don't overwrite completed; only overwite with more recent timestamp
        if created or (time > a.time and a.verb != COMPLETED):
            a.verb = verb
            a.type = type
            a.value = value
            a.name = name
            a.description = description
            a.time = time
            a.save()
    transaction.commit()
    return HttpResponse()


# dashboard
def index(request, cached=True):
    email = request.GET.get('email','m.cohen@sowiso.nl');
    mbox = 'mailto:%s' % (email,)

    if cached:
        statements = split_statements(map(lambda x: Activity._dict(x),
                                          Activity.objects.filter(user=mbox)))
    else:
        tincan = TinCan(USERNAME, PASSWORD, ENDPOINT)
        obj = {'agent': {'mbox': mbox}}
        tc_resp = tincan.getFilteredStatements(obj)
        #tc_resp = tincan.getAllStatements()  # debug
        statements = split_statements(parse_statements(tc_resp))


    assignments = statements['assignments']
    exercises = statements['exercises']
    video = statements['video']

    return render(request, 'dashboard/index.html',
                  {'barcode_height': BARCODE_HEIGHT,
                   'email':email,
                   'assignments': assignments,
                   'exercises': exercises,
                   'video': video})


# Recommendations
def get_recommendations(request):
    item_hash = hash(sort(request.POST))
    Recommendation.objects.get(item_hash=item_hash)
    # FIXME do something


@transaction.commit_manually
def generate_recommendations(request):
    r_list, r_dict = recommend(minsup=4, minconf=.5)

    # Add recommendations to database
    Recommendation.objects.all().delete()
    i = 0
    for r in r_list:
        item_hash = hash(r['antecedent'])
        confidence = r['confidence']
        support = r['support']
        milestone = r['milestone']
        # Store each recommendation separately
        for url in r['consequent']:
            name = r_dict[url][0]
            description = r_dict[url][1]
            i += 1
            print 'adding rule:', i
            rec = Recommendation(item_hash=item_hash,
                                 confidence=confidence,
                                 support=support,
                                 milestone=milestone,
                                 name=name,
                                 url=url,
                                 description=description)
            rec.save()

    transaction.commit()
    return HttpResponse(pformat(r_list))
