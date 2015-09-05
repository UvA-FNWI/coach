from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^cache/?$', 'dashboard.views.cache_activities', name='cache'),
    url(r'^barcode/?$', 'dashboard.views.barcode', name='barcode'),
    url(r'^admin/', include(admin.site.urls)),
)
