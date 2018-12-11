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
#from ldap3 import Server, Connection, ALL
#import socket
import thomas_queries
#import thomas_utils

def getargs(argv):
    parser = argparse.ArgumentParser(description="Show or update and close tickets from SAFE. Use [positional argument -h] for more help.")
    parser.add_argument("-s", "--show", dest="show", help="Show all current open tickets", action='store_true')
    parser.add_argument("-f", "--file", dest="jsonfile", default=None, help="Parse json tickets from a file")
    parser.add_argument("-r", "--refresh", dest="refresh", help="Refresh open tickets in DB", action='store_true')
    parser.add_argument("-c", "--complete", dest="complete", default=None, help="Complete this ticket ID")

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

def updatebudget(ticket_id, projectname):
    parameters = {'qtid':ticket_id, 'new_username':projectname, 'mode':'completed'}


# Update and close a ticket.
# parameters is a dictionary of values: {'qtid':id,'new_username':'Test', 'mode':'completed'}
def updateticket(config, parameters):
    request = requests.post(config['safe']['host'], auth = (config['safe']['user'], config['safe']['password']), params = parameters)
    if "<title>SysAdminServlet Success</title>" in request.text:
        print("Ticket " + parameters['qtid'] + " closed.")

# end updateticket


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
    if args.jsonfile != None:
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
        print("Number of tickets included: " + str(len(ticketlist)))


    # these options require a database connection
    if args.refresh or args.update != None:
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
                    # show database tickets
    
                # act on SAFE tickets


                # commit the change to the database unless we are debugging
                if not args.debug:
                    #if args.verbose:
                    #    print("")
                    #    print("Committing database change")
                    #    print("")
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

