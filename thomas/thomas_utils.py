# Utility functions used in multiple places in the thomas tools.

import mysql.connector
from tabulate import tabulate
import thomas_queries

##########################
#                        #
# Get last/next username #
#                        #
##########################

# Given a username as a string, get the next one
# mmm usernames are in the form mmmxxxx
def nextmmm(latestmmm):
    mmm_int = int(latestmmm[-4:]) + 1
    # pad to four digits with leading zeroes, giving a string
    mmm_string = '{0:04}'.format(mmm_int)
    return 'mmm' + mmm_string

# Get the most recent mmm username used from the database
def lastmmm(cursor):
    cursor.execute(thomas_queries.lastmmm())
    lastresult = cursor.fetchall()
    # I am using a dictionary cursor, otherwise this would be a list of tuples.
    # This is a list of dictionaries with one element - returning the string is more useful
    return lastresult[0]['username']

# Get the next unused mmm username
def getunusedmmm(cursor):
    return nextmmm(lastmmm(cursor))

#################################
#                               #
# Print functions and debugging #
#                               #
#################################

# Write out results from cursor.fetchall() as a table with
# headers and separators. 
# Assumes a dictionary cursor: conn.cursor(dictionary=True)
def tableprint(results):
    print(tabulate(results, headers="keys", tablefmt="psql"))
    print("")

# Print out the cursor statement for debugging purposes
def debugcursor(cursor, debug):
    if (debug):
        print(cursor.statement)

######################
#                    #
# Database additions #
#                    #
######################

# Add a new user to the database.
def addusertodb(args, args_dict, cursor):
    cursor.execute(thomas_queries.adduser(args.surname), args_dict)
    debugcursor(cursor, args.debug)

# Add a new project-user relationship to the database
def addprojectuser(args, args_dict, cursor):
    cursor.execute(thomas_queries.addprojectuser(), args_dict)
    debugcursor(cursor, args.debug)


