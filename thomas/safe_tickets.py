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
#import thomas_queries
#import thomas_utils

def getargs(argv):
    parser = argparse.ArgumentParser(description="Show or update and close tickets from SAFE. Use [positional argument -h] for more help.")
    parser.add_argument("-s", "--show", dest="show", help="Show all current open tickets", action='store_true')
    parser.add_argument("-f", "--file", dest="jsonfile", default=None, help="Parse json tickets from a file")

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

def updatebudget(ticket_id, projectname):
    parameters = {'qtid':ticket_id, 'new_username':projectname, 'mode':'completed'}


# Update and close a ticket.
# parameters is a dictionary of values: {'qtid':id,'new_username':'Test', 'mode':'completed'}
def updateticket(config, parameters):
    request = requests.post(config['safe']['host'], auth = (config['safe']['user'], config['safe']['password']), params = parameters)
    if "<title>SysAdminServlet Success</title>" in request.text:
        print("Ticket " + parameters['qtid'] + " closed.")

# end updateticket



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
        jsontickets = getopentickets(config)

        # parse SAFE tickets
        ticketlist = decoder.JSONDataToTickets(jsontickets)

        # print SAFE tickets
        for t in ticketlist:
            #print(str(t.Ticket))
            values = [t.Ticket.Id, t.Ticket.Type, t.Ticket.Status, t.Ticket.StartDate, t.Ticket.EndDate, t.Ticket.Machine, t.Ticket.ProjectGroup.Code, t.Ticket.Account.Person.FirstName, t.Ticket.Account.Person.LastName, t.Ticket.Account.Person.Email, t.Ticket.Account.Person.NormalisedPublicKey]
            print(values)
        print("Number of tickets included: " + str(len(ticketlist)))


    # act on SAFE tickets

# end main

# When not imported, use the normal global arguments
if __name__ == "__main__":
    main(sys.argv[1:])

