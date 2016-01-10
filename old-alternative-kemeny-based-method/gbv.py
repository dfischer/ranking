# grading by voting (gbv.py)
# Ron Rivest
# 1/7/16

"""
This is a program to produce an overall student ranking, given
as input a spreadsheet given student scores on various grade
components, and given weights for those components.
The method is based on choosing a permutation that maximizes the 
Kemeny-Young score for that permutation
"""

""" (Distributed under MIT License) """

import argparse
import csv
import math
import random
import sys
import time

import kem                       # methods for minimizing Kemeny score

##############################################################################
## Beginning of "grading by voting" method
##############################################################################

def read_grades(input_filename, skiprows=0, maxrows=10000):
    """ 
    Read grades file at given input_filename.
    Return:
       list of column names, 
       list of column weights
           non-numeric --> not part of grade
           numeric     --> weight for weighting in grade
       rows of student data.

    The input file format is:
        'skiprows' rows to be skipped
        a header row giving column names
        a weight row given component weights for components to be included
          (a zero, non-numeric or missing weight means to ignore this column for grade)
        a number of rows of data, one per student
    At most the first 'maxrows' of student data will be read.

    BE CAREFUL: the values read from csv are all STRINGS, and must be 
    converted to numeric data types as appropriate.
    """
    print "Reading input file:", input_filename
    # rU is universal newline mode
    with open(input_filename, 'rU') as csvfile:   
        gradereader = csv.reader(csvfile)
        skipped_rows = []
        for _ in range(skiprows):
            skipped_rows.append(gradereader.next())
        name_row = gradereader.next()        
        name_row = [ name.strip() for name in name_row ]
        weight_row = gradereader.next()
        weight_row = [ convert_to_float_if_possible(w,0) for w in weight_row ]
        data_rows = []
        for row in gradereader:
            data_rows.append(row)
        data_rows = data_rows[:maxrows]
        return name_row, weight_row, data_rows

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

def convert_data(weight_row, data_rows):
    """
    convert all grade data to floats, 
    with MISSING for data that doesn't convert to a float.
    """
    n_rows = len(data_rows)
    n_cols = len(weight_row)
    for j in range(n_cols):
        w = convert_to_float_if_possible(weight_row[j], 0)
        if w>0:
            for i in range(n_rows):
                data_rows[i][j] = convert_to_float_if_possible(data_rows[i][j])

def print_grade_components(name_row, weight_row):
    print "Column names (with weights for those being included in grade):"
    n_cols = len(weight_row)
    for j in range(n_cols):
        print "  %10s"%name_row[j],
        w = convert_to_float_if_possible(weight_row[j],0)
        if w>0:
            print "weight", "%g"%w
        else:
            print "------"

def make_preference_matrix(weight_row, data_rows):
    """
    weight_row = list of weights for components (may be 0 or missing)
    data_rows = actual data matrix (list of rows)
    """
    n_rows = len(data_rows)
    n_stu = n_rows                    # number of rows = number of students
    n_cols = len(weight_row)

    data_cols = zip(*data_rows)      # transpose

    A = [ [ 0 for i2 in range(n_stu)] for i1 in range(n_stu) ]
    
    for col in range(n_cols):
        w = convert_to_float_if_possible(weight_row[col], 0)
        if w>0:
            scores = data_cols[col]
            for i1 in range(n_stu):
                if not ismissing(scores[i1]):
                    for i2 in range(n_stu):
                        if not ismissing(scores[i2]):
                            if scores[i1]>scores[i2]:
                                A[i1][i2] += w
    return A

def print_preference_matrix(A):
    n_stu = len(A)
    print "Printing preference matrix (%d students)"%n_stu
    if n_stu > 30:
        print "  ** preference matrix too big to print!"
        return
    print "Preference matrix:"
    for i1 in range(n_stu):
        print "%4d"%i,
        for i2 in range(n_stu):
            print "%4d"%A[i1][i2],
        print

def datum_str(datum, width, sep):
    """
    Return string rep of data item.
    """
    if isnonnumeric(datum):
        return ("%"+str(width)+"s"+sep)%datum
    else:
        if datum == int(datum):
            return ("%"+str(width)+"d"+sep)%datum
        else:
            return ("%"+str(width)+".3f"+sep)%datum

def print_output(output, name_row, weight_row, data_rows, best_stu_order,sep):
    """
    Print output to file (or equivalent I/O) "output".
    Print name_row, weight_row, and then the rows in data_rows (one per student).
    The order of the rows is given by best_stu_order.
    Sep is what to put between data elements, either "," (for csv use) or " " (for screen).
    """
    
    n_cols = len(name_row)

    # first compute column widths for printing
    width = [0]*(n_cols+1)
    for col, name in enumerate(name_row):
        width[col] = max(width[col],len(str(name.strip())))
    for rank, stu in enumerate(best_stu_order):
        for col in range(n_cols):
            datum = data_rows[stu][col]
            width[col] = max(width[col],len(datum_str(datum, 0, sep)))

    # now print 
    for col, name, in enumerate(name_row):
        print >>output, ("%"+str(width[col])+"s"+sep)%(name.strip()),
    print >>output
    # Data rows, one per student:
    for rank, stu in enumerate(best_stu_order):
        for col in range(n_cols):
            datum = data_rows[stu][col]
            print >>output, datum_str(datum, width[col], sep),
        print >>output

def LCS(X,Y):
    """ 
    Return length of longest common subsequence of X and Y.

    Used to measure how much has changed in student ordering when
    an optimization is done.

    Algorithm straight from CLRS (Chapter 13--Dynamic Programming)
    """
    m = len(X)
    n = len(Y)
    C = [[0 for j in range(n+1)] for i in range(m+1)]
    for i in range(1, m+1):
        for j in range(1, n+1):
            if X[i-1]==Y[j-1]:
                C[i][j] = C[i-1][j-1] + 1
            elif C[i-1][j] > C[i][j-1]:
                C[i][j] = C[i-1][j]
            else:
                C[i][j] = C[i][j-1]
    return C[m][n]

def compute_gaps(weight_row, data_rows, A, best_stu_order):
    # compute "gaps" for each student)
    # (This is basically how much Kemeny score would go down if you
    # swap that student with the next one in the listing.)
    n_stu = len(A)
    n_cols = len(weight_row)
    gaps = [0]*n_stu
    for rank, stu in enumerate(best_stu_order):
        if rank+1 == n_stu:     # since no following student
            break
        gap = 0
        for col in range(n_cols):
            w = convert_to_float_if_possible(weight_row[col],0)
            if w>0:
                d1 = data_rows[stu][col]
                d2 = data_rows[best_stu_order[rank+1]][col]
                if not ismissing(d1) and not ismissing(d2):
                    if d1 > d2:
                        gap += w
                    elif d1 < d2:
                        gap -= w
        gaps[rank] = gap
    return gaps

def add_column(name_row, weight_row, data_rows, new_col_name, new_weight, row_order, row_values):
    """ Add one new column to data. """
    name_row.append(new_col_name)
    weight_row.append(new_weight)
    for rank, stu in enumerate(row_order):
        data_rows[stu].append(row_values[rank])

def main():
    print "-- Grading By Voting (GBV) program.        --"
    print "-- Version 0.1 (12/31/15) Ronald L. Rivest --"

    # PARSE ARGUMENTS 
    parser = argparse.ArgumentParser(description=\
                'Rank-order students based on performance, using a voting-based approach.')
    parser.add_argument('input_filename',help=\
                'csv file with header row, weight row, and then one row per student')
    parser.add_argument('opt_minutes',default=5,help=\
                'number of minutes to spend optimizing student order')
    parser.add_argument('--skiprows',default=0,help=\
                'number of rows to skip before header row')
    args = parser.parse_args()

    input_filename = args.input_filename
    skiprows = int(args.skiprows)
    maxrows = 1000

    name_row, weight_row, data_rows = read_grades(input_filename, skiprows, maxrows)

    n_rows = len(data_rows)
    n_stu = n_rows
    n_cols = len(weight_row)

    convert_data(weight_row, data_rows)
    print_grade_components(name_row, weight_row)

    print n_stu, "students"

    A = make_preference_matrix(weight_row, data_rows)

    best_stu_order, best_rating = kem.dc(A)
    orig_order = best_stu_order
    opt_minutes = float(args.opt_minutes)
    print "Now %.0f minutes of optimizing (fine tuning)... "\
          "initial Kemeny score is %.0f"%(opt_minutes, best_rating)
    t0 = time.time()
    i = 0
    while (time.time()-t0)/60.0 < opt_minutes:
        i += 1
        new_order, new_rating = kem.split_merge(A, best_stu_order,10)
        if new_rating > best_rating:
            print "(%4d)   --> %.0f"%(i, new_rating), \
                "(%d new changes, %d changes total)" \
                %((len(new_order)-LCS(new_order, best_stu_order)), \
                  (len(new_order)-LCS(new_order, orig_order)))
            best_rating = new_rating
            best_stu_order = new_order
    print "Done."

    # print_preference_matrix(A)
    
    gaps = compute_gaps(weight_row, data_rows, A, best_stu_order)

    # add two new columns for GBV rank and gaps
    add_column(name_row, weight_row, data_rows, "GBVrank", 0, best_stu_order, range(n_stu))
    add_column(name_row, weight_row, data_rows, "gap", 0, best_stu_order, gaps)

    print "Kemeny score for best student order:", best_rating

    avg_order, avg_norm, avg_rank = borda(name_row, weight_row, data_rows)

    print "-"*80
    print "LISTING OF ALL STUDENTS (BEST FIRST):"
    output = sys.stdout
    print_output(output, name_row, weight_row, data_rows, best_stu_order," ")
    print "-"*80

    print "-"*80
    print "LISTING OF ALL STUDENTS (BEST FIRST):"
    output = sys.stdout
    print_output(output, name_row, weight_row, data_rows, avg_order," ")
    print "-"*80

    output_filename = input_filename+".gbv.csv"
    with open(output_filename,"w") as file:
        print_output(file, name_row, weight_row, data_rows, best_stu_order,", ")


def borda(name_row, weight_row, data_rows):
    """ 
    Return best student ordering and array of average ranks. 
    """

    n_rows = len(data_rows)
    n_stu = len(data_rows)           
    n_cols = len(name_row)

    students = range(n_stu)
    
    stu_per_comp = [ 0  for col in range(n_cols) ]
    weight_per_stu = [ 0 for stu in students ]
    beats = [ [ 0 for col in range(n_cols) ] for stu in students ]
    rank =  [ [ 0 for col in range(n_cols) ] for stu in students ]

    # compare all pairs stu,stu2 of students
    for stu in students:
        for col in range(n_cols):
            w = convert_to_float_if_possible(weight_row[col],0)
            if w>0:
                d1 = data_rows[stu][col]
                if not ismissing(d1):
                    stu_per_comp[col] += 1
                    weight_per_stu[stu] += weight_row[col]
                    beats[stu][col] = 0
                    for stu2 in students:
                        d2 = data_rows[stu2][col]
                        if not ismissing(d2):
                            if stu == stu2:
                                beats[stu][col] += 1.0
                            elif d2 == d1:
                                beats[stu][col] += 0.5
                            elif d1 > d2:
                                beats[stu][col] += 1.0

    # normalize ranks to [0,1] by dividing by number of students per component, plus one
    for stu in students:
        for col in range(n_cols):
            w = convert_to_float_if_possible(weight_row[col],0)
            if w>0:
                rank[stu][col] = beats[stu][col] / (float(stu_per_comp[col]) + 1.0)
    
    # print "beats:"
    # for stu in students:
    #     for col in range(n_cols):
    #         print "%0.3f "%beats[stu][col],
    #     print

    # print "rank:"
    # for stu in students:
    #     for col in range(n_cols):
    #         print "%0.3f "%rank[stu][col],
    #     print

    
    # compute avg_rank per student as weighted sum of component ranks
    avg_norm = [0 for stu in students]
    for stu in students:
        total = 0.0
        total_weight = 0.0
        for col in range(n_cols):
            w = convert_to_float_if_possible(weight_row[col],0)
            if w>0:
                d = data_rows[stu][col]
                if not ismissing(d):
                    total += weight_row[col] * rank[stu][col]
                    total_weight += weight_row[col]
        # subtract from 1.0 so best ranks are near 0, not near 1 
        avg_norm[stu] = 1.0 - total / total_weight

    L = sorted([ (avg_norm[stu], stu) for stu in students ])
    stu_order = [ s for (an, s) in L ]
    avg_norm = [ an for (an, s) in L ]
                
    add_column(name_row, weight_row, data_rows, "avg_norm", 0, stu_order, avg_norm)
    add_column(name_row, weight_row, data_rows, "avg_rank", 0, stu_order, range(n_stu))

    return stu_order, avg_norm, range(n_stu)

main()


