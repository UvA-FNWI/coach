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
import random
import string


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


@transaction.commit_manually
def cache_activities(request):
    tincan = TinCan(USERNAME, PASSWORD, ENDPOINT)
    tc_resp = tincan.getAllStatements()
    for resp in tc_resp:
        type = resp['object']['definition']['type']
        user = resp['actor']['mbox']
        activity = resp['object']['id']
        # FIXME make
        name = resp['object']['definition']['name']['en-US']
        description = resp['object']['definition']['description']['en-US']
        if type == ASSESSMENT:
            try:
                raw = resp['result']['score']['raw']
                min = resp['result']['score']['min']
                max = resp['result']['score']['max']
                value = (raw - min) / max
            except KeyError:
                value = 0
        else:
            try:
                value = resp['result']['extensions'][PROGRESS_T]
            except KeyError:
                value = 0
        a = Activity(user=user,
                     type=type,
                     name=name,
                     description=description,
                     activity=activity,
                     value=value)
        a.save()
    transaction.commit()
    return HttpResponse()


# dashboard
def index(request, cached=True):
    # FIXME: Real login
    mbox = 'mailto:martin.latour@student.uva.nl'

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
                  {'assignments': assignments,
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
