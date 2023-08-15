import base64
import json
import os
import boto3
import urllib
from urllib import request, parse
from datetime import date

s3 = boto3.client('s3')

class Location_Menu():
    def __init__(self, name = "Default", times = [], menus = []):
        self.name = name
        self.times = times
        self.menus = menus

class User():
    def __init__(self, number, state, item_list):
        self.number = number
        self.state = state
        self.item_list = item_list


def json_to_location_list(json_str):
        location_dict = json.loads(json_str)
        location_list = []
        for dict_reference in location_dict: 
            location_object = Location_Menu(dict_reference["name"], dict_reference["times"], dict_reference["menus"])
            location_list.append(location_object)
        return location_list

def grab_menu(location_str):
    bucket_name = 'DEFAULT' # REPLACE WITH REAL BUCKET NAME
    today = str(date.today())
    file_name = today + location_str + '.json'
    s3_response = s3.get_object(Bucket = bucket_name, Key = file_name)
    file_data = s3_response["Body"].read().decode('utf')
    location_list = json_to_location_list(file_data)
    return location_list

def json_to_user(json_str):
    user_dict = json.loads(json_str)
    return_user = User(user_dict["number"], user_dict["state"], user_dict["item_list"])
    return return_user
    
def grab_user(file_name):
    bucket_name = 'DEFAULT' # REPLACE WITH REAL BUCKET NAME
    s3_response = s3.get_object(Bucket = bucket_name, Key = file_name)
    file_data = s3_response["Body"].read().decode('utf')
    return_user = json_to_user(file_data)
    return return_user


    
TWILIO_SMS_URL = 'DEFAULT' # REPLACE WITH REAL SMS_URL
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")

def send_sms(to_num, from_num, output_str):
    to_number = to_num
    from_number = from_num
    body = output_str

    if not TWILIO_ACCOUNT_SID:
        return "Unable to access Twilio Account SID."
    elif not TWILIO_AUTH_TOKEN:
        return "Unable to access Twilio Auth Token."
    elif not to_number:
        return "The function needs a 'To' number in the format +xxxxxxxxxx"
    elif not from_number:
        return "The function needs a 'From' number in the format +xxxxxxxxxx"
    elif not body:
        return "The function needs a 'Body' message to send."

    # insert Twilio Account SID into the REST API URL
    populated_url = TWILIO_SMS_URL.format(TWILIO_ACCOUNT_SID)
    post_params = {"To": to_number, "From": from_number, "Body": body}

    # encode the parameters for Python's urllib
    data = parse.urlencode(post_params).encode()
    req = request.Request(populated_url)

    # add authentication header to request based on Account SID + Auth Token
    authentication = "{}:{}".format(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    base64string = base64.b64encode(authentication.encode('utf-8'))
    req.add_header("Authorization", "Basic %s" % base64string.decode('ascii'))

    try:
        # perform HTTP POST request
        with request.urlopen(req, data) as f:
            print("Twilio returned {}".format(str(f.read().decode('utf-8'))))
    except Exception as e:
        # something went wrong!
        return e

def user_list_to_item_dict(user_list):
    return_dict = {}
    for user in user_list:
        for item in user.item_list:
            return_dict[item] = return_dict.get(item, [])
            return_dict[item].append(user.number)
    return return_dict

def compare_dict_to_location(location, item_dict, dining_hall_name):
    numbers_texted = set([])
    for index in range(0, len(location.times)):
        for item in location.menus[index]:
            if item in item_dict.keys():
                for number in item_dict[item]:
                    send_sms(number, '+13093229548', f"{location.name} is serving {item} for {location.times[index]}. ({dining_hall_name})")
                    # print(f"sending to {number}: {location.name} is serving {item} for {location.times[index]}. ({dining_hall_name})")
                    numbers_texted.add(number)
    return numbers_texted

def find_matches(dining_hall_name, item_dict):
    numbers_texted = []
    dining_hall_locations = grab_menu(dining_hall_name)
    for location in dining_hall_locations:
        recently_texted_numbers = compare_dict_to_location(location, item_dict, dining_hall_name) # returns a set
        numbers_texted_set = set(numbers_texted)
        newly_texted_numbers = recently_texted_numbers - numbers_texted_set
        numbers_texted += newly_texted_numbers
    return numbers_texted

def combine_lists(l1, l2):
    l1_set = set(l1)
    l2_set = set(l2)
    unique_l2 = list(l2_set - l1_set)
    return l1 + unique_l2
    


def lambda_handler(event, context):
    user_list = []
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket = 'numbersinfocollection')
    for page in pages:
        for file in page['Contents']:
            file_name = file['Key']
            user_ref = grab_user(file_name)
            send_sms(user_ref.number, '+13093229548', "As of 4/28, this will be the last notification this message bot will send out. I plan to revive this bot in the Fall with an updated app interface. Thank you for staying subscribed. -Jericho")
            user_list.append(user_ref)

    return "Process Complete"
