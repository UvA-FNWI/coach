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
    '''
    tc = TinCan(settings.TINCAN['username'],
                settings.TINCAN['password'],
                settings.TINCAN['endpoint'])

    # Get all info from users who completed stuff
    statement_filter = {'verb': tc.VERBS['completed']['id']}
    statements = tc.getFilteredStatements(statement_filter)

    # Group data by actor, as each actor corresponds to one 'basket'
    transactions = defaultdict(list)
    for statement in statements['statements']:
        transactions[tuple(statement['actor'])].append(statement)

    # Count occurrence of verbs and objects
    L = {0: defaultdict(int)}
    for statementlist in transactions.itervalues(): # for each transaction
        for statement in statementlist:             # for every statement
            L[(statement['verb'], statement['object']['id'])] += 1

    # Use baskets as transactions and recommend stuff itself instead of actions
    if recommendationfunction == 'apriori':
        # TODO choose between apriori / TID / hybrid
        minsup = kwargs['minsup']
        minconf = kwargs['minconf']
        rules = apriori.generate_rules(apriori.apriori, transactions, L, minsup,
                               minconf, verbose=True)

    # but only recommend media and questions

if __name__=="__main__":
    recommend('apriori', minsup=2, minconf=0.3)
