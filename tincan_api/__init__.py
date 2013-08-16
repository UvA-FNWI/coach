'''
Adaptation of tincan API for Python to work with latest tincan.
Contains lists of verbs and definition of activities specifically
for the COACH project.

Auth: Sander Latour, Auke Wiggers
Date: 29-07-2013
'''

from requests.auth import HTTPBasicAuth
from urlparse import urljoin
import requests
import json
import urllib
import uuid


class TinCan(object):
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

    def __init__(self, userName, secret, endpoint, logger=None):
        self._userName = userName
        self._secret = secret
        self._endpoint = endpoint
        self.logger = logger

    def submitStatement(self, jsonObject):
        ##Attempts to submit a single statement
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
        ##Submits a list of Statements
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
        ##Attempts to retrieve a statement by its ID
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

    def getAllStatements(self):
        ##Attempts to retrieve every TinCan Statement from the End point
        try:
            endpoint = self._endpoint
            statements = []
            while endpoint is not None:
                try:
                    resp = requests.get(endpoint,
                                        auth=HTTPBasicAuth(self._userName, self._secret),
                                        headers={"Content-Type" : "application/json",
                                                         self.VERSIONHEADER : self.VERSION})
                except ConnectionError as e:
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

    def getFilteredStatements(self, inputDict):
        ##Attempts to retrieve every TinCan Statement from the End point
        queryObject = {}
        for key in ['result', 'agent', 'context', 'timestamp',
                                'verb', 'object', 'since',
                                'stored', 'authority', 'version', 'attachments']:
            if key in inputDict:
                queryObject[key] = inputDict[key]
        self._endpoint = self._endpoint +"?"+ urllib.urlencode(queryObject)
        try:
            endpoint = self._endpoint
            statements = []
            while endpoint is not None:
                try:
                    if (len(endpoint)> 2048):
                        resp = requests.post(self._endpoint,
                                             data = queryObject,
                                             auth = HTTPBasicAuth(self._userName,self._secret),
                                             headers = {"Content-Type":"application/json",
                                                                 self.VERSIONHEADER:self.VERSION})
                    else:
                        resp = requests.get(endpoint,
                                            auth = HTTPBasicAuth(self._userName,self._secret),
                                            headers = {"Content-Type":"application/json",
                                                             self.VERSIONHEADER:self.VERSION})
                except ConnectionError as e:
                    if self.logger is not None:
                        print "Error getting statements."
                        self.logger.error(e)
                    return statements
                try:
                    result = resp.json()
                    statements = statements + result["statements"]
                    if "more" in result and result["more"]:
                        endpoint = urljoin(endpoint, result["more"])
                    else:
                        endpoint = None
                except Exception as e:
                    print "Error decoding response:", e
            return statements
        except IOError as e:
            if self.logger is not None:
                self.logger.error(e)
