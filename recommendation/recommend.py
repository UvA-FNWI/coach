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

def recommend(recommendationfunction, **kwargs):
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
    tc = TinCan(settings.TINCAN['username'],
                settings.TINCAN['password'],
                settings.TINCAN['endpoint'])

    # Get all info from users who completed stuff
    statement_filter = {'verb': tc.VERBS['completed']['id']}
    statements = tc.getFilteredStatements(statement_filter)

    # Group data by actor, as each actor corresponds to one 'basket'
    transactions = defaultdict(list)
    L = {0: defaultdict(int)}
    for statement in statements['statements']:
        # TODO somehow remove these in filter already.
        if statement['object']['definition']['type'] == tc.ACTIVITY_DEF['assessment']['type']:
            continue

        statement_tup = (statement['verb']['id'],
                         statement['object']['id'])
        # FIXME not every actor has mbox
        transactions[statement['actor']['mbox']].append(statement_tup)
        L[0][(statement_tup,)] += 1

    # Use baskets as transactions and recommend stuff itself instead of actions
    if recommendationfunction == 'apriori':
        # TODO choose between apriori / TID / hybrid
        minsup = kwargs['minsup']
        minconf = kwargs['minconf']
        rules = apriori.generate_rules(apriori.apriori, transactions, L, minsup,
                               minconf, verbose=False, veryverbose=False)

    '''
    Save found rules based on the relevant assessment.

    milestone     An id indicating for which timeslice these rules are relevant
    antecedent    LHS
    consequent    RHS
    confidence    Confidence for the rule LHS -> RHS
    support       Support for this rule
    '''

    rulebase = []
    milestone = ''
    for ante, conse, confidence, support in rules:
        rule = {'milestone': milestone, 'antecedent': ante, 'consequent': conse,
                'confidence': confidence, 'support': support}
        rulebase.append(rule)

    return rulebase

if __name__=="__main__":
    recommend('apriori', minsup=float(sys.argv[1]), minconf=float(sys.argv[2]))
