from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login
from django.conf import settings
from recommendation.recommend import recommend
import tincan_api
import json


# Create tincan object
USERNAME = settings.TINCAN['username']
PASSWORD = settings.TINCAN['password']
ENDPOINT = settings.TINCAN['endpoint']

tincan = tincan_api.TinCan(USERNAME, PASSWORD, ENDPOINT)


# dashboard
def index(request):
    return render(request, 'dashboard/index.html',
                  {'session': request.session})


# Recommendations
def apriori(request):
    recommend.recommend


# TinCan
def tincan_get(request):
    obj = {'actor': {'name': request.user, 'objectType': 'Agent'}}
    tc_resp = tincan.getFilteredStatements(obj)
    return HttpResponse(json.dumps(tc_resp['statements']))
