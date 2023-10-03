#!/usr/bin/python3
# Clockify User/Group/Manager report
#
# replace the api_key with the value of your key, and change the outputDir
#

# this will work for up to 5000 users - if larger, you will have to add a page-size loop

import csv

import requests

# constants for queries
outputDir = '/tmp/'

api_key = 'YOUR_API_KEY_HERE'
api_base = 'https://api.clockify.me/api/v1/'
headers = {'X-Api-Key': api_key, 'Content-Type': 'application/json'}
payload = {'page-size': 5000}
OK = 200
csv_headers = ['UserId', 'email', 'name', 'invitationStatus', 'userStatus', 'managerId', 'managerName', 'managerEmail']
offset = len(csv_headers)

print('Collecting data from API')

# Get workspace data
url = api_base + 'workspaces'
r = requests.get(url, headers=headers, params=payload)

if r.status_code != OK:
    print('HTTP Error: %s' % r.status_code)
    exit(1)

workspace = r.json()[0]

# get user-groups
url = api_base + 'workspaces/' + workspace['id'] + '/user-groups'
r = requests.get(url, headers=headers, params=payload)

if r.status_code != OK:
    print('HTTP Error: %s' % r.status_code)
    exit(2)

groups = r.json()

for i in range(len(groups)):
    csv_headers.append(groups[i]['name'])

csv_headers.append('groupCount')

# get user group memberships

payload = {'page-size': 5000, 'memberships': 'USERGROUP'}
url = api_base + 'workspaces/' + workspace['id'] + '/users'
r = requests.get(url, headers=headers, params=payload)

if r.status_code != OK:
    print('HTTP Error: %s' % r.status_code)
    exit(3)

memberships = r.json()

# get users
payload = {'page-size': 5000, 'memberships': 'WORKSPACE'}
url = api_base + 'workspaces/' + workspace['id'] + '/users'
r = requests.get(url, headers=headers, params=payload)

if r.status_code != OK:
    print('HTTP Error: %s' % r.status_code)
    exit(4)

users = r.json()
payload = {'page-size': 5000}
rows = []
row = dict()

# build by user
for i in range(len(users)):
    row = {
        str(csv_headers[0]): users[i].get('id'),
        str(csv_headers[1]): users[i].get('email'),
        str(csv_headers[2]): users[i].get('name'),
        str(csv_headers[3]): users[i].get('status'),
        str(csv_headers[4]): users[i]['memberships'][0]['membershipStatus']
    }

    # get user's managers
    url = api_base + 'workspaces/' + workspace['id'] + '/users/' + users[i].get('id') + '/managers'
    r = requests.get(url, headers=headers, params=payload)
    if r.status_code != OK:
        print('HTTP Error: %s' % r.status_code)
        exit(5)

    manager = r.json()

    if len(manager) >= 1:
        managerIds = ''
        managerNames = ''
        managerEmails = ''
        for j in range(len(manager)):
            managerIds += manager[j].get('id') + ','
            managerNames += manager[j].get('name') + ','
            managerEmails += manager[j].get('email') + ','
        row.update({str(csv_headers[5]): managerIds[:-1]})
        row.update({str(csv_headers[6]): managerNames[:-1]})
        row.update({str(csv_headers[7]): managerEmails[:-1]})
    else:
        row.update({str(csv_headers[5]): None})
        row.update({str(csv_headers[6]): None})
        row.update({str(csv_headers[7]): None})

    # get and count group memberships
    groupCount = 0
    for g in range(len(groups)):
        index = g + offset
        if users[i].get('id') in groups[g].get('userIds'):
            row.update({str(csv_headers[index]): True})
            groupCount += 1
        else:
            row.update({str(csv_headers[index]): False})

    row.update({'groupCount': groupCount})
    rows.append(row)

# write CSV file
outfile = outputDir + workspace['name'] + '.csv'
print('Writing CSV file to %s' % outfile)
with open(outfile, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_headers, dialect='excel')
    writer.writeheader()
    writer.writerows(rows)

print('Done')
exit(0)
