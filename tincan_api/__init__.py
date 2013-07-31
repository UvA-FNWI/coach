from requests.auth import HTTPBasicAuth
import requests
import json
import urllib
import uuid
#import dataValidation

VERSIONHEADER="X-Experience-API-Version"
VERSION="1.0.0"

class TinCan(object):
  def __init__(self,userName,secret,endpoint,logger=None):
    self._userName = userName
    self._secret = secret
    self._endpoint = endpoint
    self.logger = logger

  def submitStatement(self, jsonObject):
    ##Attempts to submit a single statement
    try:
      ##Validates that the verb is valid
      #if(not dataValidation.validateVerb(jsonObject['verb'])):
      #  raise ValueError("INVALID VERB: "+jsonObject['verb'])

      resp = requests.post(self._endpoint,
                    data=json.dumps(jsonObject),
                    auth=HTTPBasicAuth(self._userName,self._secret),
                    headers={"Content-Type":"application/json",
                             VERSIONHEADER:VERSION})
      return eval(resp.text)[0]

    except IOError as e:
      if self.logger is not None:
        self.logger.error(e)


  def submitStatementList(self, jsonObjectList):
    ##Submits a list of Statements
    for statement in jsonObjectList:
      try:
        ##Validates that the verb is valid
        #if(not dataValidation.validateVerb(statement['verb'])):
        #  raise ValueError("INVALID VERB: "+statement['verb'])

        resp = requests.post(self._endpoint,
                    data=json.dumps(statement),
                    auth=HTTPBasicAuth(self._userName,self._secret),
                    headers={"Content-Type":"application/json",
                             VERSIONHEADER:VERSION})
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
                auth=HTTPBasicAuth(self._userName,self._secret),
                headers={"Content-Type":"application/json",
                         VERSIONHEADER:VERSION})
      return resp.json()
    except IOError as e:
      if self.logger is not None:
        self.logger.error(e)

  def getAllStatements(self):
    ##Attempts to retrieve every TinCan Statement from the End point
    try:
      resp = requests.get(self._endpoint,
              auth=HTTPBasicAuth(self._userName,self._secret),
              headers={"Content-Type":"application/json",
                       VERSIONHEADER:VERSION})
      return resp.json()
    except IOError as e:
      if self.logger is not None:
        self.logger.error(e)

  def getFilteredStatements(self, inputDict):
    queryObject ={}
    for key in ['result', 'agent', 'context', 'timestamp',
                'verb', 'object',
                'stored', 'authority', 'version', 'attachments']:
        if key in inputDict:
            queryObject[key] = inputDict[key]

    ##Encodes the query object into a query string
    url = self._endpoint +"?"+ urllib.urlencode(queryObject)
    ##If the URL Length exceeds max URL length then query using post
    if (len(url)> 2048):
      resp = requests.post(self._endpoint,
                           data=queryObject,
                           auth=HTTPBasicAuth(self._userName,self._secret),
                           headers={"Content-Type":"application/json",
                                     VERSIONHEADER:VERSION})
      return resp.json()
    else:
      resp = requests.get(url,
                auth=HTTPBasicAuth(self._userName,self._secret),
                headers={"Content-Type":"application/json",
                         VERSIONHEADER:VERSION})
      return resp.json()

