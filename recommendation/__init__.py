'''
Collects data from the learning record store, from which recommendations can
be made using a prespecified algorithm and corresponding settings.

Auth: Auke Wiggers
Date: 30-07-2013
'''

import sys
import os
import uuid
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir)
from tincan_api import TinCan
from coach import settings
from operator import itemgetter
from collections import defaultdict
import apriori
import trail
import time

def recommend(recommendationfunction='apriori', inputverbs=None, **kwargs):
    '''Generate new recommendation rules for every assignment that is of some
    importance, based on completed and launched media, questions, assessments.

    Note that only questions and media may be recommended, as the filter should
    already make sure that the found questions/media are only relevant for the
    current assessment.

    TODO:
      - Check if milestone passed
      - Decay for past milestones + assigments
      - Alter filter for smaller query, perhaps multiple queries?

    Don't try to run if
      1. Top X will not be altered, based on people submitted/threshold conf/sup

    '''
    use_cache = 'activities' in kwargs

    tc = TinCan(settings.TINCAN['username'],
                settings.TINCAN['password'],
                settings.TINCAN['endpoint'])
    # By default, get all info from users who completed
    if inputverbs:
        verbs = [tc.VERBS[verb]['id'] for verb in inputverbs]
    else:
        verbs = [tc.VERBS['completed']['id']]
    max_consequent_size = kwargs['max_consequent_size'] if \
            'max_consequent_size' in kwargs else 1
    verbose = kwargs['verbose'] if 'verbose' in kwargs else False

    milestones = defaultdict(lambda : 'NO_ASSESSMENT')       # progress per actor
    assessment_ids = []
    transactions = dict()
    freq = dict()
    name_description = dict()

    if use_cache:
        print 'using cache'
        activities = kwargs['activities']
        # FIXME use cached activities, way faster, but differently formatted
        # Loop over reverse chronological data
        for activity in activities:
            if activity.verb not in verbs:
                continue

            actor = activity.user     # TODO replace mbox by ID
            name_description[activity.activity] = \
                    (activity.name,
                     activity.description)

            # Use assessments to separate timeslices per actor
            if activity.type == tc.ACTIVITY_TYPES['assessment']:
                assessment_id = activity.activity
                milestones[actor] = assessment_id       # For every milestone:

                # Keep track of all assessments in reverse chronological order as well
                if not assessment_id in assessment_ids:
                    transactions[assessment_id] = defaultdict(list) # verbs+objects /actor
                    freq[assessment_id] = {0: defaultdict(int)}     # frequency of 1-pairs
                    assessment_ids.append(assessment_id)
            else:
                assessment_id = milestones[actor]
                if assessment_id == 'NO_ASSESSMENT':
                    continue

                statement_obj = activity.activity
                transactions[assessment_id][actor].append(statement_obj)
                freq[assessment_id][0][(statement_obj,)] += 1
    else:
        print 'not using cache'

        now = time.time()
        statements = tc.getAllStatements()
        print 'Time taken: {0:2g}'.format(time.time() - now)

        # Loop over reverse chronological data
        for statement in statements:
            if statement['verb']['id'] not in verbs:
                continue

            actor = statement['actor']['mbox']     # TODO replace mbox by ID
            name_description[statement['object']['id']] = \
                    (statement['object']['definition']['name'],
                     statement['object']['definition']['description'])

            # Use assessments to separate timeslices per actor
            if statement['object']['definition']['type'] == tc.ACTIVITY_TYPES['assessment']:
                assessment_id = statement['object']['id']
                milestones[actor] = assessment_id       # For every milestone:

                # Keep track of all assessments in reverse chronological order as well
                if not assessment_id in assessment_ids:
                    transactions[assessment_id] = defaultdict(list) # verbs+objects /actor
                    freq[assessment_id] = {0: defaultdict(int)}     # frequency of 1-pairs
                    assessment_ids.append(assessment_id)
            else:
                assessment_id = milestones[actor]
                if assessment_id == 'NO_ASSESSMENT':
                    continue

                statement_obj = statement['object']['id']
                transactions[assessment_id][actor].append(statement_obj)
                freq[assessment_id][0][(statement_obj,)] += 1

    # Use baskets as transactions and recommend
    rulebase = []
    for assessment_id in assessment_ids:
        D = transactions[assessment_id]
        L = freq[assessment_id]

        rules = []
        if recommendationfunction == 'apriori':
            # TODO choose between apriori / TID / (hybrid)
            minsup = kwargs['minsup']
            minconf = kwargs['minconf']

            print 'Generating rules for assessment ', assessment_id
            rules = apriori.generate_rules(apriori.apriori, D, L, minsup,
                                           minconf, max_consequent_size,
                                           verbose=verbose, veryverbose=False)
        elif recommendationfunction == 'trail':
            gamma = kwargs['gamma']
            minsupp = kwargs['minsup']
            minconf = kwargs['minconf']

            rules = trail.generate_rules(D, gamma, minsupp, minconf,verbose = verbose)

        # Save found rules based on the relevant assessment.
        for ante, conse, confidence, support in rules:
            rule = {'milestone': assessment_id,  # id indicating assessment
                    'antecedent': ante,          # LHS
                    'consequent': conse,         # RHS
                    'confidence': confidence,    # Confidence for LHS->RHS
                    'support': support}          # Support for the rule
            rulebase.append(rule)

    return rulebase, name_description

if __name__=="__main__":
    recommend('apriori', minsup=float(sys.argv[1]), minconf=float(sys.argv[2]),
            inputverbs=['completed'], max_consequent_size=1, verbose=True)
