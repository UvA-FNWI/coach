from django.db import models
import random
import string


def rand_id():
    """Generate a random ID for use in html DOM elements."""
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for x in range(10))


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
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    time = models.DateTimeField(auto_now=True)

    def _dict(self):
        return {'user': self.user,
                'type': self.type,
                'url': self.activity,
                'value': self.value,
                'name': self.name,
                'desc': self.description,
                'id': rand_id()}

    def __unicode__(self):
        return self.user + ' ' + self.activity + ' ' + str(self.value)

# * Assignments have scores and questions have progress
