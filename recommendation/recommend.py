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

# Get all info from users who completed stuff
statement_filter = {'verb', tc.VERBS['completed']['id']}
statements = tc.getFilteredStatements(statement_filter)

# Group data by actor, as each actor corresponds to one 'basket'
transactions = defaultdict(list)
for statement in statements['statements']:
    transactions[tuple(statement['actor'])].append(statement)

# Count occurrence of part-of-statements
L = {0: defaultdict(int)}
for statementlist in transactions.itervalues(): # transaction contain statements
    for statement in statementlist:             # for every statement
        L[(statement['verb'], statement['object'])] += 1

    # Use baskets as transactions and recommend stuff itself instead of actions

    # but only recommend media and questions

