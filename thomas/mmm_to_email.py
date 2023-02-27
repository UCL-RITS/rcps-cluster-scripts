#!/usr/bin/env python3

# A simple tool to convert mmm userids into an email address for killandmail.

def getEmail(userid):
    import mysql.connector
    from mysql.connector import errorcode

    email=""

    cluster_dbs = ["thomas","young"]
    union_string = ' union '.join(["SELECT username,email FROM %s.users" % c for c in cluster_dbs])


    query = "SELECT email FROM (%s) AS t1 WHERE username LIKE '%s';" % (union_string, userid)

    try:
        conn = mysql.connector.connect(option_files=os.path.expanduser('~/.thomas.cnf'), database='thomas')
        cursor = conn.cursor()

        cursor.execute(query)
        results=cursor.fetchall()

        email = results[0][0]
    
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

    return email

if __name__ == "__main__":
    import sys
    import os.path

    if len(sys.argv) != 2:
        print("Run with " + sys.argv[0] + " <userid>")
        sys.exit(1)

    if not(os.path.isfile(os.path.expanduser('~/.thomas.cnf'))):
        print("Database connection not configured.")
        sys.exit(2)

    userid = sys.argv[1]

    if not(userid.startswith("mmm") and (len(userid) == 7)):
        print("Invalid userid.  Userid must be of the form mmmXXXX.")
        sys.exit(3)

    email = getEmail(userid)

    if email != "":
        print(email)
    else:
        sys.exit(10)

    
