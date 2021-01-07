import re
import os
import sys
import json

from selenium.common.exceptions import NoSuchElementException

def safe_find_elements_by_xpath(driver, xpath):
    try:
        return driver.find_elements_by_xpath(xpath)
    except NoSuchElementException:
        return None

def safe_find_element_by_id(driver, elem_id):
    try:
        return driver.find_element_by_id(elem_id)
    except NoSuchElementException:
        return None

def contains_year(input: str) -> bool:
    match = re.match(r'.*([1-3][0-9]{3})', input)
    if match is not None:
        return True
    return False

def cls():
    os.system('cls' if os.name=='nt' else 'clear')
    return

def save_to_file_in_json(result, filename):
    with open(filename, "w", encoding='utf-8') as output:
        json.dump(result, output, indent=4, sort_keys=False, ensure_ascii=False)
    return

def read_from_file(filename):
    ids = set()
    for line in open(filename):
        if line.lstrip().startswith("#") or line.strip() == "":
            continue
        ids.add(line.strip())
    return ids

def read_from_console():
    data = input()
    ids = set()
    for id in data.split(","):
        ids.add(id.strip("'"))
    return ids