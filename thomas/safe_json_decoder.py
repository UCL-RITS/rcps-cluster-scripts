# This module provides classes and procedures for converting the JSON example we have been provided with into 
# Python classes.

# We only have an example of a create account request so far so to process that call JSONtoAccountRequest(JSONData)
# where JSONData is a string with an account request.

# Also includes fairly dodgy __str__ methods for testing purposes.

# Owain Kenway

# For reasons the request is enclosed in a Sysadmin object.
class SysAdmin:

    known_keys = ["Id", "Type", "Status", "StartDate", "EndDate", "Machine", "Handler", "Approver", "Person", "ProjectGroup", "Project", "Account", "ExtraText"]

    def __init__(self, SysAdminDict):
        for a in SysAdminDict.keys():
            if a not in self.known_keys:
                print("Warning [SysAdmin]: Detected unknown key: " + a + ": " + str(SysAdminDict[a]))
        self.Id=SysAdminDict["Id"]
        self.Type=SysAdminDict["Type"]
        self.Status=SysAdminDict["Status"]
        self.StartDate=SysAdminDict["StartDate"]
        self.EndDate=SysAdminDict["EndDate"]
        self.Machine=SysAdminDict["Machine"]
        self.HandlerName=SysAdminDict["Handler"]["Name"]
        self.HandlerEmail=SysAdminDict["Handler"]["Email"]
        self.Approver=""
        # Approver is an instance of Person
        if "Approver" in SysAdminDict.keys():
            self.Approver=Person(SysAdminDict["Approver"])
        self.Person=""
        if "Person" in SysAdminDict.keys():
            self.Person=Person(SysAdminDict["Person"])
        self.ProjectGroup=ProjectGroup(SysAdminDict["ProjectGroup"])
        self.Project=Project(SysAdminDict["Project"])
        self.Account=""
        if "Account" in SysAdminDict.keys():
            self.Account=Account(SysAdminDict["Account"])            
        self.ExtraText=""
        if "ExtraText" in SysAdminDict.keys():
            self.ExtraText=SysAdminDict["ExtraText"]

    def __str__(self):
        return "SysAdmin: " + ",\n".join([self.Id, 
                                        self.Type, 
                                        self.Status, 
                                        self.StartDate, 
                                        self.EndDate,
                                        self.HandlerName,
                                        self.HandlerEmail,
                                        str(self.Approver),
                                        str(self.Person),
                                        str(self.Project),
                                        str(self.ProjectGroup),
                                        str(self.Account),
                                        self.Machine,
                                        self.ExtraText])

class Project:

    known_keys = ["Code", "Name", "Status", "ProjectClass", "FundingBody", "Machines", "TopGroup"]

    def __init__(self, ProjectDict):
        for a in ProjectDict.keys():
            if a not in self.known_keys:
                print("Warning [Project]: Detected unknown key: " + a + ": " + str(ProjectDict[a]))
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

    known_keys = ["Code", "GroupID"]

    def __init__(self, ProjectGroupDict):
        for a in ProjectGroupDict.keys():
            if a not in self.known_keys:
                print("Warning [ProjectGroup]: Detected unknown key: " + a + ": " + str(ProjectGroupDict[a]))
        self.Code=ProjectGroupDict["Code"]
        self.GroupID=ProjectGroupDict["GroupID"]

    def __str__(self):
        return "ProjectGroup: " + ",\n".join([self.Code,
                                            self.GroupID])

class Account:

    known_keys = ["Name", "GID", "Groups", "Person", "UID", "Machines"]

    def __init__(self, AccountDict):

        for a in AccountDict.keys():
            if (a not in self.known_keys) and (not a.startswith("Group")):
                print("Warning [Account]: Detected unknown key: " + a + ": " + str(AccountDict[a]))

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

    known_keys = ["Name", "Email", "WebName", "PublicKey", "NormalisedPublicKey", "HartreeName"]

    def __init__(self, PersonDict):
        for a in PersonDict.keys():
            if a not in self.known_keys:
                print("Warning [Person]: Detected unknown key: " + a + ": " + str(PersonDict[a]))

        self.Title=PersonDict["Name"]["Title"]
        if type(self.Title) == type(None):
            self.Title = ""
        self.FirstName=PersonDict["Name"]["Firstname"]
        self.LastName=PersonDict["Name"]["Lastname"]
        self.Email=PersonDict["Email"]
        self.WebName=""
        if "WebName" in PersonDict.keys():
            self.WebName=PersonDict["WebName"]
        self.PublicKey=""
        if "PublicKey" in PersonDict.keys():
            self.PublicKey=PersonDict["PublicKey"]
        self.NormalisedPublicKey=""
        if "NormalisedPublicKey" in PersonDict.keys():
            self.NormalisedPublicKey=PersonDict["NormalisedPublicKey"]
        self.HartreeName=""
        if "HartreeName" in PersonDict.keys():
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
def JSONtoTickets(JSONData):
    import json
    from io import StringIO

    jsdata = json.load(StringIO(JSONData))

    return JSONDataToTickets(jsdata)

# Convert JSON data structure to a list of objects
def JSONDataToTickets(JSONData):
    Tickets = []
    if type(JSONData) == list:
        for a in JSONData:
            Tickets.append(AccountRequest(a))
    else:
        Tickets.append(AccountRequest(JSONData))
    return Tickets

# If this is run directly, process test.json in the current working directory and print the output as a string.
if __name__=="__main__":
    import json
    import sys

    filename="test.json"

    if len(sys.argv) > 1:
	    filename=sys.argv[1]

    f = open(filename, 'r')
    jdata=f.read()
    ar=JSONtoTickets(jdata)
    f.close()
    for a in ar:
        print(str(a.Ticket))
    
    print("Number of tickets included: " + str(len(ar)))
