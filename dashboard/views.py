from django.http import HttpResponse
from recommendation import apriori


def index(request):
    return HttpResponse()


def apriori(request, minsup=0):
    apriori.apriori(minsup)
    return HttpResponse("apriori, minsup=%s" % minsup)
