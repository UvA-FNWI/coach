import requests

LRS = "http://cygnus.ic.uva.nl:8000/XAPI/statements"

u = raw_input("LRS username: ")
p = raw_input("LRS password: ")

r = requests.get(LRS,headers={"X-Experience-API-Version":"1.0"},auth=(u,p));
if r.status_code == 200:
    print "Success"
else:
    print "Server returns",r.status_code
