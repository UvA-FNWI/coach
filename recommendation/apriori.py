'''
Implementation of the a priori algorithm, found in 'Fast discovery of association rules' by Agrawal et al.

Auth: Auke Wiggers
Date: 29-07-2013
'''
import sys
from itertools import izip, combinations
from collections import defaultdict

def apriori(D, L, minsup=2, verbose=True):
    ''' The apriori algorithm itself consists of two phases:
    First, generate new candatate C_k, then scan the database and count
    support of candidates in C_k.

    D:       Dataset containing transactions.
    L:       Set of large k-itemsets.
    minsup:  Support threshold

    '''
    if verbose:
        print '===Apriori==='
    k = 1

    while len(L[k-1]) > 0:
        C_k = apriori_gen(L[k-1], k)         # create new candidate
        for transaction in D.itervalues():
            C_t = subset(C_k, transaction)   # candidates contained in t
            for candidate in C_t:
                C_k[candidate] += 1

        L[k] = {c: count for c, count in C_k.iteritems() if count >= minsup}

        if verbose and len(L[k]) > 0:
            print '==== Iteration {} ===='.format(k)
            display_dict('C{}'.format(k), C_k)
            display_dict('L{}'.format(k), L[k])

        k += 1
    return L

def apriori_TID(D, L, minsup=2, verbose=True):
    '''
    Version of the apriori algorithm that uses the database directly to
    generate candidates.

    D : Database containing transactions
    L : Input dictionary containing L[1]
    '''
    if verbose:
        print '===Apriori TID==='
    C__ = {0: items_to_setofitemsets(D)}
    if verbose:
        display_dict('C__[0]', C__[0])
    k = 1

    while len(L[k-1]) > 0:
        C_k = apriori_gen(L[k-1], k)
        C__[k] = dict()

        for TID, set_of_itemsets in C__[k-1].iteritems():
            C_t = [c for c in C_k if
                    c[:k] in set_of_itemsets and
                    tuple(c[:k-1]) + (c[k],) in set_of_itemsets]
            for candidate in C_t:
                C_k[candidate] += 1
            if len(C_t):
                C__[k][TID] = C_t

        L[k] = {c: count for c, count in C_k.iteritems() if count >= minsup}
        if verbose and len(L[k]) > 0:
            print '==== Iteration {} ===='.format(k)
            display_dict('C{}'.format(k), C_k)
            display_dict('C__{}'.format(k), C__[k])
            display_dict('L{}'.format(k), L[k])

        k += 1
    return L

def subset(candidate_set, transaction):
    ''' Subset function finds the candidates contained in the transaction.

    candidate_set:  set of items that are candidates
    transaction:    set of items present in the transaction

    Returns the remainder of the candidate set after item selection.
    '''
    return (c for c in candidate_set if all(item in transaction for item in c))

def apriori_gen(L_kmin1, k):
    ''' Candidate generation for the apriori algorithm. First, L[k-1] is
    joined with itself to obtain a superset of the final set of candidates.
    The union of itemsets p and q from L[k-1] is inserted in the final set
    if they share their k-2 first items.

    Then, all itemsets c from C_k are pruned so that some (k-1)-subset of
    c is not present in L[k-1].

    L_kmin1: The set of all large k-1 itemsets.
    k:       Integer indicating sweep phase.

    Returns the candidate set for the current k.
    '''
    C_k = dict()

    for p, q in combinations(sorted(L_kmin1), 2):
        if p[:k-1] == q[:k-1]:
            candidate = p[:k-1] + tuple(sorted((p[k-1], q[k-1])))
            if not any( (subset_c not in L_kmin1 for subset_c in
                      combinations(candidate, k)) ):
                C_k[candidate] = 0
    return C_k

def generate_rules(apriori_function, D, L, minsup, minconf,
                   max_consequent_size, verbose, veryverbose=False):
    ''' Using an apriori candidate generation function, find the itemsets
    for k >= 1. Then, use these candidates to find association rules.

    '''
    rules = set()

    candidates = sorted(apriori_function(D, L, minsup, verbose=veryverbose).
                        iteritems())
    for k, L_k in candidates:
        if verbose and len(L_k):
            print '\n==== L{} ====='.format(k)
        for l_k, support in L_k.iteritems():
            # H0 holds consequents of rules with one item in the consequent
            H_0 = {(element,) : support for element in l_k}

            new_rules = apriori_genrules(L, l_k, support, k, H_0, 0, minconf,
                                         max_consequent_size, veryverbose)

            if verbose and len(new_rules):
                for a, c, conf, supp in new_rules:
                    for antecedent in a:
                        print '\n{}'.format(antecedent),
                    print ' -->      {}'.format(conf)
                    for consequent in c:
                        print '    {}'.format(consequent)

            rules |= new_rules

    return rules

def apriori_genrules(L, l_k, support_l_k, k, H_m, m, minconf,
                     max_consequent_size, verbose):
    '''Based on aprioris itemsets, association rules can be generated given a
    confidence threshold.

    L_k     : Large itemset
    k       : Corresponding integer indicating size of items
    H_m     : Input set of rules
    m       : Corresponding integer indicating size of consequent
    minconf : Confidence threshold

    Returns a set of rules in form
        (antecedent, consequent, confidence, support)
    '''
    rules = set()

    if k > m + 1:
        H_mplus1 = apriori_gen(H_m, m+1)
        if (k - m) <= max_consequent_size + 1:
            for h_mplus1 in H_mplus1.keys():
                difference =  tuple(l for l in l_k if not l in h_mplus1)

                # Conf = support(l_k) / support(l_k - h_m+1)
                conf = support_l_k / float(L[len(difference)-1][difference])
                if conf >= minconf:
                    rules.add((h_mplus1, difference, conf, support_l_k))
                else:
                    del H_mplus1[h_mplus1]

        rules |= apriori_genrules(L, l_k, support_l_k, k, H_mplus1, m+1,
                                  minconf, max_consequent_size, verbose)
    return rules

def items_to_setofitemsets(d):
    setofitemsets = dict()
    for k, v in d.iteritems():
        if type(v[0]) is not int:
            setofitemsets[k] = set(tuple(x) for x in v)
        else:
            setofitemsets[k] = set((x,) for x in v)

    return setofitemsets

def display_dict(name, d):
    print '\n{}'.format(name)
    for k,v in d.iteritems():
        display_item(k)
        print ' : ',
        display_item(v)
        print ''
def display_item(item):
    if isinstance(item, str) or isinstance(item, unicode):
        print item.split('/')[-1],
    elif isinstance(item, list) or isinstance(item, tuple) or \
            isinstance(item, set):
        for sub_item in item:
            display_item(sub_item)
        print ' ',
    else:
        print item,

if __name__ == '__main__':
    '''
    example db from:
    http://www.cs.helsinki.fi/u/htoivone/pubs/advances.pdf

    '''
    D = {100: (1,3,4),
         200: (2,3,5),
         300: (1,2,3,5),
         400: (2,5),
         500: (1,2,3,4,5),
         600: (1,2,3,4,5),
         700: (1,2,3,5)}

    L = {0: defaultdict(int)}
    for v in D.itervalues():
        for elem in v:
            L[0][(elem,)] += 1

    try:
        minsup=float(sys.argv[1])
        minconf=float(sys.argv[2])
    except:
        print 'Usage: python apriori.py <minsup> <minconf>'
        sys.exit(0)

    #apriori(D, L, minsup=minsup)
    #apriori_TID(D, L, minsup=minsup)

    verbose=True
    apriori_function = apriori_TID

    generate_rules(apriori_function, D, dict(L), minsup, minconf,
                   max_consequent_size=1, verbose=True, veryverbose=True)
