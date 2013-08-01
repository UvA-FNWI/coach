import sys
import os
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir)
from coach import settings
from tincan_api import TinCan
import random
import time
import string

ASSIGNMENTS = [('http://www.uva.nl/question1', 'question'),
               ('http://www.uva.nl/question2', 'question'),
               ('http://www.uva.nl/question3', 'question'),
               ('http://www.uva.nl/question4', 'question'),
               ('http://www.uva.nl/question5', 'question'),
               ('http://www.uva.nl/media1', 'media'),
               ('http://www.uva.nl/media2', 'media'),
               ('http://www.uva.nl/assessment', 'assessment')]

def simulate(_actor):
    '''Pick an assignment at random and complete it with some prob of
       success
    '''
    for _id, _def in ASSIGNMENTS:
        _object = activity_object(_id, _def)
        complete(_actor, _object, steps=1,
                p_success=random.uniform(0.8, 1.0))

def activity_object(_id, _activity):
    '''Create an object of type activity'''
    return {'id': _id, 'definition': tc.ACTIVITY_DEF[_activity]}

def complete(_actor, _object, steps=2, p_success=1.0):
    '''Finish an object in steps by progressing through it'''
    for s in xrange(steps):
        progressed(_actor, _object, 1.0 / steps)
        if random.random() > p_success:
            suspended(_actor, _object)
            print _actor['name'], 'suspended assignment ', _object['id']
            break
    else:
        completed(_actor, _object)
        print _actor['name'], 'completed assignment ', _object['id']

def progressed(_actor, _object, progress):
    jsonobject = { 'actor': _actor,
                   'verb': tc.VERBS['progressed'],
                   'object': _object,
                   #'extensions': {'progress': str(progress)}
                   }
    tc.submitStatement(jsonobject)

def suspended(_actor, _object):
    jsonobject = { 'actor': _actor,
                   'verb': tc.VERBS['suspended'],
                   'object': _object,}
    tc.submitStatement(jsonobject)

def completed(_actor, _object):
    jsonobject = { 'actor': _actor,
                   'verb': tc.VERBS['completed'],
                   'object': _object,}
    tc.submitStatement(jsonobject)

if __name__=="__main__":
    try:
        _actor = {'name':sys.argv[1],
                  'mbox':sys.argv[2]}
    except:
        name = ''.join(random.choice(string.ascii_uppercase +
                                     string.digits) for x in range(10))
        _actor = {'name': name,
                'mbox': 'mailto:{name}@uva.nl'.format(name=name) }

    tc = TinCan(settings.TINCAN['username'],
                settings.TINCAN['password'],
                settings.TINCAN['endpoint'])
    simulate(_actor)
