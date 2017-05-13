# routine to make test data for GBV (Grading By Voting) program
# Ronald L. Rivest
# 5/13/17
# python2

"""
Minor note: having "ID" as the contents of row 0, col 0 
causes Excel to mis-interpret the type of the file produced
as SYLK rather than CSV.  So, we use "STU_ID" rather than "ID"
in the header row.
"""

import argparse
import random

MISSING = " --"

def rand_score(mu, max_score, frac_missing):
    """ Return a string for score, or MISSING """
    if random.random() <= frac_missing:
        return MISSING
    mean = mu*max_score
    stdev = 0.15 * max_score
    x = int(random.normalvariate(mean,stdev))
    x = min(max_score,max(0,x))
    return "%3d"%int(x)

def main():
    parser = argparse.ArgumentParser(description='Produce sample data set for use by GBV, a voting-based program to order students based on their performance on homeworks, quizzes, and a final exam.')
    parser.add_argument('n_students',help='number of students records to produce')
    parser.add_argument('--seed',help='random number seed',default=1)
    args = parser.parse_args()
    n_IDs = 1
    n_homeworks = 4
    n_quizzes = 2
    n_finals = 1
    n_students = int(args.n_students)
    max_homework_score = 10
    max_quiz_score = 100
    max_final_score = 200
    frac_homework_missing = 0.10
    frac_quizzes_missing = 0.10
    frac_final_missing = 0.0
    
    random.seed(int(args.seed))

    DQ = '\"'
    DQC = DQ+","
    C = ","

    # create name_row
    name_row = []
    if n_IDs == 1:
        name_row.append("STU_ID")
    else:
        for i in range(n_IDs):
            name_row.append("STU_ID"+str(i+1))
    for i in range(n_homeworks):
        name_row.append("H"+str(i+1))
    for i in range(n_quizzes):
        name_row.append("Q"+str(i+1))
    name_row.append("Final")

    # create perfect_grades row
    perfect_grades_row = [0]*n_IDs + [5]*n_homeworks + [100]*n_quizzes + [200]*n_finals

    # create weight row
    weight_row = [0]*n_IDs + [5]*n_homeworks + [20]*n_quizzes + [30]*n_finals

    # create data rows
    data_rows = []
    idmin, idmax = 60, 100
    while (idmax-idmin) < n_students*1.5:
        idmin, idmax = idmin*10, idmax*10
    used = [ False for i in range(idmax) ]
    for i in range(n_students):
        # ID (random, but unique for each student)
        q = random.randint(idmin,idmax-1)
        while used[q]:
            q = random.randint(idmin,idmax-1)
        used[q] = True
        mu = float(q) / float(idmax)
        row = []
        ID = "X"+str(q)
        row.append(ID)
        for j in range(n_homeworks):
            row.append(rand_score(mu, max_homework_score, frac_homework_missing))
        for j in range(n_quizzes):
            row.append(rand_score(mu, max_quiz_score, frac_quizzes_missing))
        for j in range(n_finals):
            row.append(rand_score(mu, max_final_score, frac_final_missing))
        data_rows.append(row)

    assert len(name_row) == len(perfect_grades_row)
    assert len(name_row) == len(weight_row)
    assert len(weight_row) == len(data_rows[0])

    all_data = [name_row] + [perfect_grades_row] + [weight_row] + data_rows                                     

    column_widths = [0]*len(name_row)

    for row in all_data:
        for i, datum in enumerate(row):
            column_widths[i] = max(column_widths[i], len(str(datum)))

    for row in all_data:
        for i, datum in enumerate(row):
            print ("%" + str(column_widths[i]) + "s")%datum,
            if i< len(row)-1:
                print ",",
        print

main()
