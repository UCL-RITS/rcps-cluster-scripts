#!/usr/bin/env python3

import os.path
import sys
import configparser
import argparse
#import csv
import numpy
import pandas

def getargs(argv):
    parser = argparse.ArgumentParser(description="Show allocation usage in given period.")
    parser.add_argument("--input", help="Gold allocations from stdin, input formed from glsalloc --raw", action='store_true')
    parser.add_argument("-i", "--institute", dest="institute", help="Show Gold total usage for this institute")
    parser.add_argument("-d", "--date", dest="date", help="Filter by start date of allocation period, in format yyyy-mm-dd")
    parser.add_argument("--csv", dest="csvfile", help="Write out CSV to this file in this location")
    parser.add_argument("--verbose", help="", action='store_true')
    parser.add_argument("--debug", help="", action='store_true')

    # Show the usage if no arguments are supplied
    if len(argv) < 1:
        parser.print_usage()
        exit(1)

    # return the arguments
    # contains only the attributes for the main parser and the subparser that was used
    return parser.parse_args(argv)
# end getargs


# Put main in a function so it is importable.
def main(argv):

    try:
        args = getargs(argv)
        # make a dictionary from args to make string substitutions doable by key name
        #args_dict = vars(args)
    except ValueError as err:
        print(err)
        exit(1)

    # Update Gold allocations from pipe-separated stdin input
    # Id|Account|Projects|StartTime|EndTime|Amount|Deposited|Description

    if args.input:
        dataframe = pandas.read_csv(sys.stdin, sep='|')
        # filter by date
        if date is not None:
            dataframe = dataframe[dataframe.StartTime == date]

        # add an institute column. We only want the first item in the split
        dataframe['Institute'] = dataframe['Projects'].str.split('_', 1).str[0]

        # filter by institute
        if institute is not None:
            # select all lines where institute matches
            dataframe = dataframe[dataframe.Institute == institute]

        # filter out _allocation projects and everything else separately
        allocs = dataframe[dataframe.Projects.str.contains("_allocation")]
        projects = dataframe[~dataframe.Projects.str.contains("_allocation")]

        # We want this output:
        # StartTime  Institute  Deposited  Unallocated  Unused  % Unused
        projects = projects.rename(columns={'Amount':'Unused'})
        allocs = allocs.rename(columns={'Amount':'Unallocated'})
        # sum the unused time for each institute in this period
        unused = projects.groupby(['StartTime','Institute'])['Unused'].sum().reset_index()
        # merge the columns we want from allocs and unused
        result = allocs[['StartTime', 'EndTime', 'Institute', 'Deposited', 'Unallocated']].merge(unused, on=['StartTime', 'Institute'])
        result['Used'] = result['Deposited'] - result['Unallocated'] - result['Unused']

        # write out as csv, leave off the row indices
        if args.csv is not None:
           result.to_csv(args.csv, index=False)
        else:
            print(result)

    else:
        print("No input was specified.")

# end main

# When not imported, use the normal global arguments
if __name__ == "__main__":
    main(sys.argv[1:])

