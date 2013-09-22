import random
import json
import pytz
import dateutil.parser
from datetime import datetime, timedelta
from pprint import pformat
from hashlib import md5

from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.conf import settings
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
        paramlist = request.GET.get('paramlist', None)
        email = request.GET.get('email', None)
        param_hash = request.GET.get('hash', None)
        if paramlist is not None:
            hash_contents = []
            for param in paramlist.split(","):
                if param == "pw":
                    hash_contents.append(settings.AUTHENTICATION_SECRET)
                else:
                    hash_contents.append(request.GET.get(param, ""))
            hash_string = md5(",".join(hash_contents)).hexdigest().upper()
            if hash_string == param_hash and email is not None:
                request.session['user'] = "mailto:%s" % (email, )

        # Fetch user from session
        user = request.session.get('user', None)

        # If no user is specified, show information on how to login
        if user is None:
            return render(request, 'dashboard/loginfirst.html', {})
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
        user = request.session.get('user', None)

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
                    assignment = GroupAssignment(user=user, group='A')
                    assignment.save()
                    return func(request, *args, **kwargs)
                else:
                    assignment = GroupAssignment(user=user, group='B')
                    assignment.save()
                    return HttpResponse()
            # Case 2b: Second half of new pair,
            #          choose the group that was not previously chosen.
            else:
                try:
                    last_group = GroupAssignment.objects.order_by('-id')[0].group
                except:
                    last_group = random.choice(['A', 'B'])
                if last_group == 'A':
                    assignment = GroupAssignment(user=user, group='B')
                    assignment.save()
                    return HttpResponse()
                else:
                    assignment = GroupAssignment(user=user, group='A')
                    assignment.save()
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
    user = request.session.get('user', None)

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
        for i in range(len(data['people'])):
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
    user = request.session.get('user', None)

    activities = Activity.objects.filter(user=user).order_by('-time')
    statements = map(lambda x: x._dict(), activities)
    statements = aggregate_statements(statements)

    for statement in statements:
        statement['activity'] = fix_url(statement['activity'], request)

    statements = split_statements(statements)

    assignments = statements['assignments']
    exercises = statements['exercises']
    exercises.sort(key = lambda x: x['value'])
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
def get_recommendations(request, milestones, max_recommendations=False):
    # Fetch user from session
    user = request.session.get('user', None)

    # Get maximum recommendations to be showed
    max_recommendations = int(request.GET.get('max', max_recommendations))

    # Fetch activities that can be perceived as seen by the user
    seen = Activity.objects.filter(
        Q(verb=COMPLETED) | Q(verb=PROGRESSED),
        value__gte=30,
        user=user
    )
    # Futher filter that list to narrow it down to activities that can be
    # perceived as being done by the user.
    done = seen.filter(value__gte=80)

    # Preprocess the seen and done sets to be used later
    seen = set(map(lambda x: hash(x.activity), seen))
    done = set(map(lambda x: x.activity, done))

    # Init dict containing final recommendations
    recommendations = {}

    # For every milestone we want to make recommendations for:
    for milestone in milestones.split(','):
        # Make sure the milestone is not already passed
        if milestone not in done:
            # Fetch list of rules from the context of this milestone.
            # Rules contain antecedent => consequent associations with a
            # certain amount of confidence and support. The antecedent is
            # stored as a hash of the activities in the antecedent. The
            # consequent is the activity that is recommended if you did the
            # activities in the consequent. At the moment only the trail
            # recommendation algorithm is used, which has antecedents of only
            # one activity. If this was different, the antecedent hash check
            # would have to include creating powersets of certain length.
            rules = Recommendation.objects.filter(milestone=milestone)
            # For each recommendation rule
            for rule in rules:
                # If the LHS applies and the RHS is not already done
                if rule.antecedent_hash in seen and \
                        rule.consequent not in done:
                    # If the consequent was already recommended earlier
                    if rule.consequent in recommendations:
                        # Fetch earlier recommendation
                        earlier_rule = recommendations[rule.consequent]
                        # Calculate the original total by with the support was
                        # divided in order to get the confidence of the
                        # the earlier recommendation
                        earlier_total = earlier_rule['support']
                        earlier_total /= float(earlier_rule['confidence'])
                        total = earlier_total + rule.support/rule.confidence
                        # Calculate combined values
                        support = earlier_rule['support'] + rule.support
                        confidence = support / float(total)
                        score = f_score(confidence, support, beta=1.5)
                        # Update the earlier recommendation to combine both
                        earlier_rule['support'] = support
                        earlier_rule['confidence'] = confidence
                        earlier_rule['score'] = score
                    # If the consequent is recommended for the first time
                    else:
                        # Calculate F-score
                        score = f_score(rule.confidence, rule.support, beta=1.5)
                        # Store recommendation for this consequent
                        recommendations[rule.consequent] = {
                            'milestone': milestone,
                            'url': rule.consequent,
                            'id': rand_id(),
                            'name': rule.name,
                            'desc': rule.description,
                            'm_name': rule.m_name,
                            'confidence': rule.confidence,
                            'support': rule.support,
                            'score': score
                        }
    # Convert to a list of recommendations.
    # The lookup per consequent is no longer necessary
    recommendations = recommendations.values()

    # If recommendations were found
    if len(recommendations) > 0:
        # Normalise score
        max_score = max(map(lambda x: x['score'], recommendations))
        for recommendation in recommendations:
            recommendation['score'] /= max_score

        # Sort the recommendations using their f-scores
        recommendations.sort(key = lambda x: x['score'], reverse=True)

        # Cap the number of recommendations if applicable.
        if max_recommendations:
            recommendations = recommendations[:max_recommendations]

        # Log Recommendations viewed
        data = json.dumps({
                "recs": map(lambda x: x['url'], recommendations),
                "path": request.path,
                "milestone_n": len(milestones.split(',')),
                "milestones": milestones})
        event = LogEvent(type='V', user=user, data=data)
        event.save()

        # Render the result
        return render(request, 'dashboard/recommend.html',
                  {'recommendations': recommendations,
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
    EPOCH = datetime(2013, 9, 3, 0, 0, 0, 0, pytz.utc)

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
    statements = tincan.dynamicIntervalStatementRetrieval(t1, INTERVAL)
    for statement in statements:
        statement_type = statement['object']['definition']['type']
        user = statement['actor']['mbox']
        activity = statement['object']['id']
        verb = statement['verb']['id']
        name = statement['object']['definition']['name']['en-US']
        description = statement['object']['definition']['description']['en-US']
        time = dateutil.parser.parse(statement['timestamp'])
        try:
            raw_score = statement['result']['score']['raw']
            min_score = statement['result']['score']['min']
            max_score = statement['result']['score']['max']
            value = 100 * (raw_score - min_score) / max_score
        except KeyError:
            try:
                value = 100 * float(statement['result']['extensions'][PROGRESS_T])
            except KeyError:
                # If no information is given about the end result then assume a
                # perfect score was acquired when the activity was completed,
                # and no score otherwise.
                if verb == COMPLETED:
                    value = 100
                else:
                    value = 0
        if aggregate:
            a, created = Activity.objects.get_or_create(user=user,
                                                        activity=activity)
            # Don't overwrite completed except with other completed events
            # and only overwite with more recent timestamp
            if created or (time > a.time and
                           (verb == COMPLETED or a.verb != COMPLETED)):
                a.verb = verb
                a.type = statement_type
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
                a.type = statement_type
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
    recommendations, names = recommend(
            minsup=minsup,
            minconf=minconf,
            gamma=gamma
    )

    # Add recommendations to database
    Recommendation.objects.all().delete()
    for recommendation in recommendations:
        model = Recommendation(
            antecedent_hash = hash(recommendation['antecedent']),
            confidence = recommendation['confidence'],
            support = recommendation['support'],
            milestone = recommendation['milestone'],
            m_name = names[recommendation['milestone']][0],
            name = names[recommendation['consequent']][0],
            consequent = recommendation['consequent'],
            description = names[recommendation['consequent']][1])
        model.save()

    event = LogEvent(type='G', user='all', data=json.dumps(recommendations))
    event.save()
    return HttpResponse(pformat(recommendations))

@identity_required
def track(request, defaulttarget='index.html'):
    """Track user clicks so that we may be able to improve recommendation
    relevance in the future.
    """
    # Fetch user from session
    user = request.session.get('user', None)

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

