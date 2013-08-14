from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.db import transaction
from recommendation import recommend
from models import Recommendation, Activity
from tincan_api import TinCan
import json
import re


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
    r = {}
    for s in objects:
        try:
            type = s['object']['definition']['type']
        except KeyError:
            type = ''
        if type == ASSESSMENT:
            try:
                raw = s['result']['score']['raw']
                min = s['result']['score']['min']
                max = s['result']['score']['max']
                score = 100 * (raw - min) / max
            except KeyError:
                score = None
        else:
            score = None
        try:
            progress = float(s['result']['extensions'][PROGRESS_T]) * 100
        except KeyError:
            progress = None
        try:
            verb_t = s['verb']['id']
            d = s['object']['definition']
            name = d['name']['en-US']
            desc = d['description']['en-US']
            url = s['object']['id']
            # HARDCODE LOGIN HACK FOR PERCEPTUM
            if re.search('www.iktel.nl', url):
                url = pre_url + url
            if not verb_t == ANSWERED and ((url not in r) or verb_t == COMPLETED):
                r[url] = {'mbox': s['actor']['mbox'],
                          'score': score,
                          'progress': progress,
                          'url': url,
                          'name': name,
                          'desc': desc,
                          'id': s['id'],
                          'verb': s['verb']['display']['en-US'],
                          'time': s['timestamp'].split(' ')[0]}
        except KeyError as e:
            print 'Error:', e
    return r.values()


def split_statements(statements):
    r = {}
    r['assignments'] = []
    r['exercises'] = []
    r['video'] = []
    r['rest'] = []
    for s in statements:
        try:
            type = s['object']['definition']['type']
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


# FIXME: This is just for testing
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
                     activity=activity,
                     value=value)
        a.save()
    transaction.commit()
    return HttpResponse()


# dashboard
def index(request):
    tincan = TinCan(USERNAME, PASSWORD, ENDPOINT)
    # FIXME: Real login
    mbox = 'mailto:martin.latour@student.uva.nl'
    obj = {'agent': {'mbox': mbox}}
    tc_resp = tincan.getFilteredStatements(obj)
    #tc_resp = tincan.getAllStatements()  # debug
    statements = split_statements(tc_resp)

    assignments = parse_statements(statements['assignments'])
    exercises = parse_statements(statements['exercises'])
    video = parse_statements(statements['video'])

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
