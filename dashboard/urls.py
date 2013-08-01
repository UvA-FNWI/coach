from django.conf.urls import patterns, url

from dashboard import views

urlpatterns = patterns('',
        url(r'^$', views.index, name='index'),
        url(r'^apriori/$', views.apriori, name='apriori'),
        url(r'^apriori/(?P<minsup>\d+(.\d+)?)/$', views.apriori, name='apriori'),
        url(r'^api/statements$', views.tincan_get, name='tincan_get'),
        )
