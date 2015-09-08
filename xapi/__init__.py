'''
Adaptation of tincan API for Python to work with latest tincan.
Contains lists of verbs and definition of activities specifically
for the COACH project.

Auth: Sander Latour, Auke Wiggers
Date: 04-09-2015, 29-07-2013
'''

from requests.auth import HTTPBasicAuth
from urlparse import urljoin
from django.conf import settings
import requests
import json
import urllib
import uuid
import pytz
from datetime import datetime, timedelta


class XAPIConnector(object):
    VERSIONHEADER = "X-Experience-API-Version"
    VERSION = "1.0.0"
    VERBS = {'launched': {'id': 'http://adlnet.gov/expapi/verbs/launched',
                                                'display': {'en-US': 'launched'}},
                     'interacted': {'id': 'http://adlnet.gov/expapi/verbs/interacted',
                                                    'display': {'en-US': 'interacted'}},
                     'progressed': {'id': 'http://adlnet.gov/expapi/verbs/progressed',
                                                    'display': {'en-US': 'progressed'}},
                     'answered': {'id': 'http://adlnet.gov/expapi/verbs/answererd',
                                                'display': {'en-US': 'answered'}},
                     'suspended': {'id':    'http://adlnet.gov/expapi/verbs/suspended',
                                                 'display': {'en-US': 'suspended'}},
                     'completed': {'id':    'http://adlnet.gov/expapi/verbs/completed',
                                                 'display': {'en-US': 'completed'}}}
    ACTIVITY_TYPES = {
             'assessment': 'http://adlnet.gov/expapi/activities/assessment',
             'media': 'http://adlnet.gov/expapi/activities/media',
             'question': 'http://adlnet.gov/expapi/activities/question'
                                     }

    def __init__(self, userName=None, secret=None, endpoint=None, logger=None):
        self._userName = userName or settings.LRS.get('username','')
        self._secret = secret or settings.LRS.get('password','')
        self._endpoint = endpoint or settings.LRS.get('endpoint','')
        self.logger = logger

    def submitStatement(self, jsonObject):
        """Submit a single statement."""
        try:
            ##Validates that the verb is valid
            #if(not dataValidation.validateVerb(jsonObject['verb'])):
            #    raise ValueError("INVALID VERB: "+jsonObject['verb'])

            resp = requests.post(self._endpoint,
                                        data=json.dumps(jsonObject),
                                        auth=HTTPBasicAuth(self._userName,self._secret),
                                        headers={"Content-Type":"application/json",
                                                         self.VERSIONHEADER:self.VERSION})

        except IOError as e:
            if self.logger is not None:
                self.logger.error(e)


    def submitStatementList(self, jsonObjectList):
        """Submits a list of Statements."""
        for statement in jsonObjectList:
            try:
                ##Validates that the verb is valid
                #if(not dataValidation.validateVerb(statement['verb'])):
                #    raise ValueError("INVALID VERB: "+statement['verb'])

                resp = requests.post(self._endpoint,
                                        data=json.dumps(statement),
                                        auth=HTTPBasicAuth(self._userName,self._secret),
                                        headers={"Content-Type":"application/json",
                                                         self.VERSIONHEADER:self.VERSION})
            except IOError as e:
                if self.logger is not None:
                    self.logger.error(e)
                else:
                    print e


    def getStatementByID(self, ID):
        """Retrieve a statement by its ID."""
        try:
            url = self._endpoint+"?statementId="+ID
            resp = requests.get(url,
                                auth=HTTPBasicAuth(self._userName, self._secret),
                                headers={"Content-Type":"application/json",
                                                 self.VERSIONHEADER:self.VERSION})
            return resp.json()
        except IOError as e:
            if self.logger is not None:
                self.logger.error(e)

    def dynamicIntervalStatementRetrieval(self, t1, dt):
        """
        Wrapper function for getFilteredStatements to handle a LRS that
        timeouts quickly when the data stored in it is too big. It uses dynamic
        time intervals to limit the data requested in order to retrieve the
        data slowly bit by bit. The size of the bits (interval) is dynamically
        altered bases on the result of the LRS. When a timeout occurs the
        interval is halved, when an empty result is returned the timeout
        doubles. It returns the cumulative list of statements between t1 and
        now when the entire period was bridgeable with dynamic intervals. It
        raises an Exception when the interval needs to be reduced to less then
        a second. Typically the latter case would indicate a different problem.

        @arg t1 Datetime object that indicates the begin of the period to be
        retrieved
        @arg dt Timedelta object that indicates the initial interval to be
        tried
        @return List of statements as returned by getFilteredStatements
        """
        t2 = datetime.now().replace(tzinfo=pytz.utc)
        if t1.tzinfo is None:
            t1.replace(tzinfo=pytz.utc)
        min_dt = timedelta(seconds=1)
        statements = []
        while True:
            since = t1.isoformat()
            until = (t1+dt).isoformat()
            r = self.getFilteredStatements({"since":since,"until":until},False)
            if r == False:
                if dt > min_dt*2:
                    dt /= 2
                else:
                    raise Exception("dt %s too small, t1: %s" % (dt,t1))
            elif r == []:
                if t1+dt > t2:
                    return statements
                else:
                    t1 += dt
                    dt *= 2
            else:
                statements += r
                t1 += dt

    def getAllStatements(self):
        """Retrieve every TinCan Statement from the End point."""
        try:
            endpoint = self._endpoint
            statements = []
            while endpoint is not None:
                try:
                    resp = requests.get(endpoint,
                                        auth=HTTPBasicAuth(self._userName, self._secret),
                                        headers={"Content-Type" : "application/json",
                                                         self.VERSIONHEADER : self.VERSION})
                except requests.ConnectionError as e:
                    if self.logger is not None:
                        print "Error getting statements."
                        self.logger.error(e)
                    return statements
                result = resp.json()
                statements = statements + result["statements"]
                if "more" in result and result["more"]:
                    endpoint = urljoin(endpoint, result["more"])
                else:
                    endpoint = None
            return statements
        except IOError as e:
            if self.logger is not None:
                self.logger.error(e)

    def getFilteredStatements(self, filters, fail_safe=None):
        """Retrieve every TinCan Statement that matches filters."""
        fail_safe = True if fail_safe is None else fail_safe

        resource = self._endpoint+"?"+urllib.urlencode(filters)
        more = False
        try:
            statements = []
            while resource is not None:
                try:
                    resp = requests.get(resource,
                            auth = HTTPBasicAuth(self._userName, self._secret),
                            headers = {
                                "Content-Type": "application/json",
                                self.VERSIONHEADER: self.VERSION})

                except requests.ConnectionError as e:
                    if self.logger is not None:
                        print "Error getting statements."
                        self.logger.error(e)
                    return statements if fail_safe else False

                try:
                    result = resp.json()
                    statements = statements + result["statements"]
                    if "more" in result and result["more"]:
                        more = True
                        resource = urljoin(self._endpoint, result["more"])
                    else:
                        resource = None
                except Exception as e:
                    print "Error decoding response:", resp
                    return False
            return statements
        except IOError as e:
            if self.logger is not None:
                self.logger.error(e)

    def getAllStatementsByRelatedActitity(self, related_activity, epoch=None):
        filters = {
                'related_activities': 'True',
                'activity': related_activity}
        if epoch is not None:
            if epoch.tzinfo is None:
                epoch = epoch.replace(tzinfo=pytz.utc)
            if not epoch.microsecond == 0:
                epoch = epoch.microsecond.replace(microsecond=0)
            filters['since'] = epoch.isoformat()

        return self.getFilteredStatements(filters)
