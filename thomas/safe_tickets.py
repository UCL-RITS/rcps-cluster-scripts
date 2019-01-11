#!/usr/bin/env python3

import os.path
import sys
import configparser
import argparse
import subprocess
import validate
import mysql.connector
from mysql.connector import errorcode
from tabulate import tabulate
import json
import requests
import safe_json_decoder as decoder
import thomas_queries
import thomas_utils
import thomas_create

def getargs(argv):
    parser = argparse.ArgumentParser(description="Show or update and close tickets from SAFE. Use [positional argument -h] for more help.")
    parser.add_argument("-s", "--show", dest="show", help="Show all current open tickets", action='store_true')
    parser.add_argument("-f", "--file", dest="jsonfile", default=None, help="Parse json tickets from a file")
    parser.add_argument("-r", "--refresh", dest="refresh", help="Refresh open tickets in DB", action='store_true')
    parser.add_argument("-c", "--close", dest="close", default=None, help="Carry out and close this ticket ID")
    parser.add_argument("--reject", dest="reject", default=None, help="Reject this ticket ID")
    parser.add_argument("--debug", help="Show what would be submitted without committing the change", action='store_true')

    # Show the usage if no arguments are supplied
    if len(argv) < 1:
        parser.print_usage()
        exit(1)

    # return the arguments
    # contains only the attributes for the main parser and the subparser that was used
    return parser.parse_args(argv)
# end getargs

def parsejsonfile(filename):
    f = open(filename, 'r')
    jdata = f.read()
    ticketlist = decoder.JSONtoTickets(jdata)
    f.close()
    for t in ticketlist:
        print(str(t.Ticket))
    print("Number of tickets included: " + str(len(ticketlist)))

# Connect to SAFE, get open tickets as JSON
def getopentickets(config):
    request = requests.get(config['safe']['host'] + "?mode=json", auth = (config['safe']['user'], config['safe']['password']))
    if request.status_code == 200:
        try:
            data = request.json()
            return data
        except json.decoder.JSONDecodeError as err:
            print("Received invalid json, contents: " + str(request.content))
            exit(1)
    else:
        print("Request not successful, code " + str(request.status_code))

# end getopentickets

def gettickets(config):
        # get SAFE tickets
        jsontickets = getopentickets(config)
        # parse SAFE tickets
        ticketlist = decoder.JSONDataToTickets(jsontickets)
        return ticketlist
# end gettickets

# Update and complete a budget (project) ticket
def updatebudget(ticket_id, projectname):
    parameters = {'qtid':ticket_id, 'new_username':projectname, 'mode':'completed'}
    return parameters

def updateaddtobudget(ticket_id):
    parameters = {'qtid':ticket_id, 'mode':'completed'}
    return parameters

# Update and complete a New User ticket
def updatenewuser(ticket_id, username):
    parameters = {'qtid':ticket_id, 'new_username':username, 'mode':'completed'}
    return parameters

# Reject the ticket because it would cause an error
def rejecterror(ticket_id):
    parameters = {'qtid':ticket_id, 'mode':'error'}
    return parameters

# Reject the ticket for any other reason
def rejectother(ticket_id):
    parameters = {'qtid':ticket_id, 'mode':'refused'}
    return parameters

# Update and close a ticket.
# parameters is a dictionary of values: {'qtid':id,'new_username':'Test', 'mode':'completed'}
def updateticket(config, parameters):
    request = requests.post(config['safe']['host'], auth = (config['safe']['user'], config['safe']['password']), params = parameters)
    if "<title>SysAdminServlet Success</title>" in request.text:
        print("Ticket " + parameters['qtid'] + " closed.")
# end updateticket


# Deal with a New User ticket
def newuser(cursor, config, ticketid):
    # get the ticket (the ID is unique so there is only one)
    cursor.execute(thomas_queries.getsafeticket(), {'id':ticketid})
    result = cursor.fetchall()
    # this dict will be needed when we create the user
    user_dict = {'username': result[0]['username'], 
                 'givenname': result[0]['firstname'],
                 'email': result[0]['email'],
                 'ssh_key': result[0]['publickey'],
                 'status': "active"}
    # check that we don't already have a username for them
    if "to_be_allocated_" in user_dict['username']:
        # check if they are a UCL user: UCL email
        if "ucl.ac.uk" in user_dict['email']:
            # UCL: get username from AD
            user_dict['username'] = thomas_utils.AD_username_from_email(config, user_dict['email'])
            print("UCL username found from AD: " + user_dict['username'])
        else:
            # not UCL, get next mmm username
            user_dict['username'] = thomas_utils.getunusedmmm(cursor)
            print("Not UCL email, username is " + user_dict['username'])
    # we have a non-placeholder username
    else:
        print("Using ticket-provided username: " + user_dict['username'])
    # Add new user to database: need the user_dict dictionary we created.
    # Surname may be empty.
    args.surname = result[0]['lastname']
    thomas_utils.addusertodb(args, user_dict, cursor)
    # create this account, checking we are on that machine
    cluster = thomas_utils.getnodename()
    if result[0]['machine'].casefold() in cluster:
        # make sure the point of contact gets copied in on account creation
        args.cc_email = result[0]['poc_email']
        thomas_create.createaccount(args, cluster)
    else:
        print("SAFE ticket was for " + result[0]['machine'].casefold() + "and you are on " + cluster + ", exiting.")
        exit(1)    
    
    # update SAFE and close the ticket
    updateticket(config, updatenewuser(ticketid, user_dict['username']))
# end newuser


# Deal with a New Budget ticket
def newbudget(cursor, config, ticketid):
    # get the ticket (the ID is unique so there is only one)
    cursor.execute(thomas_queries.getsafeticket(), {'id':ticketid})
    result = cursor.fetchall()

    # this dict will be needed when we create the budget
    budget_dict = {'project_ID': result[0]['project'],
                   'inst_ID': ''}

    # need to work out what institute it is for
    # use the first part of the project_ID up to any underscore as institute
    budget_dict['inst_ID'] = budget_dict['project_ID'].partition("_")[0] 

    # add new project to database
    thomas_utils.addproject(args, budget_dict, cursor)

    # update SAFE and close the ticket
    updateticket(config, updatebudget(ticketid, projectname))
# end newbudget


# Deal with an Add to budget ticket
def addtobudget(cursor, config, ticketid):
    # get the ticket (the ID is unique so there is only one)
    cursor.execute(thomas_queries.getsafeticket(), {'id':ticketid})
    result = cursor.fetchall()

    # this dict will be needed when we create the projectuser
    projectuser_dict = {'username': result[0]['username'],
                        'project_ID': result[0]['project'],
                        'poc_id': '',
                        'poc_firstname': result[0]['poc_firstname'],
                        'poc_lastname': result[0]['poc_lastname'], 
                        'poc_email': result[0]['poc_email'],
                        'status': 'active'}
    # budget exists: get the point of contact
    projectuser_dict['poc_id'] = thomas_utils.findpocID(cursor, projectuser_dict)

    thomas_utils.addprojectuser(args, projectuser_dict, cursor)

    # update SAFE and close the ticket
    updateticket(config, updateaddtobudget(ticketid))
# end addtobudget


# Match a New User ticket with an Add to budget ticket for the same user
def matchbudgetticket(cursor, ticketid):
    # get the username from the New User ticket
    cursor.execute(thomas_queries.getsafeticket(), {'id':ticketid})
    result = cursor.fetchall()
    user = result[0]['id']

    # get the matching add to budget tickets
    cursor.execute(thomas_queries.getusersbudgettickets(), {'account_name':user})
    result = cursor.fetchall()
    rowcount = cursor.rowcount

    # There were no matches! We did that ticket already (or we need to refresh).
    if rowcount == 0:
        print("No pending Add to budget tickets for " + user)
        print("You may wish to use --refresh to refresh tickets.")
        return None

    # May be multiple matches - we just want the first one as they can be done in any order.
    # Return ticket id so we know which one we are completing.         
    return {'project': result[0]['project'], 'ticket_ID': result[0]['id']}
# end matchbudgetticket


# Turn a list of tickets into a list of dicts for use in SQL queries
def ticketstodicts(ticketlist):
    ticket_dicts = []
    for t in ticketlist:
        t_dict = {
                       "id": t.Ticket.Id,
                       "type": t.Ticket.Type,
                       "status": t.Ticket.Status,
                       "account_name": t.Ticket.Account.Name,
                       "machine": t.Ticket.Machine,
                       "project": t.Ticket.ProjectGroup.Code,
                       "firstname": t.Ticket.Account.Person.FirstName,
                       "lastname": t.Ticket.Account.Person.LastName,
                       "email": t.Ticket.Account.Person.Email,
                       "publickey": t.Ticket.Account.Person.NormalisedPublicKey,
                       "poc_firstname": t.Ticket.Approver.FirstName,
                       "poc_lastname": t.Ticket.Approver.LastName,
                       "poc_email": t.Ticket.Approver.Email,
                       "startdate": t.Ticket.StartDate,
                       "enddate": t.Ticket.EndDate
                 }
        ticket_dicts.append(t_dict)
    return ticket_dicts


# Put main in a function so it is importable.
def main(argv):

    try:
        args = getargs(argv)
        # make a dictionary from args to make string substitutions doable by key name
        args_dict = vars(args)
    except ValueError as err:
        print(err)
        exit(1)
    print(args)
    try:
        config = configparser.ConfigParser()
        config.read_file(open(os.path.expanduser('~/.thomas.cnf')))
    #except FileNotFoundError as err:
    except OSError as err:
        print(err)

    # Read tickets from a file
    if args.jsonfile is not None:
        parsejsonfile(args.jsonfile)

    # Show tickets live from SAFE
    if args.show:
        # get SAFE tickets
        ticketlist = gettickets(config)

        # print SAFE tickets
        for t in ticketlist:
            #print(str(t.Ticket))
            values = [t.Ticket.Id, t.Ticket.Type, t.Ticket.Status, t.Ticket.Account.Name, t.Ticket.Machine, t.Ticket.ProjectGroup.Code, t.Ticket.Account.Person.FirstName, t.Ticket.Account.Person.LastName, t.Ticket.Account.Person.Email, t.Ticket.Account.Person.NormalisedPublicKey, t.Ticket.Approver.FirstName, t.Ticket.Approver.LastName, t.Ticket.Approver.Email,  t.Ticket.StartDate, t.Ticket.EndDate]
            print(values)
        print("Number of pending tickets: " + str(len(ticketlist)))

    # these options require a database connection
    if args.refresh or args.close is not None or args.reject is not None:
        try:
            conn = mysql.connector.connect(option_files=os.path.expanduser('~/.thomas.cnf'), option_groups='thomas_update', database='thomas')
            cursor = conn.cursor()

            # Refresh the database tickets
            if args.refresh:
                # get SAFE tickets as list of dicts
                ticketdicts = ticketstodicts(gettickets(config))
                # refresh tickets in database
                for t in ticketdicts:
                    cursor.execute(thomas_queries.refreshsafetickets(), t)
                    thomas_utils.debugcursor(cursor, args.debug)
                # show database tickets (not inc ssh key)
                print("Refreshed tickets:")
                cursor.execute(thomas_queries.showpendingtickets())
                thomas_utils.tableprint(cursor.fetchall())
    
            # Update and close SAFE tickets
            if args.close is not None:
                # for readability below
                ticket = args.close
                # get the type of ticket - ticket id is unique so there is only one
                # (Either make a temporary dict or pass in (ticket,) with the comma which is ugly).
                cursor.execute(thomas_queries.safetickettype(), {'id':ticket})
                result = cursor.fetchall()
                # make sure we got a result, or exit
                if cursor.rowcount < 1:
                    print("No tickets with id " + ticket + " found, exiting.")
                    exit(1)

                tickettype = result[0][0]
                # store all the ticket info

                # new user
                if tickettype == "New User":
                    newuser(cursor, config, ticket)
                    # Each new user ticket should have a matching Add to budget ticket.
                    # Find it if it exists and complete it too.
                    match = matchbudgetticket(cursor, config, ticket)
                    if match is not None:
                        print("Matching 'Add to budget' ticket " + match['ticket_ID']  +  " found for this new user, carrying out.")
                        addtobudget(cursor, config, match['ticket_ID'])

                # new budget
                elif tickettype == "New Budget":
                    newbudget(cursor, config, ticket)
                # add to budget
                elif tickettype == "Add to budget":
                    addtobudget(cursor, config, ticket)
                else:
                    print("Ticket " + ticket + " type unrecognised: " + tickettype)
                    exit(1)
                 
            # Reject SAFE tickets - there are two types of rejection so ask
            if args.reject is not None:
                ticket = args.reject
                answer = thomas_utils.select_from_list("Reason to reject ticket: would it cause an error, or is it being rejected for any other reason?", ("other", "error"), default_ans="other")
                if answer == "error":
                    updateticket(config, rejecterror(ticket))
                else:
                    updateticket(config, rejectother(ticket))

            # commit the change to the database unless we are debugging
            if not args.debug:
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

# When not imported, use the normal global arguments
if __name__ == "__main__":
    main(sys.argv[1:])

