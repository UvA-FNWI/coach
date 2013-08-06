from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.db import transaction
from recommendation import recommend
from models import Recommendation
import tincan_api
import json


from pprint import pformat, pprint


# Create tincan object
USERNAME = settings.TINCAN['username']
PASSWORD = settings.TINCAN['password']
ENDPOINT = settings.TINCAN['endpoint']

tincan = tincan_api.TinCan(USERNAME, PASSWORD, ENDPOINT)


# dashboard
def index(request):
    mbox = 'mailto:5ETUPQXP1V@uva.nl'
    obj = {'agent': {'mbox': mbox}}
    tc_resp = tincan.getFilteredStatements(obj)
    statements = {}
    for s in tc_resp['statements']:
        try:
            d = s['object']['definition']
            name = d['name']['en-US']
            desc = d['description']['en-US']
            url = s['object']['id']
            statements[url] = {'mbox': s['actor']['mbox'],
                               'name': name,
                               'desc': desc,
                               'id': s['id'],
                               'verb': s['verb']['display']['en-US'],
                               'time': s['timestamp'].split(' ')[0]}
        except KeyError as e:
            print 'Error:', e
    pprint(statements)
    return render(request, 'dashboard/index.html',
                  {'statements': statements})

# Recommendations

def get_recommendations(request):
    item_hash = hash(sort(request.POST))
    Recommendation.objects.get(item_hash=item_hash)
    # FIXME do something


# Recommendation
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
