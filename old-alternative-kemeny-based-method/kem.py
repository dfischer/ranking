# kem.py
# Ronald L. Rivest
# Heuristics for maximizing Kemeny score
# 2015-12-31

"""
Assume a given  m x m  matrix A, and assume a given
list L that specifies a subset of range(m) in some
arbitrary order.  (At the top level L = range(m), but
smaller Ls may be used during recursion or optimization.)

The goal is to produce a permutation of L that maximizes
    K(A,L) = sum_{i<j} A[L[i]][L[j]]
which is one version of the Kemeny score.

In the case that A[i][j] is the number of voters preferring
candidate i to candidate j, then K(A,L) is the sum, over all
pairs of candidates (i,j) where i is listed ahead of j in L,
of the number of voters preferring i to j.

While optimizing K(A,L) is NP-hard in general, we are happy
here with heuristics that may provide approximate optimization.
Some of our heuristics (e.g. those based on the dynamic programming
approch in "merge", may be new.
"""

import itertools
import math
import random

def K(A,L=None):
    """ 
    Function we are trying to maximize: sum_{i<j} A[L[i]][L[j]]
    A is m x m matrix, 
    L is a subset of range(m) (or defaults to range(m) if no L given)
    """
    if L==None:
        L = range(len(A))
    return sum([A[L[i]][L[j]] for j in range(len(L)) for i in range(j)])

##############################################################################
## Test matrix generation
##############################################################################

betavariate = random.betavariate

def test_A(m, test_type=1, **kwargs):
    """
    Return an  m x m  test matrix (preferential matrix), of given type.
    """
    if test_type == 1:    # ad-hoc, large integer values
        N = 10**12
        A = [[int(N*math.sin(i+3)*math.sqrt(j+3)) \
              for j in range(m)] for i in range(m)]
        return A
    if test_type == 2:    # ad-hoc, small integer values
        N = 10**1
        A = [[abs(int(N*math.sin(i+3)*math.sqrt(j+3))) \
              for j in range(m)] for i in range(m)]
        return A
    if test_type == 3:    # beta distribution for each [i][j] -- [j][i] split
        A = [[0 for j in range(m)] for i in range(m)]
        alpha = kwargs.get('alpha',3)     # 'successes' seen
        beta = kwargs.get('beta',2)       # 'failures' seen
        n = kwargs.get('n', 100)          # number of 'voters'
        for i in range(m):
            for j in range(m):
                x = betavariate(alpha,beta) # draw x from beta distribution
                if i<j:
                    A[i][j] = int(x*n)
                elif i>j:
                    A[i][j] = int((1.0-x)*n)
        return A

##############################################################################
## End test matrices
##############################################################################

def BF(A,L=None):
    """
    Solve the K-maximization problem by Brute Force.
    Here A is an m x m matrix, and L is a subset of range(m).
    Return best permutation and its K-value.
    """
    if L==None:
        L = range(len(A))
    best_p = L
    best_K = K(A,L)
    for p in itertools.permutations(L):
        Kp = K(A,p)
        if Kp>best_K:
            best_K = Kp
            best_p = p
    return best_p, best_K

def test_BF():
    """ Test BF implementation """
    m = 9            
    A = test_A(m, 1)
    best_p, best_K = BF(A)
    # print best_p, best_K
    assert best_p == (5, 4, 6, 0, 3, 7, 8, 1, 2) 
    assert best_K == 27047279315230

test_BF()

##############################################################################
## implementation of Tideman's ranked pairs voting method (RP)
## https://en.wikipedia.org/wiki/Ranked_pairs
## (The RP method is not used here any more, but is kept for reference purposes.)
##############################################################################

def sorted_pairs(A, L=None):
    """ 
    Input A is an m x m matrix of pairwise preferences (numbers)
          A[i][j] is number of voters preferring i to j
          L is a subset of range(m)
    Output is a sorted list of pairs, decreasing order of strength,
          from L x L
    Uses Tidemans criterion for comparison:
       (i,j) > (k, l) if
           Aij > Akl, or
           Aij == Akl and Aji < Alk
    (Ties that still exist are broken using random numbers as tie-breakers.)
    """
    m = len(A[0])
    if L == None:
        L = range(m)
    pairs = [(A[i][j], -A[j][i], random.random(), i, j) for i in L for j in L if i != j ]
    pairs = sorted(pairs, reverse=True)
    return [(i,j) for (Aij, negAji, rand, i, j) in pairs]

def test_sorted_pairs():
    A = [ [  0,  6,  9 ],
          [  7,  0, 11 ],
          [ 13, 12,  0 ]]
    assert sorted_pairs(A) == \
        [(2, 0), (2, 1), (1, 2), (0, 2), (1, 0), (0, 1)]
    # assertion always true since there are no ties...

test_sorted_pairs()

def reachable(Adj, s, t):
    """
    Adj is adjacency list rep of graph
    Return True if edges in Adj have directed path from s to t.

    Note that this routine is one of the most-used and most time-consuming
    of this whole procedure, which is why it is passed an adjacency list 
    rep rather than a list of vertices and edges, since the adjacency list
    rep is easy to update when a new edge is committed to in RP.
    """
    # search for path
    Q = [ s ]         # vertices to expand
    R = set([s])      # reachable
    while Q:
        i = Q.pop()
        for j in Adj[i]:
            if j == t:
                return True
            if j not in R:
                R.add(j)
                Q.append(j)
    return False

def RP(A, L=None):
    """ 
    Ranked-pairs algorithm.
    Input: A is m x m preference matrix.
           L is a subset of range(m) (or omitted, meaning range(m))
    Output is a permutation of L. (Most favored first)
    """
    m = len(A)
    if L==None:
        L=range(m)
    V = L
    E = sorted_pairs(A, L)
    CE = [ ]                      # committed edges
    Adj = { i:[] for i in V }     # adj list for committed edges
    for (i,j) in E:
        if not reachable(Adj, j, i):
            CE.append((i,j))
            Adj[i].append(j)
    beats = { i:0 for i in V }    # number that i beats
    for (i,j) in CE:
        beats[i] += 1
    B = [ (beats[i], i) for i in V ]
    B = sorted(B, reverse=True)
    order = [ i for (c, i) in B ]
    return order, K(A, order)

def test_RP():
    A = [ [ 0, 6, 9 ], \
          [ 7, 0, 11 ], \
          [ 13, 12, 0 ]]
    RP_order, RP_K = RP(A)
    assert RP_order == [2, 1, 0]
    assert RP_K == 32

test_RP()

def IRP(A, L=None):
    # iterate RP with different random number seeds,
    # to optimize over tie-breaking choices
    # The "best" output is the one that maximizes the K value
    trials = 100
    best_K = 0
    m = len(A)                        # candidates (students)
    for seed in range(trials):
        # print "Random number seed =", seed
        random.seed(seed)                
        RP_order, RP_K  = RP(A, L)                   
        if RP_K > best_K:
            best_order, best_K = RP_order, RP_K
            print "new best rating for ranked-pairs order = ", RP_K
    return best_order, best_K

def test_RP():
    """ Test the RP method. """
    m = 9
    print "m = 9"
    A = test_A(m,3)
    # for row in A:
    #     print row
    print "BF:", BF(A)
    print "RP:", RP(A)
    print "IRP:", IRP(A)
    for m in range(10, 100, 10):
        print "m = ",m
        A = test_A(m,3)
        print "RP:", RP(A)
        print "IRP:", IRP(A)
        print

# test_RP()    

##############################################################################
## end of ranked-pairs (RP) implementation
##############################################################################

def merge(A, L, M):
    """
    A is an input matrix of size m x m
    L and M are disjoint subsets of range(m)
    Return the merge N of L and M with maximum K value.

    This is a dynamic-programming algorithm. O(m^3) time.
    The formulation of this "merge" proglem and the use of dynamic
    programming to solve it may be the most novel aspect of our approach.
    """
    m = len(A)
    nL = len(L)
    nM = len(M)
    if nL == 0:
        return M
    if nM == 0:
        return L
    # Dynamic programming
    # B[i][j] is best (largest) K-value for merge of L[:i],M[:j]
    # C[i][j] indicates choice made to achieve that value ('L' or 'M' last)
    B = [[0 for j in range(nM+1)] for i in range(nL+1)]
    C = [['-' for j in range(nM+1)] for i in range(nL+1)]
    # fill in first row
    for j in range(1, nM+1):
        B[0][j] = K(A,M[:j])
        C[0][j] = 'M'
    # fill in first column
    for i in range(1, nL+1):
        B[i][0] = K(A,L[:i])
        C[i][0] = 'L'
    # upper-left entry, though, has no predecessor
    C[0][0] = '-'
    # fill in bulk of matrix
    for i in range(1, nL+1):
        for j in range(1, nM+1):
            # K value if L is last
            KL = B[i-1][j]
            for x in L[:i-1]:
                KL += A[x][L[i-1]]
            for y in M[:j]:
                KL += A[y][L[i-1]]
            # K value if M is last
            KM = B[i][j-1]
            for x in L[:i]:
                KM += A[x][M[j-1]]
            for y in M[:j-1]:
                KM += A[y][M[j-1]]
            # maximize
            if KL > KM:
                B[i][j] = KL
                C[i][j] = 'L'
            else:
                B[i][j] = KM
                C[i][j] = 'M'
    # return answer -- backtrack through B,C matrices
    N = [ ]              # accumulate in reverse order
    i = nL
    j = nM
    while i>0 or j>0:
        if C[i][j] == 'L':
            N.append(L[i-1])
            i = i-1
        elif C[i][j] == 'M':
            N.append(M[j-1])
            j = j-1
    N.reverse()
    return N, B[nL][nM]

def is_subsequence(L, M):
    """ Return True if L is a subsequence of M """
    j = 0
    for i in range(len(L)):
        try:
            j = M.index(L[i], j)
        except ValueError:
            return False
    return True

def test_is_subsequence():
    assert is_subsequence([], [1, 2, 3])
    assert is_subsequence([1], [1, 2, 3])
    assert is_subsequence([1, 3], [1, 2, 3])
    assert is_subsequence([1,2,3], [1,2,3])
    assert not is_subsequence([5], [1, 2, 3])
    assert not is_subsequence([5], [])
    assert not is_subsequence([1,2,6],[1,2,3])

test_is_subsequence()

def test_merge():
    A = test_A(4, 3)
    L = [0, 2]
    M = [1, 3]
    N, KN = merge(A, L, M)
    # print "N, KN = ", N, KN
    for NN in itertools.permutations(N):
        if is_subsequence(L, NN) and is_subsequence(M, NN):
            KNN = K(A,NN)
            if KNN > KN:
                print "A = ", A
                print "L = ", L
                print "M = ", M
                print "N = ", N
                print "KN = ", KN
                print "NN = ", NN
                print "KNN = ", KNN
                assert KNN <= KN
            # print NN, KNN

def random_split(L, nM=None):
    """
    Split sequence L into two random subsequences M, N
    Length of M will be nM (defaults to len(L)//2)
    Return M, N
    """
    nL = len(L)
    if nM == None:
        nM = nL//2
    mark = [False for _ in range(nL)]
    for i in random.sample(range(nL), nM):
        mark[i] = True
    M = [ L[i] for i in range(nL) if mark[i] ]
    N = [ L[i] for i in range(nL) if not mark[i] ]
    return M, N

def random_nontrivial_split(L, Mmaxlen = None):
    """ 
    Same as random_split, but both lists are non-empty if possible.
    Length of M not to exceed Mmaxlen
    """
    if len(L)<2:
        return L
    M = []
    N = []
    while M == [] or N == []:
        M, N = random_split(L, Mmaxlen)
    return M, N

def test_random_nontrivial_split(Mmaxlen = None):
    L = [1, 2, 3, 4, 5]
    for _ in range(30):
        print random_nontrivial_split(L, Mmaxlen)

# test_random_nontrivial_split(2)

def split_merge(A, L, steps=100, nM=None):
    """ 
    Use iterative split-merge heuristic to optimize K(A, L)
    Return optimized list L and associate K score, KL.
    """
    for _ in range(steps):
        M, N = random_nontrivial_split(L,nM)
        L, KL = merge(A, M, N)
        # print L, KL
    return L, KL

def dc(A, L=None):
    """ 
    Use divide-and-conquer approach to approximately 
    optimize K(A, L); split-merge is used as a subroutine.

    This method can get a very good initial approximation
    quickly; further optimization can be obtained using
    repeated calls to split_merge.
    """
    m = len(A)
    if L == None:
        L = range(m)
    if len(L)<7:
        return BF(A, L)
    nL = len(L)
    nLmid = int(len(L)/2)
    L1, KL1 = dc(A, L[:nLmid])
    L2, KL2 = dc(A, L[nLmid:])
    L, KL = merge(A, L1, L2)
    return split_merge(A, L, 1)

def test_and_compare():
    """ Compare SM, RP, and DC methods """
    m = 300
    A = test_A(m,3)
    L = [m-i-1 for i in range(m)]      # pessimal starting order for type 3
    SML, SMKL = split_merge(A, L)
    print "SM:", SML, SMKL
    RPL, RPKL = RP(A, L)
    print "RP:", RPL, RPKL
    DCL, DCKL = dc(A, L)
    print "DC:", DCL, DCKL
    for i in range(60):
        SML, SMKL = split_merge(A, SML)
        print SMKL
        
# test_and_compare()    
    
    
