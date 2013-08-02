from django.conf.urls import patterns, url

from dashboard import views

urlpatterns = patterns('',
        url(r'^$', views.index, name='index'),
        url(r'^recommendations$', views.generate_recommendations,
            name='generate recommendations'),
        #url(r'^apriori/(?P<minsup>\d+(.\d+)?)/$', views.apriori, name='apriori'),
        url(r'^api/statements$', views.get_statements, name='get statements'),
        )
