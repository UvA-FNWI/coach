from django.db import models
import random
import string
import ast


def rand_id():
    """Generate a random ID for use in html DOM elements."""
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for x in range(10))


class Recommendation(models.Model):
    item_hash = models.BigIntegerField()
    milestone = models.URLField()
    url = models.URLField()
    name = models.CharField(max_length=255)
    m_name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    confidence = models.FloatField()
    support = models.IntegerField()
    timestamp = models.DateTimeField(auto_now=True)


    def get_name(self):
        return ast.literal_eval(self.name).values()[0]

    def get_desc(self):
        return ast.literal_eval(self.description).values()[0]

    def get_m_name(self):
        return ast.literal_eval(self.m_name)[0].values()[0]

    def get_m_desc(self):
        return ast.literal_eval(self.m_name)[1].values()[0]

    def __unicode__(self):
        return self.name

    def __html__(self):
        return '<a href="' + str(self.url) + '" >' + \
               str(self.name) + '</a>'


class Activity(models.Model):
    user = models.EmailField()
    type = models.URLField(max_length=255)
    verb = models.URLField(max_length=255)
    activity = models.URLField(max_length=255)
    value = models.FloatField(null=True)  # Progress/score depending on type *
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    time = models.DateTimeField(null=True)

    def _dict(self):
        return {'user': self.user,
                'type': self.type,
                'verb': self.verb,
                'url': self.activity,
                'value': self.value,
                'name': self.name,
                'desc': self.description,
                'id': rand_id()}

    def __unicode__(self):
        return self.user + ' ' + self.activity + ' ' + str(self.value)

class Click(models.Model):
    target = models.URLField()
    env1 = models.URLField()
    env2 = models.URLField()
    env3 = models.URLField()
    env4 = models.URLField()

    def _dict(self):
        return {'target': self.target,
                'env1': self.env1,
                'env2': self.env2,
                'env3': self.env3,
                'env4': self.env4}

    def __unicode__(self):
        return 'Clicked on:' + str(self.target)

# * Assignments have scores and questions have progress
