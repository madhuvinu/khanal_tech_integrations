import frappe
from frappe.utils import add_to_date, get_datetime, now_datetime, today
import requests




def AuthenticateSafexpress():
    doc = frappe.get_doc('Safexpress Settings')
    """Function to authenticate SafeXpress API. 
    Renew the token only if expired and 
    returns the doc instance
	"""
        
    # RENEW TOKEN ONLY IF EXPIRED
    expires_on = frappe.db.get_single_value('Safexpress Settings', 'expires_on')
    # print(expires_on)
    if (expires_on==''):
        try:
            safexpress_doc = renew_session()
        except Exception as e:
            raise e
    
    elif (expires_on != ''): 
        if now_datetime() >= get_datetime(doc.expires_on):
            try:
                safexpress_doc = renew_session()
            except Exception as e:
                raise e
        # DO NOT RENEW IF NOT EXPIRED
        else:
            safexpress_doc = doc        
        return safexpress_doc



import requests
import logging

# logging.basicConfig(level=logging.DEBUG)  # Set the logging level to DEBUG

def renew_session():
    doc = frappe.get_doc('Safexpress Settings')
    requrl = doc.login_url
    payload={   "grant_type": 'client_credentials',
                "scope": 'server/waybillapps',
                "username":doc.username,
                "password":doc.password}
    headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': '*/*',
                'Authorization': 'Basic Zm1xYWRsY2ZyY29jdW5hY2xyaWxodTRsbTpqamZ0M3Izb2ZtOWxsbmJudmZxMHZic2FwN2oxZWRrNm4wYzE5am5yM2VlMWVxcnNxNWE=',
                'Cookie': 'XSRF-TOKEN=5de4fefb-a52f-439f-83c2-ad473f2cef5b'
                }
    try:
        response = requests.request("POST", requrl, headers=headers, data=payload, timeout=10,verify=False)  # Timeout set to 10 seconds
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        resp_json = response.json()
        doc.access_token = resp_json['access_token']
        doc.expires_on = add_to_date(now_datetime(), seconds=int(resp_json["expires_in"]))
        doc.save()
        frappe.db.commit()
    except requests.exceptions.Timeout as e:
        logging.error(f"Request Timeout: {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request Exception: {e}")
    except ValueError as e:
        logging.error(f"JSON Parsing Error: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

    # response=requests.request("POST", requrl, headers=headers, data=payload)
    # print(response)
    # print(response.text)
    # resp_json = response.json()
    # doc.access_token = resp_json['access_token']
    # doc.expires_on = add_to_date(now_datetime(), seconds=int(resp_json["expires_in"]))
    # doc.save()
    # frappe.db.commit()
    # return doc
 

    # bench --site dev.localhost execute khanal_tech_integrations.utils.safexpress.auth.AuthenticateSafexpress

#%%
# import requests
# def SafeXpressAuth():
#     url = "https://api-auth.safexpress.com/oauth2/token"

#     payload={   "grant_type": 'client_credentials',
#                 "scope": 'server/waybillapps',
#                 "username":'fmqadlcfrcocunaclrilhu4lm',
#                 "password":'jjft3r3ofm9llnbnvfq0vbsap7j1edk6n0c19jnr3ee1eqrsq5a'
#                 }
#     headers = {
#     'Content-Type': 'application/x-www-form-urlencoded',
#     'Authorization': 'Basic Zm1xYWRsY2ZyY29jdW5hY2xyaWxodTRsbTpqamZ0M3Izb2ZtOWxsbmJudmZxMHZic2FwN2oxZWRrNm4wYzE5am5yM2VlMWVxcnNxNWE=',
#     'Cookie': 'XSRF-TOKEN=6d10c3b7-9dc5-496c-af3d-3fe9a5549618'
#     }

#     response = requests.request("POST", url, headers=headers, data=payload)

#     print(response.text)

# SafeXpressAuth()

# %%
