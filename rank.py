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
    Return:
       list of column names, 
       list of column weights
           positive numeric     --> weight for weighting in grade
           non-positive or non-numeric --> not part of grade
       rows of student grades.

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
    return names, weights, grades

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

def convert_data(weights, grades):
    """
    convert all grade data to floats, 
    with MISSING for data that doesn't convert to a float.
    """
    n_rows = len(grades)
    n_cols = len(weights)
    for j in range(n_cols):
        w = convert_to_float_if_possible(weights[j], 0)
        if w>0:
            for i in range(n_rows):
                grades[i][j] = convert_to_float_if_possible(grades[i][j])

def print_grade_components(names, weights):
    print "Column names (with weights for those being included in grade):"
    n_cols = len(weights)
    for j in range(n_cols):
        print "  %10s"%names[j],
        if weights[j]>0:
            print "weight", "%g"%weights[j]
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

def build_output(names, weights, data, best_stu_order,sep):
    """
    Build and return string for later output to file (or equivalent I/O) "output".
    Give names, weights, and then the rows in data (one per student).
    The order of the rows is given by best_stu_order.
    Sep is what to put between data elements:
        either "," (for csv use) or " " (for screen).
    """
    n_cols = len(names)

    # first compute column widths for printing
    width = [0]*(n_cols+1)
    for col, name in enumerate(names):
        width[col] = max(width[col],len(str(name.strip())))
    for rank, stu in enumerate(best_stu_order):
        for col in range(n_cols):
            datum = data[stu][col]
            width[col] = max(width[col],len(datum_str(datum, 0, sep)))

    # now build list of items for output
    items = []
    for col, name, in enumerate(names):
        items.append(("%"+str(width[col])+"s"+sep)%(name.strip()))
    items.append("\n")
    # Data rows, one per student:
    for rank, stu in enumerate(best_stu_order):
        for col in range(n_cols):
            datum = data[stu][col]
            items.append(datum_str(datum, width[col], sep))
        items.append("\n")
    return "".join(items)

def compute_scores(names, weights, grades):
    """ 
    Return scores: array of student x column with student scores (derived from rank within column)
    """
    n_stu = len(grades)           
    n_cols = len(names)
    students = range(n_stu)
    stu_per_comp = [ 0  for col in range(n_cols) ]
    weight_per_stu = [ 0 for stu in students ]
    beats = [ [ 0 for col in range(n_cols) ] for stu in students ]

    # compare all pairs stu,stu2 of students
    # beats[stu][col] is number of other students in same column this student beats
    # where a student beats himself by one (+1)
    # and beats others with same score by one-half (0.5)
    for stu in students:
        for col in range(n_cols):
            if weights[col]>0:
                d1 = grades[stu][col]
                if not ismissing(d1):
                    stu_per_comp[col] += 1
                    weight_per_stu[stu] += weights[col]
                    for stu2 in students:
                        d2 = grades[stu2][col]
                        if not ismissing(d2):
                            if stu == stu2:
                                beats[stu][col] += 1.0
                            elif d2 == d1:
                                beats[stu][col] += 0.5
                            elif d1 > d2:
                                beats[stu][col] += 1.0
    return normalize_scores(weights, grades, beats, stu_per_comp)

def normalize_scores(weights, grades, beats, stu_per_comp):
    """
    Return normalized scores (in beats) to [0,1] by dividing by 
    one plus the number of students in the component component
    preserve missing or other data "as is"
    """
    n_cols = len(weights)
    n_stu = len(beats)
    students = range(n_stu)
    
    scores =  [ [ 0 for col in range(n_cols) ] for stu in students ]
    for stu in students:
        for col in range(n_cols):
            if weights[col]>0:
                if not ismissing(grades[stu][col]):
                    scores[stu][col] = beats[stu][col] / (float(stu_per_comp[col]) + 1.0)
                else:
                    scores[stu][col] = MISSING
            else:
                scores[stu][col] = grades[stu][col]
    return scores

def compute_ranks(names, weights, scores):
    """
    Compute weighted average score and new ranks.

    Return new student ordering (best to worst), weighted scores per student,
    ranks of students (1 is best).
    """
    columns = range(len(scores[0]))
    n_stu = len(scores)
    students = range(n_stu)

    # compute avg_score per student as weighted sum of component scores
    wtd_score = [0 for stu in students]
    for stu in students:
        total = 0.0
        total_weight = 0.0
        for col in columns:
            if weights[col]>0:
                d = scores[stu][col]
                if not ismissing(d):
                    total += weights[col] * d
                    total_weight += weights[col]
        wtd_score[stu] = total / total_weight

    L = sorted([ (wtd_score[stu], stu) for stu in students ], reverse=True)
    stu_order = [ stu for (ws, stu) in L ]
    wtd_score = [ ws for (ws, stu) in L ]
                
    ranks = range(1, n_stu+1)
    return stu_order, wtd_score, ranks

def augment(names, weights, grades, scores, stu_order, wtd_score):
    """
    Augment grades and scores to have two new columns
    """
    names = copy.deepcopy(names)
    weights = copy.deepcopy(weights)
    grades = copy.deepcopy(grades)
    scores = copy.deepcopy(scores)
    names.append("wtd_score")
    weights.append(0)
    names.append("rank")
    weights.append(0)
    for r, stu in enumerate(stu_order):
        grades[stu].append(wtd_score[r])
        grades[stu].append(r+1)
        scores[stu].append(wtd_score[r])
        scores[stu].append(r+1)
    return names, weights, grades, scores

def print_and_write_to_file(names, weights, data, stu_order, file_name):
    """ 
    Write data to terminal and to output file with given filename.
    Here data is grades or scores.
    """
    print build_output(names, weights, data, stu_order," "),
    print "-"*80

    with open(file_name,"w") as file:
        file.write(build_output(names, weights, data, stu_order,", "))
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
    names, weights, grades = parse_csv(rows, skiprows, maxgraderows)
    convert_data(weights, grades)
    print_grade_components(names, weights)
    print len(grades), "students"

    # COMPUTE SCALED SCORES
    # scores has one row per student, one column per original grades column
    scores = compute_scores(names, weights, grades)

    # COMPUTE WEIGHTED AVERAGE SCORES AND RANKS
    stu_order, wtd_score, ranks = compute_ranks(names, weights, scores)

    names2, weights2, grades2, scores2 = augment(names, weights, grades, scores, stu_order, wtd_score)

    # OUTPUT RESULTS
    print "-"*80 + "\nLISTING OF ALL STUDENTS (BEST FIRST) WITH RAW GRADES:"
    print_and_write_to_file(names2, weights2, grades2, stu_order, 
                            input_filename+".1.grades.rank.csv")

    print "-"*80 + "\nLISTING OF ALL STUDENTS (BEST FIRST) WITH SCALED SCORES:"
    print_and_write_to_file(names2, weights2, scores2, stu_order, 
                            input_filename+".2.scores.rank.csv")

    if policy.DROP_POLICY != []:
        # DROP WORST HOMEWORK, ETC. ACCORDING TO POLICY
        scores3 = copy.deepcopy(scores)
        scores3 = policy.drop(names, weights, scores3)

        # THEN RECOMPUTE WEIGHTED SCORES AND NEW RANKS
        print "Recomputing weighted scores and ranks..."
        stu_order, wtd_score, ranks = compute_ranks(names, weights, scores3)
        names3, weights3, grades3, scores3 = augment(names, weights, grades, scores3, stu_order, wtd_score)

        print "-"*80 + "\n LISTING OF ALL STUDENTS (BEST FIRST) WITH SCALED AND DROPPED SCORES:"
        print_and_write_to_file(names3, weights3, scores3, stu_order, 
                                input_filename+".3.droppedscores.rank.csv")
        
main()


