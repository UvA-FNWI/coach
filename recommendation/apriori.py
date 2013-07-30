'''
Implementation of the a priori algorithm, found in 'Fast discovery of association rules' by Agrawal et al.

Auth: Auke Wiggers
Date: 29-07
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
        C_k = apriori_gen(L[k-1], k)            # create new candidate
        for transaction in D['transactions'].itervalues():
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

def apriori_TID(D, L, verbose=True, minsup=2):
    '''
    Version of the apriori algorithm that uses the database directly to
    generate candidates.

    D : Database containing transactions
    L : Input dictionary containing L[1]
    '''
    if verbose:
        print '===Apriori TID==='
    candidate_count = defaultdict(int)
    C__ = {0: items_to_setofitemsets(D['transactions'])}
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

        if verbose and len(L[k]) > 0:
            print '==== Iteration {} ===='.format(k)
            display_dict('C{}'.format(k), C_k)
            display_dict('C__{}'.format(k), C__[k])
            display_dict('L{}'.format(k), L[k])

        L[k] = {c: count for c, count in C_k.iteritems() if count >= minsup}
        k += 1
    return L

def subset(candidate_set, transaction):
    ''' Subset function finds the candidates contained in the transaction.

    candidate_set:  set of items that are candidates
    transaction:    set of items present in the transaction

    Returns the remainder of the candidate set after item selection.
    '''
    return (c for c in candidate_set if c in
            (x for x in combinations(transaction, len(c))))

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
            if candidate not in C_k and not \
                any( (subset_c not in L_kmin1 for subset_c in
                      combinations(candidate, k)) ):
                C_k[candidate] = 0
    return C_k

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
        print str(k).ljust(8),
        try:
            for v_ in v:
                print str(v_).ljust(10),
            print ''
        except:
            print v
    print ''

if __name__ == '__main__':
    '''
    example db from:
    http://www.cs.helsinki.fi/u/htoivone/pubs/advances.pdf

    '''
    D = {'transactions': {100: (1,3,4),
                          200: (2,3,5),
                          300: (1,2,3,5),
                          400: (2,5),
                          }
         }
    L = {0: {(1,): 2,
             (2,): 3,
             (3,): 3,
             (5,): 3}
         }
    try:
        minsup=float(sys.argv[1])
    except:
        print 'Usage: python apriori.py <minsup>'
        sys.exit(0)
    apriori(D, L, minsup=minsup)
    apriori_TID(D, L, minsup=minsup)
