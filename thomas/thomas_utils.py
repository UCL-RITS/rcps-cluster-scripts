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

##############
#            #
# User input #
#            #
##############

# Interactive confirmation - asks for yes/no input.
# default_ans can be True, False, None
def are_you_sure(question, default_ans=False):
    yes_list = ["yes", "y"]
    no_list = ["no", "n"]

    # Input hint shows whether there is a default
    defaults = { None:"[y/n]", True:"[Y]", False:"[N]" }
    # assemble prompt string
    prompt = "%s %s: " %(question, defaults[default_ans])

    # get answer in lower case. If no default, loops until valid input received.
    while True:
        try:
            confirm = input(prompt).lower()
        except KeyboardInterrupt:
            return False
        if not confirm and default_ans is not None:
            return default
        if confirm in yes_list:
            return True
        if confirm in no_list:
            return False

        # invalid input received
        reprompt = "Please respond with y or n"
        print(reprompt)
# end of are_you_sure

#########################################
#                                       #
# Make sure you're on the right cluster #
#                                       #
#########################################

def checkprojectoncluster(project, nodename):
    # If this is a Faraday project and this isn't Michael, ask for confirmation.
    if (project.startswith("Faraday")):
        if not ("michael" in nodename):
            answer = are_you_sure("You are trying to create project "+project+" on "+nodename+" which is not Michael.\n Do you want to continue?", False)
            # they said no, exit
            if not answer:
                exit(1)
    # If this isn't a Faraday project and this is Michael, ask for confirmation.
    elif ("michael" in nodename):
        answer = are_you_sure("You are trying to create project "+project+" which does not begin with Faraday on "+nodename+".\n Do you want to continue?", False)
        # they said no, exit
        if not answer:
            exit(1)

# end checkprojectoncluster

def getcluster(nodename):
    if "thomas" in nodename:
        return "thomas"
    elif "michael" in nodename:
        return "michael"
    else:
        print("Cluster not recognised, nodename is "+nodename)
        exit(1)
# end getcluster

