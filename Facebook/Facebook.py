import sys
import yaml
import utils

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, InvalidSessionIdException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def scraper(ids):
    with open("credentials.yaml", "r") as ymlfile:
        cfg = yaml.safe_load(stream=ymlfile)
        #print(cfg);

    if ("password" not in cfg) or ("email" not in cfg):
        print("Your email or password is missing. Kindly write them in credentials.yaml")
        exit(1)

    if len(ids) > 0:        
        print("Input ids: {}".format(ids))
        print("\n\nRun selenium:")
        login(cfg["email"], cfg["password"])
        
        print("\n\nStarting Scraping...")
        result = {}
        for id in ids:
            result[id] = scrap_profile(id)
        utils.save_to_file_in_json(result,"output.json")
        print("\n\n\n\t\t\t\t R E S U L T S (also in 'output.json')")
        print(open("output.json", "r", encoding = 'utf-8').read())
        print("\n\n")
        try:
            driver.close()
        except InvalidSessionIdException as e:
            print("InvalidSessionIdException while closing driver.")
    else:
        print("Input file is empty.")
    return

def login(email, password):
    """ Logging into our own profile """

    try:
        global driver
        
        options = webdriver.ChromeOptions()

        #  Code to disable notifications pop up of Chrome Browser
        #options.add_experimental_option("excludeSwitches",['enable-logging'])
        #options.add_argument("headless")
        options.add_argument("disable-extensions")
        options.add_argument("disable-notifications")
        options.add_argument("disable-infobars")
        options.add_argument("mute-audio")

        try:
           driver = webdriver.Chrome(
               executable_path=ChromeDriverManager().install(), options = options)
        except Exception:
            print("Error loading chrome webdriver " + sys.exc_info()[0])
            exit(1)
                
        driver.get("https://www.facebook.com/") 
        driver.maximize_window()
        #utils.cls()
        
        try:
            # New Facebook design has an annoying cookie banner.
            driver.find_element_by_css_selector(
                "button[data-cookiebanner=accept_button]"
            ).click()
        except NoSuchElementException:
            pass

        # filling the form
        driver.find_element_by_name("email").send_keys(email)
        driver.find_element_by_name("pass").send_keys(password)

        try:
            # clicking on login button
            driver.find_element_by_id("loginbutton").click()
        except NoSuchElementException:
            # Facebook new design
            driver.find_element_by_name("login").click()

        # there are so many screens asking you to verify things. Just skip them all
        while (
            utils.safe_find_element_by_id(driver, "checkpointSubmitButton") is not None
        ):
            dont_save_browser_radio = utils.safe_find_element_by_id(driver, "u_0_3")
            if dont_save_browser_radio is not None:
                dont_save_browser_radio.click()

            driver.find_element_by_id("checkpointSubmitButton").click()
            
    except Exception:
        print("There's some error in log in.")
        print(sys.exc_info()[0])
        exit(1)


def scrap_profile(user_id):
    # execute for all profiles given in input.txt file
    prefix = "https://www.facebook.com/"
    page:str = None
    if(user_id.isdigit()):
        page = prefix + "profile.php?id=" + user_id + "&sk=about_work_and_education"
    else:
        page = prefix + user_id + "/about_work_and_education"
    return scrape_data(page)

def scrape_data(page):    
    work_and_ed_path = "/html/body/div[1]/div/div[1]/div[1]/div[3]/div/div/div[1]/div[1]/div/div/div[4]/div/div/div/div[1]/div/div/div/div[2]"
    try:
        driver.get(page)
        work_ed_data = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, work_and_ed_path)))
        data_items = work_ed_data.find_elements_by_xpath("./div/div/div");
        return parse_data(data_items)
    except Exception:
        print(
        "Exception (scrape_work_and_education)",
         sys.exc_info()[0],
         )
    return None


def parse_data(data):
    result = {'works':[], 'education':[]}

    for work in data[0].find_elements_by_xpath("./div")[1:]:
        work = parse_work(work)
        if(work is not None):
            result['works'].append(work)        

    for univ in data[1].find_elements_by_xpath("./div")[1:]:
        univ = parse_university(univ)
        if(univ is not None):
            result['education'].append(univ)

    for school in data[2].find_elements_by_xpath("./div")[1:]:
        school = parse_school(school)
        if(school is not None):
            result['education'].append(school)
     
    return result

def parse_work(work_item):
    result = {}
    if(work_item.get_attribute('innerText') != "No workplaces to show"):
        work_info:str = work_item.find_element_by_xpath("./div/div/div[2]/div[1]"
                                                        ).get_attribute('innerText')
        index:int = work_info.rfind(" at ");
        key = work_info;
        if(index > 0):
            key = work_info[:index]
            work_info = work_info[index+4:]
        else:
            work_info = None
        result[key] = {"info" : None, "dt_start" : None, "dt_end" : None}
        result[key]["info"] = work_info
        try:
            work_info = work_item.find_element_by_xpath("./div/div/div[2]/div[2]/div/span[1]/span[1]"
                                                        ).get_attribute('innerText')
            if(utils.contains_year(work_info)):
                    work_info = work_info.split(" - ", 2)
                    result[key]["dt_start"] = work_info[0]
                    result[key]["dt_end"] = work_info[1]
            else:
                result[key]["info"] += " " + work_info
        except:
            pass
        try:
            work_info = work_item.find_element_by_xpath("./div/div/div[2]/div[2]/div/span[2]/span[1]"
                                                        ).get_attribute('innerText')
            result[key]["info"] += ", " + work_info
        except:
            pass
        return result
    return None

def parse_university(univ_item):
    result = {}
    if(univ_item.get_attribute('innerText') != "No schools/universities to show"):
        univ_info:str = univ_item.find_element_by_xpath("./div/div/div[2]/div[1]"
                                                        ).get_attribute('innerText')
        index:int = univ_info.rfind(" at ");
        key = univ_info;
        if(index > 0):
            key = univ_info[index + 4:]
            univ_info = univ_info[:index]
        else:
            univ_info = None
        result[key] = {"info" : None, "dt_start" : None, "dt_end" : None, "type" : "UNIVERSITY"}
        result[key]["info"] = univ_info
        try:
            univ_info = univ_item.find_element_by_xpath("./div/div/div[2]/div[2]/div/span[1]/span[1]"
                                                        ).get_attribute('innerText')
            if(utils.contains_year(univ_info)):
                if(univ_info.startswith("School year")):
                    result[key]["dt_end"]=univ_info[-4:]
                else:
                    univ_info = univ_info.split(" - ", 2)
                    result[key]["dt_start"] = univ_info[0]
                    result[key]["dt_end"] = univ_info[1]
            else:
                result[key]["info"] += " " + univ_info
        except:
            pass
        try:
            univ_info = univ_item.find_element_by_xpath("./div/div/div[2]/div[2]/div/span[2]/span[1]"
                                                        ).get_attribute('innerText')
            if(utils.contains_year(univ_info)):
                if(univ_info.startswith("School year")):
                    result[key]["dt_end"]=univ_info[-4:]
                else:
                    univ_info = univ_info.split(" - ", 2)
                    result[key]["dt_start"] = univ_info[0]
                    result[key]["dt_end"] = univ_info[1]
            else:
                result[key]["info"] += " " + univ_info
        except:
            pass
        return result
    return None

def parse_school(school_item):
    result = {}
    if(school_item.get_attribute('innerText') != "No schools/universities to show"):
        school_info:str = school_item.find_element_by_xpath("./div/div/div[2]/div[1]"
                                                            ).get_attribute('innerText')
        index:int = school_info.rfind(" to ");
        key = school_info;
        if(index > 0):
            key = school_info[index + 4:]
            school_info = school_info[:index]
        else:
            school_info = None
        result[key] = {"info" : None, "dt_start" : None, "dt_end" : None, "type" : "SCHOOL"}
        result[key]["info"] = school_info
        try:
            school_info = school_item.find_element_by_xpath(
                "./div/div/div[2]/div[2]/div/span[1]/span[1]").get_attribute('innerText')
            if(utils.contains_year(school_info)):
                if(school_info.startswith("School year")):
                    result[key]["dt_end"]=school_info[-4:]
                else:
                    school_info = school_info.split(" - ", 2)
                    result[key]["dt_start"] = school_info[0]
                    result[key]["dt_end"] = school_info[1]
            else:
                result[key]["info"] += " " + school_info
        except:
            pass
        try:
            school_info = school_item.find_element_by_xpath(
                "./div/div/div[2]/div[2]/div/span[2]/span[1]").get_attribute('innerText')
            result[key]["info"] += " " + school_info
        except:
            pass
        return result
    return None

def print_commands():
    print("C O M M A N D S")
    print("[-c] - data from console")
    print("[-clear] - clear console ouput")
    print("[-f] - data from file")
    print("[-h] - show commands")
    print("[-q] - exit")
    return

def show_console_menu():
    print_commands();
    while True:
        print("Enter command:", end = " ")
        command = input()
        if(command == "-c"):
            print("Enter ids in '' and split ',':", end = " ")
            ids = utils.read_from_console()
            try:
                scraper(ids)
            except Exception:
                print(
                    "Exception (show_console_menu)",
                    sys.exc_info()[0],
                    )
        elif(command == "-clear"):
            utils.cls();
        elif(command == "-f"):
            print("Enter file name:", end = " ")
            try:
                ids = utils.read_from_file(input())
                scraper(ids)
            except Exception:
                print(
                    "Exception (show_console_menu)",
                    sys.exc_info()[0],
                    )
        elif(command == "-h"):
            print_commands()
            print();
       
        elif(command == "-q"):
            break
        else:
            print("Unknown command")
    return

if __name__ == "__main__":
    driver = None
    show_console_menu()