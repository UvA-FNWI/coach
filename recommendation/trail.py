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

        for i, item in enumerate(trail):
            score_dict[cons][item] += gamma ** i
            count_dict[item] += 1

        for item in count_dict:
            if count_dict[item] > 1:
                added_dict[cons][item] += count_dict[item] - 1

    for trail in D.itervalues():
        trail_list = list(reversed(trail))

        for i, item in enumerate(trail_list):
            update(trail_list[i+1:], item)
            total_dict[item] += 1

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

if __name__ == '__main__':
    # Test Data
    D = {100: (1,1,2,3,4),
         200: (1,2,2,3,4),
         300: (3,4,2),
         400: (1,4),
         500: (1,2,2,2,4,5,3),
         600: (1,3,2,4,5),
         700: (1,2,5,4)}

    gamma = float(sys.argv[1])
    minsupp = float(sys.argv[2])
    minconf = float(sys.argv[3])

    rules = generate_rules(D, gamma, minsupp, minconf)

    for rule in rules:
        print '{0} --> {1} | {2} | {3}'.format(rule[0],rule[1],rule[2],rule[3])
