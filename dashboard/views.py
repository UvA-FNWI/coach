from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login
from django.conf import settings
#from recommendation import apriori
import tincan_api
import json


# Create tincan object
USERNAME = settings.TINCAN['username']
PASSWORD = settings.TINCAN['password']
ENDPOINT = settings.TINCAN['endpoint']

tincan = tincan_api.TinCan(USERNAME, PASSWORD, ENDPOINT)

from pprint import pprint
# dashboard
def index(request):
    pprint(request)
    print request.session
    return render(request, 'dashboard/index.html',
                  {'session': request.session})


# Recommendations
def apriori(request, minsup=0):
    # apriori.apriori(float(minsup))
    return HttpResponse("apriori, minsup=%s" % float(minsup))


# TinCan
def tincan_all(request):
    obj = {'actor': {'name': request.user, 'objectType': 'Agent'}}
    tc_resp = tincan.getFilteredStatements(obj)
    return HttpResponse(json.dumps(tc_resp['statements']))

def tincan_filtered(request):
    tc_resp = tincan.getFilteredStatements(request.GET)
    print tc_resp
    return HttpResponse(tc_resp)

def tincan_id(request, statement_id):
    tc_resp = tincan.getStatementByID(statement_id)
    return HttpResponse(tc_resp)

def tincan_submit(request):
    post = request.POST
    if isinstance(post, list):
        tc_resp = tincan.submitStatementList(post)
    else:
        tc_resp = tincan.submitStatement(post)
    return HttpResponse(tc_resp)
