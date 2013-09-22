import sys
from collections import defaultdict

def score(D, gamma = 0.9):
    '''Assigns a score to each consequent-antecedent-pair in the transactions.
    The gamma operator discounts items that lie further apart.

    D:      Dataset containing transactions.
    gamma:  Discount factor

    NOTE: This method assumes that the items within the transactions are sorted.
    '''

    score_dict = dict()
    added_dict = dict() 
    total_dict = defaultdict(int)

    def update(trail, cons):
        '''Updates the scores and counts for the given consequent according to
        the given (partial) trail.
        '''
        count_dict = defaultdict(int)

        if cons not in score_dict:
            score_dict[cons] = defaultdict(float)
            added_dict[cons] = defaultdict(float)

        for i, (item, value) in enumerate(trail):
            score_dict[cons][item] += value * gamma ** i
            count_dict[item] += 1

        for item in count_dict:
            if count_dict[item] > 1:
                added_dict[cons][item] += count_dict[item] - 1

    for trail in D.itervalues():
        trail_list = list(trail)

        for i, (cons, value) in enumerate(trail_list):
            update(trail_list[i+1:], cons)
            total_dict[cons] += 1

    return score_dict, total_dict, added_dict

def generate_rules(D, gamma, minsupp, minconf, verbose = False):
    '''Generates rules according to the scores of the items.

    D:          Dataset containing transactions.
    gamma:      Discount factor.
    minsupp:    Support threshold.
    minconf:    Confidence threshold.
    '''
    score_dict, total_dict, added_dict = score(D, gamma)

    rules = set()

    for cons in score_dict:
        for ante in score_dict[cons]:
            supp = float(score_dict[cons][ante])
            conf = supp / float(total_dict[cons] + added_dict[cons][ante])
        
            if supp >= minsupp and conf >= minconf:
                rules.add((ante, cons, conf, supp))

    return rules
