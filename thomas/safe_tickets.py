#!/usr/bin/env python3

import os.path
import sys
import configparser
import argparse
import subprocess
import validate
import mysql.connector
from mysql.connector import errorcode
import requests
import safe_json_decoder as decoder
#from ldap3 import Server, Connection, ALL
#import socket
#import thomas_queries
#import thomas_utils

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
        config = configparser.ConfigParser()
        config.read_file(open(os.path.expanduser('~/.thomas.cnf')))
    #except FileNotFoundError as err:
    except OSError as err:
        print(err)

    # get SAFE tickets
    jsontickets = getopentickets(config)

    # parse SAFE tickets
    ticketlist = decoder.JSONDataToTickets(jsontickets)

    # print SAFE tickets
    for t in ticketlist:
        print(t)

    # act on SAFE tickets

# end main

# When not imported, use the normal global arguments
if __name__ == "__main__":
    main(sys.argv[1:])

