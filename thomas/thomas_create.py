#!/usr/bin/env python

import os.path
import argparse
import subprocess
import validate
import thomas_show
import thomas_add

# This should take all the arguments necessary to run both thomas-add user 
# and createThomasuser in one. It gets the next available mmm username
# automatically if this is not a UCL user.

# If a UCL email is given, this should be an active UCL user and their
# existing username should have been supplied.
# custom Action class, must override __call__
class CheckUCL(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if ("ucl.ac.uk" in values and namespace.username == None):
            print ("This is a UCL email address - please provide the user's UCL username with --user USERNAME")
            exit(1)
        setattr(namespace, self.dest, values)
# end class CheckUCL

def getargs():
    parser = argparse.ArgumentParser(description="Create a new user account, either from an account request in the Thomas database or from scratch.")
    subparsers = parser.add_subparsers(dest="subcommand")

    # Create a user entirely manually and add them to the database
    userparser = subparsers.add_parser("user", help="Create a new active user account and add their info to the Thomas database. Non-UCL users will be given the next free mmm username automatically.")
    parser.add_argument("-u", "--user", dest="username", help="Existing UCL username")
    parser.add_argument("-e", "--email", dest="email", help="Institutional email address of user", required=True, action=CheckUCL)
    parser.add_argument("-n", "--name", dest="given_name", help="Given name of user", required=True)
    parser.add_argument("-s", "--surname", dest="surname", help="Surname of user")
    parser.add_argument("-k", "--key", dest='ssh_key', help="User's public ssh key (quotes necessary)", required=True)
    parser.add_argument("-p", "--project", dest="project_ID", help="Initial project the user belongs to", required=True)
    parser.add_argument("-c", "--contact", dest="poc_id", help="An existing Point of Contact ID", required=True)
    parser.add_argument("-b", "--cc", dest="cc_email", help="CC the welcome email to this address")
    parser.add_argument("--noemail", help="Create account, don't send welcome email", action='store_true')
    parser.add_argument("--debug", help="Show SQL query submitted without committing the change", action='store_true')
    parser.add_argument("--nosshverify", help="Do not verify SSH key (use with caution!)", action='store_true')
    
    # Used when request(s) exists in the thomas database and we get the input from there
    # Requires at least one id to be provided. request is a list.
    requestparser = subparsers.add_parser("request", nargs='+', type=int, help="The request id(s) to carry out, divided by spaces")

    # Show the usage if no arguments are supplied
    if len(argv) < 1:
        parser.print_usage()
        exit(1)

    # return the arguments
    # contains only the attributes for the main parser and the subparser that was used
    return parser.parse_args()
# end getargs

# Return the next available mmm username (without printing result).
# mmm usernames are in the form mmmxxxx, get the integers and increment
def nextmmm():
    latestmmm = thomas_show.main(['--getmmm'], False)
    mmm_int = int(latestmmm[-4:]) + 1
    # pad to four digits with leading zeroes, giving a string
    mmm_string = '{0:04}'.format(mmm_int)
    return 'mmm' + mmm_string

# Add new user to Thomas database. Do not send support email as we are acting on one!
def addtodb(args):
    user_args = ['user', '-u', args.username, '-n', args.given_name, '-e', args.email, '-k', args.ssh_key,
                 '-p', args.project_ID, '-c', args.poc_id, '--nosupportemail']
    # add surname if there is one
    if (args.surname != None):
        user_args.extend(['-s', args.surname])
    if (args.debug):
        user_args.append('--debug')
    thomas_add.main(user_args)

# Activate account on Thomas and add user's key
def createaccount(args):
    create_args = ['createThomasuser', '-u', args.username, '-e', args.email, '-k', args.ssh_key]
    if (args.cc_email != None):
        create_args.extend(['-c', args.cc_email])
    if (args.noemail):
        create_args.append('-n') 
    if (args.debug):
        return print(create_args)
    else:
        return subprocess.check_call(create_args)

def create_and_add_user(args):
# if nosshverify is not set, verify the ssh key
        if (args.nosshverify == False):
            validate.ssh_key(args.ssh_key)

        # if no username was specified, get the next available mmm username
        if (args.username == None):
            args.username = nextmmm()
    
        # First, add the information to the database, as it enforces unique usernames etc.
        addtodb(args)

        # Now create the account.
        createaccount(args)
# end createuser

def updaterequest(args, cursor):
    query = ("""UPDATE requests SET isdone='1', approver=%(approver)s
                WHERE id=%(id)s""")
    cursor.execute(query, args_dict)
    

def approverequest(args, args_dict):

    # connect to MySQL database with write access.
    # (.thomas.cnf has readonly connection details as the default option group)
    try:
        conn = mysql.connector.connect(option_files=os.path.expanduser('~/.thomas.cnf'), option_groups='thomas_update', database='thomas')
        cursor = conn.cursor()

        # get the arguments from the database
        # args.request is a list of ids     
        # make the format string for the number of ids we are checking
        format_strings = ','.join(['%s'] * len(args.request))
        query = ("""SELECT username, email, ssh_key, poc_cc_email, isdone, approver FROM requests 
                    WHERE id IN (%s)""" % format_strings)
        cursor.execute(query, tuple(args.request))
        results = cursor.fetchall()
        if (args.debug):
            thomas_show.tableprint(cursor, results)

        # check if this request still needs doing
        for (row in results):
            if (row.isdone == '0'):

                # set the variables
                args.username = row.username 
                args.email = row.email
                args.ssh_key = row.ssh_key
                args.cc_email = row.poc_cc_email
                args.id = row.id
                args.approver = os.environ['USER']
                # create the account
                createaccount(args)
                # update the request status
                updaterequest(args, cursor)
                
            else:
                print("Request id " + row.id + " was already approved by " + row.approver)

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
# end approverequest    


    
if __name__ == "__main__":

    # get all the parsed args
    try:
        args = getargs()
        # make a dictionary from args to make string substitutions doable by key name
        args_dict = vars(args)
    except ValueError as err:
        print(err)
        exit(1)

    # Either create a user from scratch or approve an existing request
    if (args.subcommand == "user"):
        create_and_add_user(args)
    elif (args.subcommand == "request"):
        approverequest(args, args_dict)
        


# end main
