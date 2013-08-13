import sys
from collections import defaultdict

# For debug purposes
from apriori import display_dict

def score(D, gamma = 0.9):
    '''Assigns a score to each consequent-antecedent-pair in the transactions.
    The gamma operator discounts items that lie further apart.

    D:      Dataset containing transactions.
    gamma:  Discount factor

    NOTE: This method assumes that the items within the transactions are sorted.
    '''

    score_dict = dict()

    def update(trail, cons):
        if cons not in score_dict:
            score_dict[cons] = dict()

        for i, item in enumerate(trail):
            if item not in score_dict[cons]:
                score_dict[cons][item] = gamma ** i
            else:
                score_dict[cons][item] += gamma ** i

    for trail in D.itervalues():
        trail_list = list(reversed(trail))
        for i, item in enumerate(trail_list):
            update(trail_list[i+1:], item)

    return score_dict

def generate_rules(D, gamma, minsupp, minconf, verbose = False):
    '''Generates rules according to the scores of the items.

    D:          Dataset containing transactions.
    gamma:      Discount factor.
    minsupp:    Support threshold.
    minconf:    Confidence threshold.
    verbose:    Prints the score-dict for debug purposes.
    '''
    score_dict = score(D, gamma)

    if verbose:
        display_dict('scores', score_dict)

    total_dict = dict()
    for v in D.itervalues():
        for item in v:
            if item not in total_dict:
                total_dict[item] = 1
            else:
                total_dict[item] += 1

    rules = set()

    for cons in score_dict:
        for ante in score_dict[cons]:
            supp = float(score_dict[cons][ante])
            conf = supp / float(total_dict[cons])
        
            if supp >= minsupp and conf >= minconf:
                rules.add((ante, cons, conf, supp))

    return rules

if __name__ == '__main__':

    # Test Data
    D = {100: (1,3,4),
         200: (2,3,5),
         300: (1,2,3,5),
         400: (2,5),
         500: (1,2,4,5,3),
         600: (1,3,2,4,5),
         700: (1,2,5,4)}

    L = {0: defaultdict(int)}
    for v in D.itervalues():
        for elem in v:
            L[0][(elem,)] += 1

    gamma = float(sys.argv[1])
    minsupp = float(sys.argv[2])
    minconf = float(sys.argv[3])

    rules = generate_rules(D, gamma, minsupp, minconf)

    for rule in rules:
        print '{0} --> {1} | {2} | {3}'.format(rule[0],rule[1],rule[2],rule[3])
