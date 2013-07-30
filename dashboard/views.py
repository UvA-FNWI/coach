from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
#from recommendation import apriori


def index(request):
    return render(request, 'dashboard/index.html', {})


def apriori(request, minsup=0):
    # apriori.apriori(float(minsup))
    return HttpResponse("apriori, minsup=%s" % float(minsup))
