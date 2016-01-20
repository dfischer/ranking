# policy.py
# program to drop lowest grade for a student, or implement other policy
# Ron Rivest
# 1/20/16

# policy.py is used by student ranking program rank.py

# Change the following drop policy, or have rank.py
# pass along a different policy, in order to change the dropping behavior
# Set DROP_POLICY to the empty list to have no items dropped.
# Items that don't have corresponding columns in the data are just ignored.

DROP_POLICY = [ (2, "H1", "H2", "H3", "H4", "H5", "H6"),      # drop lowest two psets
                (1, "Q1", "Q2"),                              # drop lowest one quiz
                (2, "pset1", "pset2", "pset3", "pset4", "pset5", "pset6"), # variant spellings?
                (1, "quiz1", "quiz2")
              ]

MISSING = "--"

def isnonnumeric(x):
    """ Return True if x looks to be non-numeric """
    try:
        x = float(x)
    except ValueError:
        return True
    return False

def drop(names, weights, scores, drop_policy=DROP_POLICY):
    """
    Drop some of the student scores and return resulting modified scores.
    Dropping is effected by replacing some values by MISSING.
    Drop policy has the form (by example):
        [ (2, "H1", "H2", "H3", "H4", "H5"),           # drop lowest two homeworks
          (1, "Q1", "Q2")                              # drop lowest quiz
        ]                        
    Note that here "lowest" is intended to refer to scores, not grades.
    """
    print_drop_policy(names, drop_policy)
    new_scores = []
    for score_row in scores:
        for drop_policy_item in drop_policy:
            score_row = process_drop_policy_item(names, weights, score_row, drop_policy_item)
        new_scores.append(score_row)
    return new_scores

def compare(x, y):
    """
    Return a negative, zero, or positive value if x < y, x==y, or x>y.
    Treat MISSING or nonnumeric is small.
    Here x, y are pairs (x0, x1), (y0, y1) e.g. (0.33, "H1") or ("--", "Q2").
    """
    x0, x1 = x
    if x0 == MISSING or isnonnumeric(x0):
        x0 = float("-inf")
    y0, y1 = y
    if y0 == MISSING or isnonnumeric(y0):
        y0 = float("-inf")
    if x0 < y0:
        return -1
    if x0 > y1:
        return 1
    if x1 < y1:
        return -1
    if x1 > y1:
        return 1
    return 0

def process_drop_policy_item(names, weights, score_row, drop_policy_item):
    """
    Return score_row after effecting given drop_policy item.
    Here drop_policy_item is, e.g. (1, "Q1", "Q2") (E.g. drop lowest quiz.)
    """
    k = drop_policy_item[0]
    drop_policy_names = drop_policy_item[1:]
    common_names = [name for name in drop_policy_names if name in names]
    d = dict()
    for name, score in zip(names, score_row):
        d[name] = score
    L = [(d.get(name,MISSING), name) for name in common_names]
    L = sorted(L, cmp=compare) 
    L = L[:k]            # list of items to drop
    for score, name in L:
        d[name] = MISSING             # i.e. dropped
    score_row = [ d[name] for name in names ]
    return score_row

def print_drop_policy(names, drop_policy=DROP_POLICY):
    """
    Print out the specified drop policy for dropping items from a student's record 
    for grading purposes.
    """
    print "Effecting the following drop policy:"
    for drop_policy_item in drop_policy:
        k = drop_policy_item[0]
        drop_policy_names = drop_policy_item[1:]
        common_names = [name for name in drop_policy_names if name in names]
        if len(common_names)>0:
            print "    Dropping lowest %d from:"%k,
            for name in common_names:
                print name,
            print        
    


        
