from django.db import models

class Course(models.Model):
    url = models.URLField(max_length=255)
    title = models.CharField(max_length=255)
    active = models.BooleanField(default=True, blank=True)
    start_date = models.DateField()
    last_updated = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u'%s' % (self.title,)

    def __repr__(self):
        return "Course(%s)" % (self.url,)


class Assessment(models.Model):
    url = models.URLField(max_length=255)
    title = models.CharField(max_length=255)
    course = models.ForeignKey('Course')
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u'%s' % (self.title,)

    def __repr__(self):
        return "Assessment(%s)" % (self.url,)
