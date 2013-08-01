from django.db import models


class Recommendation(models.Model):
    task_url = models.URLField()
    items_hash = models.IntegerField()
    recommendation_url = models.URLField()
    recommendation_name = models.CharField(max_length=255)
    confidence = models.FloatField()
    timestamp = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.recommendation_name

    def __html__(self):
        return '<a href="' + str(recommendation_url) + '" >' + \
               str(recommendation_name) + '</a>'
