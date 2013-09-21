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
from django.db.models import Q

from models import Activity, Recommendation, LogEvent, GroupAssignment
from recommendation import recommend
from tincan_api import TinCan
from helpers import *

# Fetch TinCan credentials from settings
USERNAME = settings.TINCAN['username']
PASSWORD = settings.TINCAN['password']
ENDPOINT = settings.TINCAN['endpoint']

# Reference to TinCan verbs
COMPLETED = TinCan.VERBS['completed']['id']
PROGRESSED = TinCan.VERBS['progressed']['id']

# Reference to TinCan activity types
ASSESSMENT = TinCan.ACTIVITY_TYPES['assessment']
MEDIA = TinCan.ACTIVITY_TYPES['media']
QUESTION = TinCan.ACTIVITY_TYPES['question']

# Reference to progress URI in result/extension
PROGRESS_T = "http://uva.nl/coach/progress"

# Default barcode height
BARCODE_HEIGHT = 35

## Decorators
def identity_required(func):
    def inner(request, *args, **kwargs):
        # Fetch email from GET paramaters if present and store in session.
        email = request.GET.get('email',None)
        if email is not None:
            request.session['user'] = "mailto:%s" % (email,)

        # Fetch user from session
        user = request.session.get('user',None)

        # If no user is specified, show information on how to login
        if user is None:
            return render(request, 'dashboard/loginfirst.html',{})
        else:
            return func(request, *args, **kwargs)
    return inner

def check_group(func):
    """Decorator to check the group for A/B testing.
    Users in group A see the dashboard and users in group B do not.
    Users that are in no group will be assigned one, so that both groups differ
    at most 1 in size. If both groups are the same size, the group will be
    assigned pseudorandomly.
    """
    def inner(request, *args, **kwargs):
        # Fetch user from session
        user = request.session.get('user',None)

        # Case 1: Existing user
        try:
            assignment = GroupAssignment.objects.get(user=user)
            if assignment.group == 'A':
                return func(request, *args, **kwargs)
            else:
                return HttpResponse()
        # Case 2: New user
        except ObjectDoesNotExist:
            # Case 2a: First half of new pair,
            #          randomly pick A or B for this user.
            if GroupAssignment.objects.count() % 2 == 0:
                group = random.choice(['A', 'B'])
                if group == 'A':
                    ga = GroupAssignment(user=user, group='A')
                    ga.save()
                    return func(request, *args, **kwargs)
                else:
                    ga = GroupAssignment(user=user, group='B')
                    ga.save()
                    return HttpResponse()
            # Case 2b: Second half of new pair,
            #          choose the group that was not previously chosen.
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
                    return func(request, *args, **kwargs)
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
@identity_required
@check_group
def barcode(request, default_width=170):
    """Return an svg representing progress of an individual vs the group."""
    # Fetch user from session
    user = request.session.get('user',None)

    width = int(request.GET.get('width', default_width))
    data = {'width': width, 'height': BARCODE_HEIGHT}

    # Add values
    markers = {}
    activities = Activity.objects.filter(type=ASSESSMENT)
    for activity in activities:
        if activity.user in markers:
            markers[activity.user] += min(80, activity.value)
        else:
            markers[activity.user] = min(80, activity.value)
    if user in markers:
        data['user'] = markers[user]
        del markers[user]
    else:
        data['user'] = 0
    data['people'] = markers.values()

    # Normalise
    if len(markers) > 0:
        maximum = max(max(data['people']), data['user'])
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

@identity_required
@check_group
def index(request):
    # Fetch user from session
    user = request.session.get('user',None)

    activities = Activity.objects
    statements = map(lambda x: x._dict(),
                     activities.filter(
                         user=user).order_by('-time'))
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
        'assignments': assignments,
        'exercises': exercises,
        'video': video,
        'host': request.get_host()
    })
    response = HttpResponse(template.render(context))
    response['Access-Control-Allow-Origin'] = "*"

    event = LogEvent(type='D', user=user, data="{}")
    event.save()

    return response

@identity_required
@check_group
def get_recommendations(request, milestones, max_recs=False):
    # Fetch user from session
    user = request.session.get('user',None)

    rec_objs = Recommendation.objects
    result = []

    # Get maximum recommendations to be showed
    max_recs = int(request.GET.get('max', max_recs))

    # TODO: CHECK IS THIS OK?
    # Create exclude set of completed items
    #  these should not be recommended.
    exclude = Activity.objects.filter(
        Q(verb=COMPLETED) | Q(verb=PROGRESSED),
        value__gte=80,
        user=user
    )
    exclude = set(map(lambda x: x.activity, exclude))

    for milestone in milestones.split(','):
        if milestone not in exclude:
            recommendations = rec_objs.filter(milestone=milestone)
            for rec in recommendations:
                if rec.url not in exclude:
                    score = f_score(rec.confidence, rec.support, beta=1.5)
                    result.append({'milestone': milestone,
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
        data = json.dumps({
                "recs": map(lambda x: x['url'],result),
                "path": request.path,
                "milestone_n": len(milestones.split(',')),
                "milestones": milestones})
        event = LogEvent(type='V', user=user, data=data)
        event.save()

        return render(request, 'dashboard/recommend.html',
                  {'recommendations': result,
                   'context': event.id,
                   'host': request.get_host()})
    else:
        return HttpResponse()

## Background processes
def cache_activities(request):
    """Create a cache of the Learning Record Store by getting all items since
    the most recent one in the cache.
    """
    # Dynamic interval retrieval settings
    INTERVAL = timedelta(days=1)
    EPOCH = datetime(2013,9,3,0,0,0,0,pytz.utc)

    # Set aggregate to True if events concerning the same activity-person
    # should be aggregated into one row. This has impact for recommendations.
    aggregate = False

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

@identity_required
def track(request, defaulttarget='index.html'):
    """Track user clicks so that we may be able to improve recommendation
    relevance in the future.
    """
    # Fetch user from session
    user = request.session.get('user',None)

    # Fetch target URL from GET parameters
    target = request.GET.get('target', defaulttarget)

    # Fetch context log id from GET paramaters
    context = request.GET.get('context', None)

    if context is not None:
        try:
            context = LogEvent.objects.get(pk=int(context))
        except LogEvent.DoesNotExist:
            context = None

    event = LogEvent(type='C', user=user, data=target, context=context)
    event.save()

    return redirect(fix_url(target, request))

