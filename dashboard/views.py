from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.conf import settings

from urllib import quote, unquote
from hashlib import md5
from dateutil.parser import parse
from datetime import datetime, timedelta
import json
import random

from xapi import XAPIConnector
from course.models import Course, Assessment
from .models import Activity, GroupAssignment
from .helpers import get_barcode_data

BARCODE_HEIGHT = 35
ASSESSMENT = XAPIConnector.ACTIVITY_TYPES['assessment']

## Decorators
def identity_required(func):
    def inner(request, *args, **kwargs):
        # Fetch email from GET paramaters if present and store in session.
        paramlist = request.GET.get('paramlist', None)
        user = request.GET.get('user', None)
        course = request.GET.get('course', None)
        param_hash = request.GET.get('hash', None)
        if paramlist is not None:
            hash_contents = []
            for param in paramlist.split(","):
                if param == "pw":
                    hash_contents.append(settings.AUTHENTICATION_SECRET)
                else:
                    hash_contents.append(quote(request.GET.get(param, ""), ''))
            hash_string = md5(",".join(hash_contents)).hexdigest().upper()
            if hash_string == param_hash and user is not None and user != "":
                request.session['user'] = user
                if course:
                    request.session['course'] = course

        # Fetch user from session
        user = request.session.get('user', None)

        # If no user is specified, show information on how to login
        if user is None:
            return HttpResponseBadRequest()
        else:
            return func(request, *args, **kwargs)
    return inner

def check_group(func):
    """Decorator to check the group for A/B testing.
    Users in group A see the dashboard and users in group B do not.
    Users that are in no group will be assigned one, so that both groups differ
    at most 1 in size. If both groups are the same size, the group will be
    assigned pseudorandomly.
    """
    def inner(request, *args, **kwargs):
        # Fetch user from session
        user = request.session.get('user', None)

        # Case 1: Existing user
        try:
            assignment = GroupAssignment.objects.get(user=user)
            if assignment.group == 'A':
                return func(request, *args, **kwargs)
            else:
                return HttpResponse()
        # Case 2: New user
        except GroupAssignment.DoesNotExist:
            # Case 2a: First half of new pair,
            #          randomly pick A or B for this user.
            if GroupAssignment.objects.count() % 2 == 0:
                group = random.choice(['A', 'B'])
                if group == 'A':
                    assignment = GroupAssignment(user=user, group='A')
                    assignment.save()
                    return func(request, *args, **kwargs)
                else:
                    assignment = GroupAssignment(user=user, group='B')
                    assignment.save()
                    return HttpResponse()
            # Case 2b: Second half of new pair,
            #          choose the group that was not previously chosen.
            else:
                try:
                    last_group = GroupAssignment.objects.order_by('-id')[0].group
                except:
                    last_group = random.choice(['A', 'B'])
                if last_group == 'A':
                    assignment = GroupAssignment(user=user, group='B')
                    assignment.save()
                    return HttpResponse()
                else:
                    assignment = GroupAssignment(user=user, group='A')
                    assignment.save()
                    return func(request, *args, **kwargs)
    return inner

## Interface
@identity_required
@check_group
def barcode(request, default_width=170):
    """Return an svg representing progress of an individual vs the group."""
    # Fetch user and course from session
    user = request.session.get('user', None)
    course_url = request.session.get('course', None)


    width = int(request.GET.get('width', default_width))
    data = {'width': width, 'height': 60+2*BARCODE_HEIGHT}

    # Get all assessments of this course
    course_assessments = Assessment.objects.filter(
            course__url=course_url).values_list('url', flat=True)

    # Get all current assessments of this course
    today = datetime.today()
    current_assessments = Assessment.objects.filter(
            course__url=course_url,
            start_date__lte=today,
            end_date__gte=today).values_list('url', flat=True)

    # Get all activities of this course
    course_activities = Activity.objects.filter(
            type=ASSESSMENT, course=course_url)

    # Get all activities on current assessments
    current_activities = filter(lambda x: x.activity in current_assessments,
            course_activities)

    data['course_barcode'] = get_barcode_data(width, BARCODE_HEIGHT,
            course_activities, course_assessments, user)
    data['current_barcode'] = get_barcode_data(width, BARCODE_HEIGHT,
            current_activities, current_assessments, user)

    return render(request, 'dashboard/barcodes.svg', data,
            content_type='image/svg+xml')

## Background processes
def cache_activities(request):
    """Create a cache of the Learning Record Store by getting all items since
    the most recent one in the cache.
    """
    # Dynamic interval retrieval settings
    INTERVAL = timedelta(days=1)

    # Get new data
    connector = XAPIConnector()

    counters = {}
    for course in Course.objects.filter(active=True):
        course_activity = course.url
        epoch = (course.last_updated or datetime.combine(course.start_date,
            datetime.min.time()))
        statements = connector.getAllStatementsByRelatedActitity(
                course_activity, epoch=epoch)
        if statements is False:
            return HttpResponse("No statements could be retrieved.")

        counter = 0
        last_stored_date = None
        for statement in statements:
            if last_stored_date is None:
                last_stored_date = parse(statement['stored'])
            activity = Activity.extract_from_statement(statement)
            if activity:
                counter += 1

        course.last_updated = last_stored_date
        course.save()

        counters[course_activity] = counter
    return HttpResponse(json.dumps(counters))
