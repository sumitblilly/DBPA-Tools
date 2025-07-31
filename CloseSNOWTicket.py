"""
Script to automatically close a ServiceNow RITM after adding comments to it.
Author: Sumit Bhardwaj - Enterprise Automation
Version: v1.0
"""

import requests
import sys

#basic checks
if len(sys.argv)<3:
    print ("Please provide an RITM and Closing comments as first and second arguments respectively while running this script.")
    print ("Usage: closeSnowTicket.py <RITM> <Closing Comments> <SNOW Environment: Default DEV>[<DEV> | <QA> | <PROD>]")
    sys.exit(0)
elif len(sys.argv)<2:
    print ("Please provide an RITM as first argument to this script.")
    print ("Usage: closeSnowTicket.py <RITM> <Closing Comments> <SNOW Environment: Default DEV>[<DEV> | <QA> | <PROD>]")
    sys.exit(0)


# Configuration
environments={"DEV":"lillydev", "QA":"lillyqa", "PROD":"lilly"}
instance = ""
if len(sys.argv)<4:
    instance=environments["DEV"]
else
    instance=environments[sys.argv[3]]

client_id = ''
client_secret = ''
username = ''
password = ''
ritm_sys_id = ''
ritm_to_close=sys.argv[1]
comment_text=sys.argv[2]
access_token=""


def get_access_token():
    """
    Function to get access token from ServiceNow
    """
    
    token_url = f'https://{instance}.service-now.com/oauth_token.do'

    token_payload = {
        'grant_type': 'password',
        'client_id': client_id,
        'client_secret': client_secret,
        'username': username,
        'password': password
    }

    token_response = requests.post(token_url, data=token_payload)
    if token_response.status_code != 200:
        print(f"Failed to get token: {token_response.status_code}")
        print(token_response.text)
        return None

    return token_response.json().get('access_token')
    


def get_sysid_from_ritm(ritm=""):
    """
    Function to get sysid from a RITM number. 
    """
    
    query_url = f'https://{instance}.service-now.com/api/now/table/sc_req_item'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    params = {
        'sysparm_query': f'number={ritm_to_close}',
        'sysparm_fields': 'sys_id,number,short_description'
    }

    response = requests.get(query_url, headers=headers, params=params)

    
    if response.status_code == 200:
        result = response.json().get('result')
        if result:
            ritm = result[0]
            print(f"RITM Number: {ritm['number']}")
            print(f"sys_id: {ritm['sys_id']}")
            print(f"Short Description: {ritm['short_description']}")
            return ritm["sys_id"]
        else:
            print("No RITM found with that number.")
            return None
    else:
        print(f"Failed to retrieve RITM. Status code: {response.status_code}")
        print(response.json())
        return None


def update_and_close_ritm(access_token, ritm_sys_id):
    """
    Function to add a comment and then close a RITM
    """
    update_url = f'https://{instance}.service-now.com/api/now/table/sc_req_item/{ritm_sys_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    payload = {
        'comments': comment_text,
        'state': '3'  # Typically 'Closed Complete'
    }

    update_response = requests.patch(update_url, headers=headers, json=payload)

    # Step 3: Check result
    if update_response.status_code == 200:
        print('RITM updated and closed successfully.')
        return True
    else:
        print(f'Failed to update RITM. Status code: {update_response.status_code}')
        print(update_response.json())
        return False



#Run the program
if "__name__"=="__main__":
    
    #Step 1: Get access token
    access_token=get_access_token()

    if access_token==None or access_token=="":
        print ("Error: Unable to get access token from ServiceNow. Exiting.")
        sys.exit(0)
    
    #Step 2: Get RITM Sys ID
    ritm_sys_id=get_sysid_from_ritm(ritm_to_close)

    if ritm_sys_id==None or ritm_sys_id=="":
        print ("Error: Unable to get system id for the RITM from ServiceNow. Exiting.")
        sys.exit(0)

    #Step 3: Actually update and close the access token
    status=update_and_close_ritm(access_token=access_token, ritm_sys_id=ritm_sys_id)

    if status==False:
        print ("Error: Unable to complete the update and close operation for RITM: " + ritm_to_close + ", RITM Sys ID: "+ritm_sys_id +". Exiting.")
        sys.exit(0)
    else:
        print ("RITM " + ritm_to_close + " with RITM Sys ID: "+ritm_sys_id +" successfully updated and closed.")

    