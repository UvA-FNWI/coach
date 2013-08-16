from django.db import models


class Recommendation(models.Model):
    item_hash = models.BigIntegerField()
    milestone = models.URLField()
    url = models.URLField()
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    confidence = models.FloatField()
    support = models.IntegerField()
    timestamp = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    def __html__(self):
        return '<a href="' + str(self.url) + '" >' + \
               str(self.name) + '</a>'

class Activity(models.Model):
    user = models.EmailField()
    type = models.URLField(max_length=255)
    activity = models.URLField(max_length=255)
    value = models.FloatField()  # Progress/score depending on type *
    time = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

    def __unicode__(self):
        return self.user + ' ' + self.activity + ' ' + str(self.value)

# * Assignments have scores and questions have progress
