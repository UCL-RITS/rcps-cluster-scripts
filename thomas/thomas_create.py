#!/usr/bin/env python

import os.path
import sys
import argparse
import subprocess
import validate
import mysql.connector
from mysql.connector import errorcode
import socket
import thomas_queries
import thomas_utils

# This should take all the arguments necessary to run both thomas-add user 
# and createThomasuser in one. It gets the next available mmm username
# automatically if this is not a UCL user.
# It also acts on account requests existing in the Thomas database.

def getargs():
    parser = argparse.ArgumentParser(description="Create a new user account, either from an account request in the Thomas database or from scratch.")
    subparsers = parser.add_subparsers(dest="subcommand")

    # Create a user entirely manually and add them to the database
    # Debug etc are duplicated for each subparser as otherwise that flag
    # can't be given after the arguments for user
    userparser = subparsers.add_parser("user", help="Create a new active user account and add their info to the Thomas database. Non-UCL users will be given the next free mmm username automatically.")
    userparser.add_argument("-u", "--user", dest="username", help="Existing UCL username")
    userparser.add_argument("-e", "--email", dest="email", help="Institutional email address of user", required=True)
    userparser.add_argument("-n", "--name", dest="given_name", help="Given name of user", required=True)
    userparser.add_argument("-s", "--surname", dest="surname", help="Surname of user")
    userparser.add_argument("-k", "--key", dest='ssh_key', help="User's public ssh key (quotes necessary)", required=True)
    userparser.add_argument("-p", "--project", dest="project_ID", help="Initial project the user belongs to", required=True)
    userparser.add_argument("-c", "--contact", dest="poc_id", help="An existing Point of Contact ID", required=True)
    userparser.add_argument("-b", "--cc", dest="cc_email", help="CC the welcome email to this address")
    userparser.add_argument("--noemail", help="Create account, don't send welcome email", action='store_true')
    userparser.add_argument("--debug", help="Show SQL query submitted without committing the change", action='store_true')
    userparser.add_argument("--nosshverify", help="Do not verify SSH key (use with caution!)", action='store_true')
    
    # Used when request(s) exists in the thomas database and we get the input from there
    # Requires at least one id to be provided. request is a list.
    requestparser = subparsers.add_parser("request")
    requestparser.add_argument("request", nargs='+', type=int, help="The request id(s) to carry out, divided by spaces")
    requestparser.add_argument("--noemail", help="Create account, don't send welcome email", action='store_true')
    requestparser.add_argument("--debug", help="Show SQL query submitted without committing the change", action='store_true')
    requestparser.add_argument("--nosshverify", help="Do not verify SSH key (use with caution!)", action='store_true')

    # Show the usage if no arguments are supplied
    if len(sys.argv[1:]) < 1:
        parser.print_usage()
        exit(1)

    # return the arguments
    # contains only the attributes for the main parser and the subparser that was used
    return parser.parse_args()
# end getargs

# Activate account on cluster and add user's key
def createaccount(args, nodename):
    if ("thomas" in nodename):
        create_args = ['createThomasuser', '-u', args.username, '-e', args.email, '-k', args.ssh_key]
    elif ("michael" in nodename):
        create_args = ['createMichaeluser', '-u', args.username, '-e', args.email, '-k', args.ssh_key]
    else:
        print("You do not appear to be on a supported cluster: nodename is "+nodename)
        exit(1)

    if (args.cc_email != None):
        create_args.extend(['-c', args.cc_email])
    if (args.noemail):
        create_args.append('-n') 
    if (args.debug):
        print("Arguments that would be used:")
        return print(create_args)
    else:
        return subprocess.check_call(create_args)

def create_and_add_user(args, args_dict, cursor, nodename):

        # check the cluster matches the project
        thomas_utils.checkprojectoncluster(args.project_ID, nodename)
        # if nosshverify is not set, verify the ssh key
        if (args.nosshverify == False):
            validate.ssh_key(args.ssh_key)

        # check for duplicates and ask

        # if no username was specified, get the next available mmm username
        if (args.username == None):
            args.username = thomas_utils.getunusedmmm(cursor)
    
        # First add the information to the database, as it enforces unique usernames etc.
        thomas_utils.addusertodb(args, args_dict, cursor)
        thomas_utils.addprojectuser(args, args_dict, cursor)

        # Now create the account.
        createaccount(args, nodename)
# end createuser

def updaterequest(args, cursor):
    #query = ("""UPDATE requests SET isdone='1', approver=%s 
    #            WHERE id=%s""")
    cursor.execute(thomas_queries.updaterequest(), (args.approver, args.id))
    thomas_utils.debugcursor(cursor, args.debug)

def updateuserstatus(args, cursor):
    cursor.execute(thomas_queries.activateuser(), (args.username))
    thomas_utils.debugcursor(cursor, args.debug)

def updateprojectuserstatus(args, cursor):
    cursor.execute(thomas_queries.activatependingprojectuser(), (args.username))
    thomas_utils.debugcursor(cursor, args.debug)

def approverequest(args, args_dict, cursor, nodename):

        # args.request is a list of ids - we use the length of it to add enough
        # parameter placeholders to the querystring
        cursor.execute(thomas_queries.getrequestbyid(len(args.request)), tuple(args.request))
        results = cursor.fetchall()
        if (args.debug):
            print("Requests found:")
            thomas_utils.tableprint(results)
        # carry out the request unless it is already done
        for row in results:
            if (row['isdone'] == 0):
                # set the variables
                args.username = row['username'] 
                args.email = row['email']
                args.ssh_key = row['ssh_key']
                args.cc_email = row['poc_cc_email']
                args.id = row['id']
                args.approver = os.environ['USER']
                args.cluster = row['cluster']
                # check the cluster matches where we are running from
                if (args.cluster in nodename):
                    # create the account
                    createaccount(args, nodename)
                    # update the request status
                    updaterequest(args, cursor)
                    # update the user and projectuser status from pending to active
                    updateuserstatus(args, cursor)
                    updateprojectuserstatus(args, cursor)               
                else:
                    print("Request id " +str(row['id'])+ "was for "+args.cluster+" and this is "+nodename)
            else:
                print("Request id " + str(row['id']) + " was already approved by " + row['approver'])

# end approverequest    

if __name__ == "__main__":

    # check we are on Thomas or Michael before continuing.
    # Later we also need to check if we are on the correct cluster for this project.
    nodename = socket.getfqdn()
    # if fqdn does not contain a suitable hostname prompt whether you really want to do this
    # (in case you *are* somewhere on those clusters and fqdn is not useful)
    if not ("thomas" in nodename or "michael" in nodename):
        answer = thomas_utils.are_you_sure("Current hostname does not appear to be on Thomas or Michael ("+nodename+")\n Do you want to continue?", False)    
        # they said no, exit
        if not answer:
            exit(1)

    # get all the parsed args
    try:
        args = getargs()
        # make a dictionary from args to make string substitutions doable by key name
        args_dict = vars(args)
    except ValueError as err:
        print(err)
        exit(1)

    # connect to MySQL database with write access.
    # (.thomas.cnf has readonly connection details as the default option group)
    try:
        conn = mysql.connector.connect(option_files=os.path.expanduser('~/.thomas.cnf'), option_groups='thomas_update', database='thomas')
        cursor = conn.cursor(dictionary=True)

        # Either create a user from scratch or approve an existing request
        if (args.subcommand == "user"):
            # UCL user validation - if this is a UCL email, make sure username was given 
            # and that it wasn't an mmm one.
            validate.ucl_user(args.email, args.username)
            create_and_add_user(args, args_dict, cursor, nodename)
        elif (args.subcommand == "request"):
            approverequest(args, args_dict, cursor, nodename)
        
        # commit the change to the database unless we are debugging
        if (not args.debug):
            conn.commit()

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Access denied: Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        cursor.close()
        conn.close()

# end main
