from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.db import transaction
from recommendation import recommend
from models import Recommendation
from tincan_api import TinCan
import json


from pprint import pformat, pprint


# Create tincan object
USERNAME = settings.TINCAN['username']
PASSWORD = settings.TINCAN['password']
ENDPOINT = settings.TINCAN['endpoint']


"""
def parse_statements(objects, view_all=False):
    r = []
    uris = set()
    for s in objects:
        try:
            d = s['object']['definition']
            name = d['name']['en-US']
            desc = d['description']['en-US']
            url = s['object']['id']
            if view_all or (url not in uris):
                r.append({'mbox': s['actor']['mbox'],
                          'url': url,
                          'name': name,
                          'desc': desc,
                          'id': s['id'],
                          'verb': s['verb']['display']['en-US'],
                          'time': s['timestamp'].split(' ')[0]})
                uris.add(url)
            elif not view_all:
                uris.add(url)
        except KeyError as e:
            print 'Error:', e
    return r
"""


def parse_statements(objects):
    COMPLETED = TinCan.VERBS['completed']['id']
    ANSWERED = TinCan.VERBS['answered']['id']
    r = {}
    for s in objects:
        try:
            verb_t = s['object']['definition']['type']
            d = s['object']['definition']
            name = d['name']['en-US']
            desc = d['description']['en-US']
            url = s['object']['id']
            if not verb_t == ANSWERED and ((url not in r) or verb_t == COMPLETED):
                r[url] = {'mbox': s['actor']['mbox'],
                                    'url': url,
                                    'name': name,
                                    'desc': desc,
                                    'id': s['id'],
                                    'verb': s['verb']['display']['en-US'],
                                    'time': s['timestamp'].split(' ')[0]}
        except KeyError as e:
            print 'Error:', e
    print r.values()
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


# dashboard
def index(request):
    tincan = TinCan(USERNAME, PASSWORD, ENDPOINT)
    mbox = 'mailto:martin.latour@student.uva.nl'
    obj = {'agent': {'mbox': mbox}}
    #tc_resp = tincan.getFilteredStatements(obj)
    tc_resp = tincan.getAllStatements()
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
