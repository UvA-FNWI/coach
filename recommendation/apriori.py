'''
Implementation of the a priori algorithm, found in 'Fast discovery of association rules' by Agrawal et al.

Auth: Auke Wiggers
Date: 29-07
'''

itemset = []

def apriori(minsup):
    ''' The apriori algorithm itself consists of two phases:
    First, generate new candatate C_k, then scan the database and count
    support of candidates in C_k.

    L_k:     Set of large k-itemsets.
    C_k:     Set of candidate k-itemsets.
    D:       Dataset containing transactions.
    minsup:  Support threshold

    '''
    candidate_count = dict()

    # Define the first itemset (k=1)
    L[1] = set()
    for k in range(2, len(L_k)):
        C_k = apriori_gen(L[k-1])            # create new candidate
        for transaction in D.transactions:
            C_t = subset(C_k, transaction)   # candidates contained in t
            for candidate in C_t:
                candidate_count[candidate] += 1
        L_k = [c for c in C_k if candidate_count[c] >= minsup]

    return L_k

def apriori_TID(D):
    '''
    D : Database containing transactions
    '''
    L = {1: set()} # large 1-itemsets
    C_ = {1: D}
    for k in range(2, len(L_k)):
        pass


def subset(candidate_set, transaction):
    ''' Subset function finds the candidates contained in the transaction.

    candidate_set:  set of items that are candidates
    transaction:    set of items present in the transaction

    Returns the remainder of the candidate set after item selection.
    '''
    return (c for c in candidate_set if c in transaction)

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
    C_k = set()
    for p,q in itertools.izip(L_kmin1, L_kmin1):
        if p[:k-1] == q[:k-1]:
            candidate = p[:k-1] + sorted([p[k-1], q[k-1]])
            if candidate not in C_k and not \
                any( (subset_c not in L_kmin1 for subset_c in
                      itertools.combinations(c, k-1)) ):
                C_k.add(candidate)
    return C_k
