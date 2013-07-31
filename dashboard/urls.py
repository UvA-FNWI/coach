from django.conf.urls import patterns, url

from dashboard import views

urlpatterns = patterns('',
        url(r'^$', views.index, name='index'),
        url(r'^apriori/$', views.apriori, name='apriori'),
        url(r'^apriori/(?P<minsup>\d+(.\d+)?)/$', views.apriori, name='apriori'),
        url(r'^api/statements$', views.tincan_all, name='tincan_all'),
        #url(r'^api/statements/filtered/$', views.tincan_filtered,
        #                                   name='tincan_filtered'),
        #url(r'^api/statements/(?P<statement_id>[\da-f-]+)/$', views.tincan_id,
        #                                                      name='tincan_id'),
        #url(r'^api/submit/$', views.tincan_submit, name='tincan_submit'),
        )
