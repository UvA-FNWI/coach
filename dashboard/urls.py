from django.conf.urls import patterns, url
from django.contrib import admin
admin.autodiscover()

from dashboard import views

urlpatterns = patterns('',
        url(r'^$', views.index, name='index'),
        url(r'^cache$', views.cache_activities, name='cache'),
        url(r'^barcode$', views.barcode, name='barcode'),
        url(r'^recommendations$',
            views.generate_recommendations,
            name='generate recommendations'),

        url(r'^bootstrap$',
            views.bootstrap,
            name='bootstrap'),
        url(r'^bootstrap/recommend/(?P<milestones>.+)$',
            views.bootstrap_recommend,
            name='bootstrap recommendations'),

        url(r'^recommend/(?P<milestones>.+)$',
            views.get_recommendations,
            name='get recommendations'),

        url(r'^track$', views.track, name='track'),
        )
