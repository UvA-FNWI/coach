import sys
import os
import os,sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir)
from coach import settings
from tincan_api import TinCan
import random
import time

VERBS = {'launched': {'id': 'http://adlnet.gov/expapi/verbs/launched',
                      'display': {'en-US': 'launched'}},
         'interacted': {'id': 'http://adlnet.gov/expapi/verbs/interacted',
                        'display': {'en-US': 'interacted'}},
         'progressed': {'id': 'http://adlnet.gov/expapi/verbs/progressed',
                        'display': {'en-US': 'progressed'}},
         'answered': {'id': 'http://adlnet.gov/expapi/verbs/answererd',
                      'display': {'en-US': 'answered'}},
         'suspended': {'id':  'http://adlnet.gov/expapi/verbs/suspended',
                       'display': {'en-US': 'suspended'}},
         'completed': {'id':  'http://adlnet.gov/expapi/verbs/completed',
                       'display': {'en-US': 'completed'}}}

ACTIVITY_DEF = {'assessment': {'name': {'en-US': 'assessment'},
                    'type': 'http://adlnet.gov/expapi/activities/assessment'},
                'media': {'name': {'en-US': 'media'},
                    'type': 'http://adlnet.gov/expapi/activities/media'},
                'question': {'name': {'en-US': 'question'},
                    'type': 'http://adlnet.gov/expapi/activities/question'}
                }

ASSIGNMENTS = [('http://www.uva.nl/question1', 'question'),
               ('http://www.uva.nl/question2', 'question'),
               ('http://www.uva.nl/media1', 'media'),
               ('http://www.uva.nl/media2', 'media'),
               ('http://www.uva.nl/assessment', 'assessment')]

def simulate(_actor):
    '''Pick an assignment at random and complete it with some prob of
       success
    '''
    for _id, _def in ASSIGNMENTS:
        _object = activity_object(_id, _def)
        complete(_actor, _object, steps=10,
                p_success=random.uniform(0.8, 1.0))

def activity_object(_id, _activity):
    '''Create an object of type activity'''
    return {'id': _id, 'definition': ACTIVITY_DEF[_activity]}

def complete(_actor, _object, steps=10, p_success=1.0):
    '''Finish an object in steps by progressing through it'''
    for s in xrange(steps):
        progressed(_actor, _object, 1.0 / steps)
        time.sleep(1)
        if random.random() > p_success:
            suspended(_actor, _object)
            break
    else:
        completed(_actor, _object)

def progressed(_actor, _object, progress):
    jsonobject = { 'actor': _actor,
                   'verb': VERBS['progressed'],
                   'object': _object,
                   #'extensions': {'progress': str(progress)}
                   }
    print '\n', jsonobject, '\n'

    tc.submitStatement(jsonobject)

def suspended(_actor, _object):
    jsonobject = { 'actor': _actor,
                   'verb': VERBS['suspended'],
                   'object': _object,}
    for x in jsonobject:
        print x, jsonobject[x]
    tc.submitStatement(jsonobject)

def completed(_actor, _object):
    jsonobject = { 'actor': _actor,
                   'verb': VERBS['completed'],
                   'object': _object,}
    for x in jsonobject:
        print x, jsonobject[x]
    tc.submitStatement(jsonobject)

if __name__=="__main__":
    try:
        _actor = {'name':sys.argv[1],
                  'mbox':sys.argv[2]}
    except:
        print 'usage: python generate_dummydata <name> <mbox>'
        sys.exit(0)

    tc = TinCan(settings.TINCAN['username'],
                settings.TINCAN['password'],
                settings.TINCAN['endpoint'])
    tc.submitStatement({
        'verb': {'id': 'http://adlnet.gov/expapi/verbs/progressed',
                 'display': {'en-US': 'progressed'}},
        'actor': {'mbox': 'mailto:auke', 'name': 'auke'},
        'object': {'definition':
                     {'type': 'http://adlnet.gov/expapi/activities/question',
                      'name': {'en-US': 'question'}},
                   'id': 'http://www.uva.nl/question1'}})
    #simulate(_actor)

