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
    parser.add_argument("-d", "--date", dest="institute", help="Filter by start date of allocation period, in format yyyy-mm-dd")
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
    # parse our credentials
    #try:
    #    config = configparser.ConfigParser()
    #    config.read_file(open(os.path.expanduser('~/.thomas.cnf')))
    #except OSError as err:
    #    print(err)

    # Update Gold allocations from pipe-separated stdin input
    # Id|Account|Projects|StartTime|EndTime|Amount|Deposited|Description

    if args.input:
        #csv = csv.reader(sys.stdin, delimiter='|')
        # pandas?
        dataframe = pandas.read_csv(sys.stdin, sep='|')
        # filter by institute
        if institute is not None:
            # select all lines where institute matches
            dataframe = dataframe[dataframe.Projects == institute]
            # TODO: case?
        # filter by date
        if date is not None:
            dataframe = dataframe[dataframe.StartTime == date]

# end main

# When not imported, use the normal global arguments
if __name__ == "__main__":
    main(sys.argv[1:])

