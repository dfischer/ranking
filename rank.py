# student ranking program (rank.py) 
# Ron Rivest
# 1/25/16 (modified 5/13/17)
# Version 0.3
# python3

"""
This is a program to produce an overall student ranking, given
as input a spreadsheet given student scores on various grade
components, and given weights for those components.

All class-specific policy code and data go into policy.py
"""

# Distributed under MIT License

import argparse
import copy
import csv

import policy

class State():
    """
    The main data structure, consisting of:
        a row of n_col column names
        a row of n_col perfect_grade values
        a row of n_col column weights  (zero weight for items not
            part of grade computation)
        a table of n_stu rows, each of n_col items, of grade or score data
    """
    def __init__(self, names, perfect_grades, weights, data):
        self.names = copy.copy(names)
        self.perfect_grades = copy.copy(perfect_grades)
        self.weights = copy.copy(weights)
        self.data = copy.deepcopy(data)

        self.n_col = len(names)
        self.columns = list(range(self.n_col))
        self.n_stu = len(data)
        self.students = list(range(self.n_stu))

        assert len(names) == len(perfect_grades)
        assert len(names) == len(weights)
        for stu in self.students:
            assert len(data[stu]) == len(names)

    def copy(self):
        """ Return copy of this State object. """
        return State(self.names, self.perfect_grades, self.weights, self.data)

##############################################################################
## Beginning of ranking program
##############################################################################

def read_csv(input_filename):
    """
    Return list of rows of a CSV file.

    Be careful: the values read from csv are all STRINGS, and must be
    converted to numeric data types as appropriate.
    """
    print("Reading input file:", input_filename)
    with open(input_filename, 'rU') as csvfile:
        reader = csv.reader(csvfile)
        return [row for row in reader]

def parse_csv(rows, skiprows=0, maxgraderows=10000):
    """
    Parse given list of rows from CSV file.
    Return a new State with
       column names,
       column perfect_grades
       column weights
           positive numeric     --> weight for weighting in grade
           zero                 --> not part of grade
       data rows of student grades.

    The input file format is:
        'skiprows' rows to be skipped
        a header row giving column names (names of components)
        a perfect_grade row giving max possible grade for each component
        a weight row given component weights for components to be included
          (a zero, non-numeric or missing weight means to ignore this
               column for grade; it will be converted to zero internally)
        a number of rows of data, one per student
    At most the first 'maxgraderows' of student grade data will be read.
    """
    rows = rows[skiprows:]
    names = rows[0]
    names = [name.strip() for name in names]
    perfect_grades = rows[1]
    perfect_grades = [max(0, convert_to_float_if_possible(pg, 0)) for pg in perfect_grades]
    weights = rows[2]
    weights = [max(0, convert_to_float_if_possible(w, 0)) for w in weights]
    grades = rows[3:maxgraderows]
    return State(names, perfect_grades, weights, grades)

# MISSING DATA (marked by sentinel value "--")
MISSING = "--"
def ismissing(x):
    """ Return True if x is a missing datum. """
    return x == MISSING

def isnonnumeric(x):
    """ Return True if x looks to be non-numeric """
    try:
        x = float(x)
    except ValueError:
        return True
    return False

def convert_to_float_if_possible(x, elsevalue=MISSING):
    """
    Return float version of value x, else elsevalue
    (MISSING or other specified value) if conversion fails
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
        if w > 0:
            for stu in state.students:
                new_state.data[stu][col] = \
                    convert_to_float_if_possible(state.data[stu][col])
    return new_state

def print_grade_components(state):
    """ Print components of grades with their perfect_grades and weights. """
    print("Column names (with perfect_grades and weights for those being included in grade):")
    for col in state.columns:
        print("  %10s"%state.names[col], end=' ')
        if state.weights[col] > 0:
            print("perfect grade: %7.3f  "%state.perfect_grades[col], end='')
            print("weight:", "%g"%state.weights[col])
        else:
            print("------")

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

def build_output(state, sep):
    """
    Build and return string for later output to file (or equivalent I/O).
    Give names, weights, and then the rows in data (one per student).
    Sep is what to put between data elements:
        either "," (for csv use) or " " (for screen).
    """

    # first compute column widths for printing
    width = [0]*(state.n_col+1)
    for col, name in enumerate(state.names):
        width[col] = max(width[col], len(str(name.strip())))
    for stu in state.students:
        for col in state.columns:
            datum = state.data[stu][col]
            width[col] = max(width[col], len(datum_str(datum, 0, sep)))

    # now build list of items for output
    items = []
    for col, name, in enumerate(state.names):
        items.append(("%"+str(width[col])+"s"+sep)%(name.strip()))
    items.append("\n")
    # Data rows, one per student:
    for stu in state.students:
        for col in state.columns:
            datum = state.data[stu][col]
            items.append(datum_str(datum, width[col], sep))
        items.append("\n")
    return "".join(items)

def compute_scores(state):
    """
    Return new state with data converted to rank-based scores.
    """
    stu_per_comp = [0  for col in state.columns]
    weight_per_stu = [0 for stu in state.students]
    beats = [[0 for col in state.columns] for stu in state.students]

    # compare all pairs stu,stu2 of students
    # beats[stu][col] is number of other students in same column
    #     this student beats
    # where a student beats himself by one (+1)
    # and beats others with same score by one-half (0.5)
    for stu in state.students:
        for col in state.columns:
            if state.weights[col] > 0:
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
    rank_weight = policy.RANK_WEIGHT
    new_state = state.copy()
    for stu in state.students:
        for col in state.columns:
            if state.weights[col] > 0:
                if not ismissing(state.data[stu][col]):
                    rank_value =  beats[stu][col] / (float(stu_per_comp[col]) + 1.0)
                    grade_value = state.data[stu][col] / state.perfect_grades[col]
                    value = rank_weight*rank_value + (1-rank_weight)*grade_value
                else:
                    value = MISSING
            else:
                value = state.data[stu][col]
            new_state.data[stu][col] = value
    return new_state

def sort_state(state, key_name):
    """ Sort data into decreasing order by key with given name"""
    key_col = state.names.index(key_name)
    L = sorted([(state.data[stu][key_col], stu)
                for stu in state.students],
               reverse=True)
    stu_order = [stu for (ws, stu) in L]
    new_state = state.copy()
    new_data = [new_state.data[stu] for stu in stu_order]
    new_state.data = new_data
    return new_state

def add_column(state, new_name, new_perfect_grade, new_weight, values):
    """ Return state with new column added. """
    new_state = state.copy()
    new_state.names.append(new_name)
    new_state.perfect_grades.append(new_perfect_grade)
    new_state.weights.append(new_weight)
    new_state.n_col += 1
    new_state.columns = list(range(new_state.n_col))
    for stu in state.students:
        new_state.data[stu].append(values[stu])
    return new_state

def print_and_write_to_file(title, state, file_name):
    """
    Write data to terminal and to output file with given filename.
    Here data is grades or scores.
    """
    print("-"*80 + "\n" + title)
    print(build_output(state, " "), end=' ')
    print("-"*80)

    with open(file_name, "w") as file:
        file.write(build_output(state, ", "))
    print(file_name, "written.")
    print()

def main():
    """ Main routine. """
    print("--------------------------------------------")
    print("-- Student ranking program (rank.py)      --")
    print("-- Version 0.3 (5/13/17) Ronald L. Rivest --")
    print("--------------------------------------------")

    # PARSE ARGUMENTS
    parser = argparse.ArgumentParser(\
                description='Rank-order students based on performance.')
    parser.add_argument(\
        'input_filename',
        help='csv file with header row, perfect_grade row, weight row, '\
        'and then one grade row per student')
    parser.add_argument('--skiprows',
                        default=0,
                        help='number of rows to skip before header row')
    args = parser.parse_args()

    input_filename = args.input_filename
    skiprows = int(args.skiprows)
    maxgraderows = 10000

    # READ AND CLEAN UP DATA
    rows = read_csv(input_filename)
    state = parse_csv(rows, skiprows, maxgraderows)
    grade_state = convert_data(state)
    print_grade_components(grade_state)
    print(grade_state.n_stu, "students")

    print()
    print("The weight of rank-based scores is", policy.RANK_WEIGHT)
    print("The weight of grade-based scores is", 1.0-policy.RANK_WEIGHT)


    # COMPUTE SCALED SCORES AND WEIGHTED AVERAGE SCORES
    # scores has one row per student,
    # one column per original grades column
    score_state = compute_scores(grade_state)
    wtd_score = policy.compute_wtd_scores(score_state)

    sorted_grade_state = add_column(grade_state,
                                    "wtd_score", 0, 0, wtd_score)
    sorted_grade_state = sort_state(sorted_grade_state,
                                    "wtd_score")
    sorted_grade_state = add_column(sorted_grade_state,
                                    "rank", 0, 0, 
                                    list(range(1, score_state.n_stu+1)))
    sorted_score_state = add_column(score_state,
                                    "wtd_score", 0, 0, wtd_score)
    sorted_score_state = sort_state(sorted_score_state, "wtd_score")
    sorted_score_state = \
        add_column(sorted_score_state,
                   "rank", 0, 0, list(range(1, score_state.n_stu+1)))

    # OUTPUT RESULTS
    title = "LISTING OF ALL STUDENTS (BEST FIRST) WITH RAW GRADES:"
    print_and_write_to_file(title, sorted_grade_state,
                            input_filename+".1.grades.rank.csv")

    title = "LISTING OF ALL STUDENTS (BEST FIRST) WITH WEIGHTED SCALED SCORES:"
    print_and_write_to_file(title, sorted_score_state,
                            input_filename+".2.scores.rank.csv")

    if policy.DROP_POLICY != []:
        # ADJUST: DROP WORST HOMEWORK, ETC. ACCORDING TO POLICY
        adjusted_score_state = policy.drop(score_state.copy())

        # THEN RECOMPUTE WEIGHTED SCORES AND NEW RANKS
        print("Recomputing weighted scores and ranks...")
        wtd_score = policy.compute_wtd_scores(adjusted_score_state)
        adjusted_score_state = add_column(adjusted_score_state,
                                          "wtd_score", 0, 0, wtd_score)
        sorted_adjusted_score_state = sort_state(adjusted_score_state,
                                                 "wtd_score")
        sorted_adjusted_score_state = \
            add_column(sorted_adjusted_score_state,
                       "rank", 0, 0, 
                       list(range(1, adjusted_score_state.n_stu+1)))

        title = "LISTING OF ALL STUDENTS (BEST FIRST) "\
                "WITH SCALED AND DROPPED SCORES:"
        print_and_write_to_file(title, sorted_adjusted_score_state,
                                input_filename+".3.droppedscores.rank.csv")

main()


