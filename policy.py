# policy.py
""" program to drop lowest grade for a student, or implement other policy """
# Ronald L. Rivest
# 5/13/17

# policy.py is used by student ranking program rank.py

##############################################################################
# All class-specific policy implementations go in this section between ###'s.
# Change the following drop policy, or have rank.py
# pass along a different policy, in order to change the dropping behavior
# Set DROP_POLICY to the empty list to have no items dropped.
# Items that don't have corresponding columns in the data are just ignored.

DROP_POLICY = [(2, "H1", "H2", "H3", "H4", "H5", "H6"), # drop lowest two psets
               (1, "Q1", "Q2"),                         # drop lowest one quiz
               (2, "pset1", "pset2", "pset3", "pset4", "pset5", "pset6"),
               # variant spellings?
               (1, "quiz1", "quiz2")]

RANK_WEIGHT = 0.5    # Average scaled rank and scaled grades.

##############################################################################

MISSING = "--"
def ismissing(x):
    """ Return True if x is MISSING. """
    return x == MISSING

def isnonnumeric(x):
    """ Return True if x looks to be non-numeric """
    try:
        x = float(x)
    except ValueError:
        return True
    return False

def compute_wtd_scores(state):
    """  Compute weighted average scores. """
    wtd_score = [0 for stu in state.students]
    for stu in state.students:
        total = 0.0
        total_weight = 0.0
        for col in state.columns:
            if state.weights[col] > 0:
                d = state.data[stu][col]
                if not ismissing(d):
                    total += state.weights[col] * d
                    total_weight += state.weights[col]
        if total_weight > 0:
            wtd_score[stu] = total / total_weight
        else:
            wtd_score[stu] = 0.0
    return wtd_score

def drop(state, drop_policy=DROP_POLICY):
    """
    Drop some of the student scores and
    return resulting modified scores.
    Dropping is effected by replacing some values by MISSING.
    Drop policy has the form (by example):
        [ (2, "H1", "H2", "H3", "H4", "H5"), # drop lowest two homeworks
          (1, "Q1", "Q2")                    # drop lowest quiz
        ]
    Note that here "lowest" is intended to refer to scores, not grades.
    """
    print_drop_policy(state.names, drop_policy)
    new_scores = []
    for score_row in state.data:
        for drop_policy_item in drop_policy:
            score_row = process_drop_policy_item(state.names,
                                                 score_row,
                                                 drop_policy_item)
        new_scores.append(score_row)
    new_state = state.copy()
    new_state.data = new_scores
    return new_state

def process_drop_policy_item(names, score_row, drop_policy_item):
    """
    Return score_row after effecting given drop_policy item.
    Here drop_policy_item is, e.g. (1, "Q1", "Q2") (E.g. drop lowest quiz.)
    Dropping is effected by replacing values by MISSING in score_row
    """
    k = drop_policy_item[0]
    drop_policy_names = drop_policy_item[1:]
    common_names = [name for name in drop_policy_names if name in names]
    d = dict()
    for name, score in zip(names, score_row):
        d[name] = score
    for name in common_names:
        if d[name] == MISSING:
            d[name] = -1
    L = [(d[name], name) for name in common_names]
    L = sorted(L, key=lambda x: x[0])
    L = L[:k]            # list of items to drop
    for score, name in L:
        d[name] = MISSING             # i.e. dropped
    for name in d:
        if d[name] == -1:
            d[name] = MISSING
    score_row = [d[name] for name in names]
    return score_row

def print_drop_policy(names, drop_policy=DROP_POLICY):
    """
    Print out the specified drop policy for dropping items
    from a student's record for grading purposes.
    """
    print("Drop policies in effect for the ranking program (version 0.3):")

    print()
    print("Effecting the following drop policy:")
    for drop_policy_item in drop_policy:
        k = drop_policy_item[0]
        drop_policy_names = drop_policy_item[1:]
        common_names = [name for name in drop_policy_names if name in names]
        if len(common_names) > 0:
            print("    Dropping lowest %d from:"%k, end=' ')
            for name in common_names:
                print(name, end=' ')
            print()
