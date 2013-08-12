from django.conf.urls import patterns, url
from django.contrib import admin
admin.autodiscover()

from dashboard import views

urlpatterns = patterns('',
        url(r'^$', views.index, name='index'),
        url(r'^getallen$', views.getallen, name='getallen'),
        url(r'^recommendations$', views.generate_recommendations,
            name='generate recommendations'),
        url(r'^recommend$', views.get_recommendations,
            name='get recommendations'),
        #url(r'^apriori/(?P<minsup>\d+(.\d+)?)/$', views.apriori, name='apriori'),
        )
