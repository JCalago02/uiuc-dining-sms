from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from datetime import date
import boto3
import json

s3 = boto3.client('s3')

class Location_Menu():
    def __init__(self, name = "Default", times = [], menus = []):
        self.name = name
        self.times = times
        self.menus = menus

    
    def print_values(self):
        print(f"{self.name} is serving the following")
        for index in range(0, len(self.times)):
            print(f"    For {self.times[index]}: {self.menus[index]}")
def get_menu_data(driver):
    dining_hall_menu = driver.find_element(By.ID, "menuData")
    all_locations_reference = dining_hall_menu.find_elements(By.CLASS_NAME, "diningserviceunit")

    def format_string(input_string, removal_string):
        input_string = input_string.replace(removal_string, "")
        output_list = [x.strip() for x in input_string.split(",")]
        return output_list
        
    def is_time(paragraph_reference):
        reference_attribute_style = paragraph_reference.get_attribute("style").strip()
        style_is_empty = len(reference_attribute_style) < 1
        if style_is_empty:
            return False
        else:
            return True
    def bool_change_location(paragraph_reference, index):
        prev_element_ID = paragraph_references[index - 1].get_attribute("id")
        next_element_ID = paragraph_references[index + 1].get_attribute("id")
        prev_element_ID_compare_string = prev_element_ID.split("_")[0]
        next_element_ID_compare_string = next_element_ID.split("_")[0]
        return prev_element_ID_compare_string != next_element_ID_compare_string
    
    items_list = []
    per_time_item_list = []
    times_list = []
    locations_objects_list = []
    bold_elements = dining_hall_menu.find_elements(By.XPATH, "//div[@id='menuData']/p/b" )

    paragraph_references = dining_hall_menu.find_elements(By.XPATH, "//div[@id='menuData']/p")

    for index in range(0, len(paragraph_references)):
        paragraph = paragraph_references[index]
        if is_time(paragraph):
            is_not_first_element = index != 0
            if is_not_first_element:
                items_list.append(per_time_item_list)
            if is_not_first_element and bool_change_location(paragraph_references, index):
                location_object = Location_Menu(all_locations_reference[0].text, times_list, items_list)
                del all_locations_reference[0]
                locations_objects_list.append(location_object)
                times_list = []
                items_list = []
            per_time_item_list = []
            current_time = paragraph.text.split(" - ")
            times_list.append(current_time[0])
        else:
            bold_to_be_removed = bold_elements[0].text
            del bold_elements[0]
            formatted_item_list = format_string(paragraph.text, bold_to_be_removed)
            per_time_item_list += formatted_item_list
        if index == len(paragraph_references) - 1:
            items_list.append(per_time_item_list)
            location_object = Location_Menu(all_locations_reference[0].text, times_list, items_list)
            locations_objects_list.append(location_object)
    return locations_objects_list

def upload_aw3(locations_list, location_str):
    def location_to_dict(location_object):
        json_dict = {"name": location_object.name, "times": location_object.times, "menus": location_object.menus}
        return json_dict
        
    today = str(date.today())
    bucket = 'DEFAULT' # real bucket name would go here
    fileName = today + location_str + '.json'
    final_json_string = json.dumps(locations_list, default=location_to_dict)
    uploadByteStream = bytes(final_json_string.encode('UTF-8'))
    s3.put_object(Bucket = bucket, Key = fileName, Body = uploadByteStream)
    
def main(event, context):
    options = Options()
    options.binary_location = '/opt/headless-chromium'
    options.add_argument('--window-size=1920,1080')  
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--single-process')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome('/opt/chromedriver',chrome_options=options)
    driver.implicitly_wait(5)
    driver.get('https://web.housing.illinois.edu/diningmenus')
    dining_hall_selector = Select(driver.find_element(By.ID, 'dineop'))
    submit_changes_button = driver.find_element(By.CLASS_NAME, "il-button")
    
    # sets the page to the menu for "Ikenberry Dining Center"
    dining_hall_selector.select_by_value('Ikenberry Dining Center')
    submit_changes_button.click()
    
    # parses the menu and formats
    locations_objects_list = get_menu_data(driver)
    print(locations_objects_list[0].name)
    upload_aw3(locations_objects_list, "IKE")

    # sets the page to the menu for "ISR Dining Center"
    dining_hall_selector.select_by_value('ISR Dining Center')
    submit_changes_button.click()
    
    # parses the menu and formats
    locations_objects_list = get_menu_data(driver)
    print(locations_objects_list[0].name)
    upload_aw3(locations_objects_list, "ISR")
    
    driver.close()
    driver.quit()
    response = {
        "statusCode": 200,
        "body": "hello"
    }

    return response