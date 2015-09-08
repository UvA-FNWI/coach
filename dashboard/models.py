from django.db import models
from django.conf import settings
from xapi import PROGRESS_T, COMPLETED

import dateutil

class Activity(models.Model):
    user = models.CharField(max_length=255)
    course = models.URLField(max_length=255, null=True, blank=True)
    type = models.URLField(max_length=255)
    verb = models.URLField(max_length=255)
    activity = models.URLField(max_length=255)
    value = models.FloatField(null=True)  # Progress/score depending on type *
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    time = models.DateTimeField(null=True)

    class Meta:
        verbose_name_plural = "activities"

    @classmethod
    def extract_from_statement(cls, statement):
        statement_type = statement['object']['definition']['type']
        if 'mbox' in statement['actor']:
            user = statement['actor']['mbox']
        elif 'account' in statement['actor']:
            account = statement['actor']['account']
            if account['homePage'] == settings.USER_AUTH_DOMAIN:
                user = account['name']
            else:
                return None
        else:
            return None

        activity = statement['object']['id']
        verb = statement['verb']['id']
        name = statement['object']['definition']['name']['en-US']
        description = statement['object']['definition']['description']['en-US']
        time = dateutil.parser.parse(statement['timestamp'])
        try:
            raw_score = statement['result']['score']['raw']
            min_score = statement['result']['score']['min']
            max_score = statement['result']['score']['max']
            value = 100 * (raw_score - min_score) / max_score
        except KeyError:
            try:
                value = 100 * float(statement['result']['extensions'][PROGRESS_T])
            except KeyError:
                # If no information is given about the end result then assume a
                # perfect score was acquired when the activity was completed,
                # and no score otherwise.
                if verb == COMPLETED:
                    value = 100
                else:
                    value = 0

        if 'context' in statement and 'contextActivities' in statement['context']:
            course = statement['context']['contextActivities']['grouping'][0]['id']
        else:
            course = None

        if activity is None or verb is None or name is None:
            return None

        activity, created = cls.objects.get_or_create(user=user, verb=verb,
                course=course, activity=activity, time=time, defaults={
                    "type": statement_type,
                    "value": value,
                    "name": name,
                    "description": description})
        return activity

    def _dict(self):
        return {'user': self.user,
                'type': self.type,
                'verb': self.verb,
                'activity': self.activity,
                'value': self.value,
                'name': self.name,
                'desc': self.description,
                'time': self.time,
                'id': rand_id()}

    def __unicode__(self):
        return u' '.join([self.user, self.verb, self.activity,
                unicode(self.value)])

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return "Activity(%s)" % (self.verb,)


class GroupAssignment(models.Model):
    GROUPS = (('A', 'Group A: Dashboard'),
              ('B', 'Group B: No Dashboard'))
    user = models.CharField(max_length=255)
    group = models.CharField(max_length=1, choices=GROUPS)

    def __unicode__(self):
        return u'%s' % (str(self.user) + str(dict(self.GROUPS)[self.group]),)
