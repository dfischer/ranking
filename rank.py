# student ranking program (rank.py)
# Ron Rivest
# 1/15/16

"""
This is a program to produce an overall student ranking, given
as input a spreadsheet given student scores on various grade
components, and given weights for those components.
"""

""" (Distributed under MIT License) """

import argparse
import copy
import csv
import sys

import policy

class State():
    """
    The main data structure, consisting of:
        a row of n_col column names
        a row of n_col column weights  (zero weight for items not part of grade computation)
        a table of n_stu rows, each of n_col items, of grade or score data
    """
    def __init__(self, names, weights, data):
        self.names = copy.copy(names)
        self.weights = copy.copy(weights)
        self.data = copy.deepcopy(data)

        self.n_col = len(names)
        self.columns = range(self.n_col)
        self.n_stu = len(data)
        self.students = range(self.n_stu)

        assert len(names) == len(weights)
        for stu in self.students:
            assert len(data[stu]) == len(names)

    def copy(self):
        return State(self.names, self.weights, self.data)

##############################################################################
## Beginning of ranking program
##############################################################################

def read_csv(input_filename):
    """ 
    Return list of rows of a CSV file. 

    Be careful: the values read from csv are all STRINGS, and must be 
    converted to numeric data types as appropriate.
    """
    print "Reading input file:", input_filename
    with open(input_filename, 'rU') as csvfile:   
        reader = csv.reader(csvfile)
        return [row for row in reader]

def parse_csv(rows, skiprows=0, maxgraderows=10000):
    """ 
    Parse given list of rows from CSV file.
    Return a new State with
       column names, 
       column weights
           positive numeric     --> weight for weighting in grade
           zero                 --> not part of grade
       data rows of student grades.

    The input file format is:
        'skiprows' rows to be skipped
        a header row giving column names
        a weight row given component weights for components to be included
          (a zero, non-numeric or missing weight means to ignore this column for grade;
           it will be converted to zero internally)
        a number of rows of data, one per student
    At most the first 'maxgraderows' of student grade data will be read.
    """
    rows = rows[skiprows:]
    names = rows[0]
    names = [ name.strip() for name in names ]
    weights = rows[1]
    weights = [ max(0, convert_to_float_if_possible(w,0)) for w in weights ]
    grades = rows[2:maxgraderows]
    return State(names, weights, grades)

# MISSING DATA (marked by sentinel value "--")
MISSING = "--"
def ismissing(x):
    return (x == MISSING)

def isnonnumeric(x):
    """ Return True if x looks to be non-numeric """
    try:
        x = float(x)
    except ValueError:
        return True
    return False

def convert_to_float_if_possible(x, elsevalue=MISSING):
    """ 
    Return float version of value x, else elsevalue (MISSING or other specified value
    if conversion fails 
    """
    if isnonnumeric(x):
        return elsevalue
    else:
        return float(x)

def convert_data(state):
    """
    convert all grade data to floats, 
    with MISSING for data that doesn't convert to a float.
    """
    new_state = state.copy()
    for col in state.columns:
        w = convert_to_float_if_possible(state.weights[col], 0)
        if w>0:
            for stu in state.students:
                new_state.data[stu][col] = convert_to_float_if_possible(state.data[stu][col])
    return new_state

def print_grade_components(state):
    print "Column names (with weights for those being included in grade):"
    for col in state.columns:
        print "  %10s"%state.names[col],
        if state.weights[col]>0:
            print "weight", "%g"%state.weights[col]
        else:
            print "------"

def datum_str(datum, width, sep):
    """
    Return string rep of data item.
    """
    if isnonnumeric(datum):
        return ("%"+str(width)+"s"+sep)%datum
    else:
        if datum == int(float(datum)):
            return ("%"+str(width)+"d"+sep)%int(float(datum))
        else:
            return ("%"+str(width)+".3f"+sep)%float(datum)

def build_output(state, stu_order,sep):
    """
    Build and return string for later output to file (or equivalent I/O).
    Give names, weights, and then the rows in data (one per student).
    The order of the rows is given by stu_order.
    Sep is what to put between data elements:
        either "," (for csv use) or " " (for screen).
    """

    # first compute column widths for printing
    width = [0]*(state.n_col+1)
    for col, name in enumerate(state.names):
        width[col] = max(width[col],len(str(name.strip())))
    for rank, stu in enumerate(stu_order):
        for col in state.columns:
            datum = state.data[stu][col]
            width[col] = max(width[col],len(datum_str(datum, 0, sep)))

    # now build list of items for output
    items = []
    for col, name, in enumerate(state.names):
        items.append(("%"+str(width[col])+"s"+sep)%(name.strip()))
    items.append("\n")
    # Data rows, one per student:
    for rank, stu in enumerate(stu_order):
        for col in state.columns:
            datum = state.data[stu][col]
            items.append(datum_str(datum, width[col], sep))
        items.append("\n")
    return "".join(items)

def compute_scores(state):
    """ 
    Return new state with data converted to rank-based scores.
    """
    stu_per_comp = [ 0  for col in state.columns ]
    weight_per_stu = [ 0 for stu in state.students ]
    beats = [ [ 0 for col in state.columns ] for stu in state.students ]

    # compare all pairs stu,stu2 of students
    # beats[stu][col] is number of other students in same column this student beats
    # where a student beats himself by one (+1)
    # and beats others with same score by one-half (0.5)
    for stu in state.students:
        for col in state.columns:
            if state.weights[col]>0:
                d1 = state.data[stu][col]
                if not ismissing(d1):
                    stu_per_comp[col] += 1
                    weight_per_stu[stu] += state.weights[col]
                    for stu2 in state.students:
                        d2 = state.data[stu2][col]
                        if not ismissing(d2):
                            if stu == stu2:
                                beats[stu][col] += 1.0
                            elif d2 == d1:
                                beats[stu][col] += 0.5
                            elif d1 > d2:
                                beats[stu][col] += 1.0
    return normalize_scores(state, beats, stu_per_comp)

def normalize_scores(state, beats, stu_per_comp):
    """
    Return normalized scores (in beats) to [0,1] by dividing by 
    one plus the number of students in the component component
    preserve missing or other data "as is"
    """
    new_state = state.copy()
    for stu in state.students:
        for col in state.columns:
            if state.weights[col]>0:
                if not ismissing(state.data[stu][col]):
                    new_state.data[stu][col] = beats[stu][col] / (float(stu_per_comp[col]) + 1.0)
                else:
                    new_state.data[stu][col] = MISSING
            else:
                new_state.data[stu][col] = state.data[stu][col]
    return new_state

def compute_ranks(state):
    """
    Compute weighted average score and new ranks.

    Return new student ordering (best to worst), weighted scores per student,
    ranks of students (1 is best).
    """

    # compute avg_score per student as weighted sum of component scores
    wtd_score = [0 for stu in state.students]
    for stu in state.students:
        total = 0.0
        total_weight = 0.0
        for col in state.columns:
            if state.weights[col]>0:
                d = state.data[stu][col]
                if not ismissing(d):
                    total += state.weights[col] * d
                    total_weight += state.weights[col]
        wtd_score[stu] = total / total_weight

    L = sorted([ (wtd_score[stu], stu) for stu in state.students ], reverse=True)
    stu_order = [ stu for (ws, stu) in L ]
    wtd_score = [ ws for (ws, stu) in L ]
                
    ranks = range(1, state.n_stu+1)
    return stu_order, wtd_score, ranks

def add_column(state, new_name, new_weight, values, stu_order):
    """ Return state with new column added. """
    new_state = state.copy()
    new_state.names.append(new_name)
    new_state.weights.append(new_weight)
    new_state.n_col += 1
    new_state.columns = range(new_state.n_col)
    for r, stu in enumerate(stu_order):
        new_state.data[stu].append(values[r])
    return new_state

def add_columns(state, stu_order, wtd_score):
    """
    Return new state with students in given order, and with
    two new columns: wtd_score and rank
    """
    state = add_column(state, "wtd_score", 0, wtd_score, stu_order)
    state = add_column(state, "rank", 0, range(1, state.n_stu+1), stu_order)
    return state

def print_and_write_to_file(title, state, stu_order, file_name):
    """ 
    Write data to terminal and to output file with given filename.
    Here data is grades or scores.
    """
    print "-"*80 + "\n" + title
    print build_output(state, stu_order," "),
    print "-"*80

    with open(file_name,"w") as file:
        file.write(build_output(state, stu_order,", "))
    print file_name, "written."
    print

def main():
    print "--------------------------------------------"
    print "-- Student ranking program (rank.py)      --"
    print "-- Version 0.2 (1/19/16) Ronald L. Rivest --"
    print "--------------------------------------------"

    # PARSE ARGUMENTS 
    parser = argparse.ArgumentParser(description='Rank-order students based on performance.')
    parser.add_argument('input_filename',help='csv file with header row, weight row, and then one grade row per student')
    parser.add_argument('--skiprows',default=0,help='number of rows to skip before header row')
    args = parser.parse_args()

    input_filename = args.input_filename
    skiprows = int(args.skiprows)
    maxgraderows = 10000

    # READ AND CLEAN UP DATA
    rows = read_csv(input_filename)
    state = parse_csv(rows, skiprows, maxgraderows)
    grade_state = convert_data(state)
    print_grade_components(grade_state)
    print grade_state.n_stu, "students"

    # COMPUTE SCALED SCORES 
    # scores has one row per student, one column per original grades column
    score_state = compute_scores(grade_state)

    # COMPUTE WEIGHTED AVERAGE SCORES AND RANKS
    stu_order, wtd_score, ranks = compute_ranks(score_state)

    sorted_grade_state = add_columns(grade_state, stu_order, wtd_score)
    sorted_score_state = add_columns(score_state, stu_order, wtd_score)

    # OUTPUT RESULTS
    title = "LISTING OF ALL STUDENTS (BEST FIRST) WITH RAW GRADES:"
    print_and_write_to_file(title, sorted_grade_state, stu_order, 
                            input_filename+".1.grades.rank.csv")

    title = "LISTING OF ALL STUDENTS (BEST FIRST) WITH SCALED SCORES:"
    print_and_write_to_file(title, sorted_score_state, stu_order, 
                            input_filename+".2.scores.rank.csv")

    if policy.DROP_POLICY != []:
        # ADJUST: DROP WORST HOMEWORK, ETC. ACCORDING TO POLICY
        adjusted_score_state = policy.drop(score_state.copy())

        # THEN RECOMPUTE WEIGHTED SCORES AND NEW RANKS
        print "Recomputing weighted scores and ranks..."
        stu_order, wtd_score, ranks = compute_ranks(adjusted_score_state)
        
        adjusted_score_state = add_columns(adjusted_score_state, stu_order, wtd_score)

        title = "LISTING OF ALL STUDENTS (BEST FIRST) WITH SCALED AND DROPPED SCORES:"
        print_and_write_to_file(title, adjusted_score_state, stu_order, 
                                input_filename+".3.droppedscores.rank.csv")
        
main()


