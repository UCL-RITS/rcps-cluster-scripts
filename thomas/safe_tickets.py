#!/usr/bin/env python3

import os.path
import sys
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

def getopentickets(config)
    request = requests.get(config['safe']['host'] + "?mode=json", auth = (config['safe']['user'], config['safe']['password']))
    data = request.json()
    return data
# end getopentickets

def updateticket()

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

