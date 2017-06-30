#!/usr/bin/env python

import os.path
import argparse
import subprocess
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
        if ("ucl.ac.uk" in values):
            print ("This is a UCL email address - please provide the user's UCL username with --user USERNAME")
            exit(1)
        setattr(namespace, self.dest, values)
# end class CheckUCL

def getargs():
    parser = argparse.ArgumentParser(description="Create a new active user account and add their info to the Thomas database. Non-UCL users will be given the next free mmm username automatically.")

    parser.add_argument("-u", "--user", dest="username", help="Existing UCL username")
    parser.add_argument("-e", "--email", dest="email", help="Institutional email address of user", required=True, action=CheckUCL)
    parser.add_argument("-n", "--name", dest="given_name", help="Given name of user", required=True)
    parser.add_argument("-s", "--surname", dest="surname", help="Surname of user")
    parser.add_argument("-k", "--key", dest='"ssh_key"', help="User's public ssh key (quotes necessary)", required=True)
    parser.add_argument("-p", "--project", dest="project_ID", help="Initial project the user belongs to", required=True)
    parser.add_argument("-c", "--contact", dest="poc_id", help="An existing Point of Contact ID", required=True)
    parser.add_argument("-b", "--cc", dest="cc_email", help="CC the welcome email to this address")
    parser.add_argument("--noemail", help="Create account, don't send welcome email", action='store_true')
    parser.add_argument("--debug", help="Show SQL query submitted without committing the change", action='store_true')

    # return the arguments
    # contains only the attributes for the main parser and the subparser that was used
    return parser.parse_args()
# end getargs

# Return the next available mmm username (without printing result).
# mmm usernames are in the form mmmxxxx, get the integers and increment
def nextmmm():
    latestmmm = thomas_show.main(['--getmmm'], False)
    #print(latestmmm)
    mmm_int = int(latestmmm[-4:]) + 1
    return 'mmm' + str(mmm_int)

def addtodb(args):
    user_args = ['user', '-u', args.username, '-n', args.given_name, '-e', args.email, '-k', args.ssh_key,
                 '-p', args.project_ID, '-c', args.poc_id]
    # add surname if there is one
    if (args.surname != None):
        user_args.append(['-s', args.surname])
    if (args.debug):
        user_args.append(['--debug'])
    thomas_add.main(user_args)

def createaccount(args):
    create_args = ['createThomasuser', '-u', args.username, '-e', args.email, '-k', args.ssh_key]
    if (args.cc_email != None):
        create_args.append(['-c', args.cc_email])
    if (args.noemail):
        create_args.append(['-n']) 
    return subprocess.check_output(create_args)

if __name__ == "__main__":

    # get all the parsed args
    try:
        args = getargs()
        # make a dictionary from args to make string substitutions doable by key name
        args_dict = vars(args)
    except ValueError as err:
        print(err)
        exit(1)
    #print(args)

    # if no username was specified, get the next available mmm username
    if (args.user == None):
        args.user = nextmmm()
    
    # First, add the information to the database, as it enforces unique usernames etc.
    addtodb(args)

    # Now create the account.
    createaccount(args)

# end main
