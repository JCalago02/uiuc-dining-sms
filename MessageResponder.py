from __future__ import print_function
import json
import boto3
import os
from datetime import date

s3 = boto3.client('s3')


class User():
    def __init__(self, number, state, item_list):
        self.number = number
        self.state = state
        self.item_list = item_list

def update_user(user_ref):
    bucket_name = 'DEFAULT' # REPLACE WITH REAL BUCKET NAME
    file_name = user_ref.number+ '.json'
    final_json_string = json.dumps({"number": user_ref.number, "state": user_ref.state, "item_list": user_ref.item_list})
    uploadByteStream = bytes(final_json_string.encode('UTF-8'))
    s3.put_object(Bucket = bucket_name, Key = file_name, Body = uploadByteStream)
    
def json_to_user(json_str):
    user_dict = json.loads(json_str)
    return_user = User(user_dict["number"], user_dict["state"], user_dict["item_list"])
    return return_user
    
def grab_user(number):
    bucket_name ='DEFAULT' # REPLACE WITH REAL BUCKET NAME
    file_name = number+ '.json'
    s3_response = s3.get_object(Bucket = bucket_name, Key = file_name)
    file_data = s3_response["Body"].read().decode('utf')
    return_user = json_to_user(file_data)
    return return_user

def update_user_list(user_ref):
    bucket_name = 'DEFAULT' # REPLACE WITH REAL BUCKET NAME
    file_name = 'user_list.txt'
    s3_response = s3.get_object(Bucket = bucket_name, Key = file_name)
    file_data = s3_response["Body"].read().decode('utf')
    file_data += f",{user_ref.number}"
    uploadByteStream = bytes(file_data.encode('UTF-8'))
    s3.put_object(Bucket = bucket_name, Key = file_name, Body = uploadByteStream)
    
def format_string_view(user_ref):
    if len(user_ref.item_list) == 0:
        return "Your notification list is currently empty. Text Add to add some items"
    return_str = "Your current list is: "
    for item in user_ref.item_list:
        return_str += item + ", "
    return return_str[:-2]

def delete_user(user_ref):
    bucket_name = 'DEFAULT' # REPLACE WITH REAL BUCKET NAME
    file_name = user_ref.number+ '.json'
    s3.delete_object(Bucket = bucket_name, Key = file_name)
    
def lambda_handler(event, context):
    try: 
        this_user = grab_user(event['From'])
    except:
        this_user = User(event['From'], "DEFAULT", [])
        update_user(this_user) 
        update_user_list(this_user)
        print("New user called program")
        
    str_output = "You should never get here, if you did uh..."
    user_input_str = event['Body']
    # separate commands via non commands and state flow-throughs
    if user_input_str == "Help":
        this_user.state = "DEFAULT"
        str_output = "List of Commands: Add, Remove, View, Unsub"
    elif user_input_str == "Add":
        this_user.state = "ADD"
        update_user(this_user)
        str_output = "Enter an item you want to be notified for (note that items must be exactly the same as listed at https://web.housing.illinois.edu/diningmenus, this is a WIP)"
    elif user_input_str == "Remove":
        this_user.state = "REMOVE"
        update_user(this_user)
        str_output = "Enter an item you want to remove from your list (note that items must be exactly the same as listed when seen with the View command)"
    elif user_input_str == "View":
        str_output = format_string_view(this_user)
    elif user_input_str == "Done":
        str_output = "Process quit. Text \"Help\" for more commands."
        this_user.state = "DEFAULT"
        update_user(this_user)
    elif user_input_str == "Unsub":
        str_output = "Are you sure you want to unsubscribe? Type \"YES\" (case sensitive) to stop receiving SMS messages. Note that this will delete all data associated with your phone number"
        this_user.state = "UNSUB"
        update_user(this_user)
    elif this_user.state == "UNSUB":
        if user_input_str == "YES":
            delete_user(this_user)
            str_output = "Successfully unsubscribed. Note that you can text this number at any time to reconfigure notifications"
        else:
            str_output = "Cancelling unsubscription request. Please text \"Unsub\" to try again"
            this_user.state == "DEFAULT"
            update_user(this_user)
    elif this_user.state == "REMOVE":
        try:
            this_user.item_list.remove(user_input_str)
            str_output = f"Successfully removed {user_input_str}. Input another item or text \"Done\" to quit."
            update_user(this_user)
        except:
            str_output = f"Your list doesn't seem to contain {user_input_str}. Please retry or text \"Done\" to quit."
    elif this_user.state == "ADD":
        this_user.item_list.append(event['Body'])
        str_output = f"Adding {event['Body']} to your food watchlist. Text another food name to add more food to your notification list or text \"Done\" to quit"
        update_user(this_user)
    else:
        str_output = "That's not a command. (All commands are case sensitive, text \"Help\" to get started)"

    print(str_output)
    print(this_user.state)
    print(len(str_output))
    return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"\
           f"<Response><Message><Body>{str_output}</Body></Message></Response>"
