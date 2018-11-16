# This module provides classes and procedures for converting the JSON example we have been provided with into 
# Python classes.

# We only have an example of a create account request so far so to process that call JSONtoAccountRequest(JSONData)
# where JSONData is a string with an account request.

# Also includes fairly dodgy __str__ methods for testing purposes.

# Owain Kenway

# For reasons the request is enclosed in a Sysadmin object.
class SysAdmin:

    def __init__(self, SysAdminDict):
        self.Id=SysAdminDict["Id"]
        self.Type=SysAdminDict["Type"]
        self.Status=SysAdminDict["Status"]
        self.StartDate=SysAdminDict["StartDate"]
        self.EndDate=SysAdminDict["EndDate"]
        self.Machine=SysAdminDict["Machine"]
        self.HandlerName=SysAdminDict["Handler"]["Name"]
        self.HandlerEmail=SysAdminDict["Handler"]["Email"]
        self.Person=Person(SysAdminDict["Person"])
        self.ProjectGroup=ProjectGroup(SysAdminDict["ProjectGroup"])
        self.Project=Project(SysAdminDict["Project"])
        self.Account=Account(SysAdminDict["Account"])

    def __str__(self):
        return "SysAdmin: " + ",\n".join([self.Id, 
                                        self.Type, 
                                        self.Status, 
                                        self.StartDate, 
                                        self.EndDate,
                                        self.HandlerName,
                                        self.HandlerEmail,
                                        str(self.Person),
                                        str(self.Project),
                                        str(self.ProjectGroup),
                                        str(self.Account),
                                        self.Machine])

class Project:

    def __init__(self, ProjectDict):
        self.Code=ProjectDict["Code"]
        self.Name=ProjectDict["Name"]
        self.Status=ProjectDict["Status"]
        self.ProjectClass=ProjectDict["ProjectClass"]
        self.FundingBody=ProjectDict["FundingBody"]
        self.Machines=str.split(ProjectDict["Machines"], ",") # Comma sep list
        self.TopGroup=ProjectGroup(ProjectDict["TopGroup"])

    def __str__(self):
        return "Project: " + ",\n".join([self.Code,
                                        self.Name,
                                        self.Status,
                                        self.ProjectClass,
                                        self.FundingBody,
                                        str(self.Machines),
                                        str(self.TopGroup)])

class ProjectGroup:

    def __init__(self, ProjectGroupDict):
        self.Code=ProjectGroupDict["Code"]
        self.GroupID=ProjectGroupDict["GroupID"]

    def __str__(self):
        return "ProjectGroup: " + ",\n".join([self.Code,
                                            self.GroupID])

class Account:

    def __init__(self, AccountDict):
        self.Name=AccountDict["Name"]
        self.GroupID=AccountDict["GID"]
        
        # Need code for parsing group fmt
        self.Groups=[]
        for a in AccountDict.keys():
            if (a.startswith("Group") and a != "Groups"):
                self.Groups.append(ProjectGroup(AccountDict[a])) 

        self.Person=Person(AccountDict["Person"])
        self.UserID=AccountDict["UID"]
        self.Machines=str.split(AccountDict["Machines"], ",")

    def __str__(self):
        strGroups = "Groups: "
        for a in self.Groups:
            strGroups += str(a) + ",\n"

        return "Account: " + ",\n".join([self.Name,
                                        self.GroupID,
                                        str(self.Person),
                                        strGroups,
                                        self.UserID,
                                        str(self.Machines)])

class Person:

    def __init__(self, PersonDict):
        self.Title=PersonDict["Name"]["Title"]
        self.FirstName=PersonDict["Name"]["Firstname"]
        self.LastName=PersonDict["Name"]["Lastname"]
        self.Email=PersonDict["Email"]
        self.WebName=PersonDict["WebName"]
        self.PublicKey=PersonDict["PublicKey"]
        self.NormalisedPublicKey=PersonDict["NormalisedPublicKey"]
        self.HartreeName=PersonDict["HartreeName"]

    def __str__(self):
        return "Person: " + ",\n".join([
                                        self.Title,
                                        self.FirstName,
                                        self.LastName,
                                        self.Email,
                                        self.WebName,
                                        self.PublicKey,
                                        self.NormalisedPublicKey,
                                        self.HartreeName])

class AccountRequest:

    def __init__(self, SystemTicketDict):
        self.Ticket=SysAdmin(SystemTicketDict["SysAdmin"])

# Convert String to objects.
def JSONtoAccountRequest(JSONData):
    import json
    from io import StringIO
    return AccountRequest(json.load(StringIO(JSONData)))

# If this is run directly, process test.json in the current working directory and print the output as a string.
if __name__=="__main__":
    import json
    import sys

    filename="test.json"

    if len(sys.argv) > 1:
	    filename=sys.argv[1]

    f = open(filename, 'r')
    jdata=f.read()
    ar=JSONtoAccountRequest(jdata)
    f.close()
    print(str(ar.Ticket))
    