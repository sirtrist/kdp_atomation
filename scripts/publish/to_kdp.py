import csv
import json
import os
import random
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoAlertPresentException

def pinterest_upload(gen:bool = True):

    # Setup du webdriver
    s = Service(ChromeDriverManager().install())
    options = Options()
    # options.add_argument("--headless")

    driver = webdriver.Chrome(service=s, options=options)
    wait = WebDriverWait(driver, 2000)  # attendez jusqu'à 10 secondes

    driver.get('https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fkdp.amazon.com%2Fbookshelf&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=amzn_dtp&openid.mode=checkid_setup&language=fr_FR&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&pageId=kdp-ap&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0')

    # driver.minimize_window()
    time.sleep(10000)

    directory = os.path.join(r'C:\Users\tr7to\OneDrive\Bureau\etsy_scripts\pinterest')

    credentials_path = os.path.join(directory, 'pinterest_credentials.json')

    with open(credentials_path, 'r') as f:
        credentials = json.load(f)

    email_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="email"]')))
    email_input.send_keys(credentials[str(1)]['email'])

    password_input = driver.find_element(By.XPATH, '//*[@id="password"]')
    password_input.send_keys(credentials[str(1)]['password'])

    login_btn = driver.find_element(By.XPATH, '//*[@id="mweb-unauth-container"]/div/div[3]/div/div/div[3]/form/div[7]/button')
    login_btn.click()

    time.sleep(10)
    # publish imae
    # count = 94
    count = random.randrange(0, 361)

    loop = True
    while loop:
        count += 1
        driver.refresh()
        driver.get('https://www.pinterest.fr/pin-creation-tool/')

        folder_path = os.path.join(directory, 'data_etsy', str(count).zfill(5))
        if not os.path.exists(folder_path):
            loop = False
            break

        num = 1
        if gen == True:
            image_path = os.path.join(folder_path, 'gen', f'gen_{num}.png')
        else:
            image_path = os.path.join(folder_path, f'image_{num}.jpg')

        # for pass folder with no image
        if not os.path.exists(image_path):
            count += 1
            folder_path = os.path.join(directory, 'data_etsy', str(count).zfill(5))

            if gen == True:
                image_path = os.path.join(folder_path, 'gen', f'gen_{num}.png')
            else:
                image_path = os.path.join(folder_path, f'image_{num}.jpg')

        # Check image size
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                if width < 200 or height < 300:
                    print(f"Image too small (size: {width}x{height}), skipping to next image.")
                    count += 1
                    folder_path = os.path.join(directory, 'data_etsy', str(count).zfill(5))

                    if gen == True:
                        image_path = os.path.join(folder_path, 'gen', f'gen_{num}.png')
                    else:
                        image_path = os.path.join(folder_path, 'image_0.jpg')
                    continue
        except Exception as e:
            print(f"Error opening image: {e}")
            continue

        try:
            alert = driver.switch_to.alert
            alert.accept()
        except NoAlertPresentException:
            pass

        time.sleep(2)
        image_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="storyboard-upload-input"]')))
        image_input.send_keys(image_path)

        # add link
        with open(os.path.join(folder_path, 'data.json'), 'r') as f:
            data = json.load(f)
        time.sleep(1)
        link_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="WebsiteField"]')))
        id = data['id']
        link_input.send_keys(f"https://www.etsy.com/listing/{id}/")

        # add tags
        for tag in range(10):
            text_to_click = random.choice(['crochet', 'tricot', 'etsy'])
            time.sleep(1)
            tag_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="storyboard-selector-interest-tags"]')))
            driver.execute_script("arguments[0].click();", tag_input)
            tag_input.send_keys(Keys.CONTROL + "a")
            tag_input.send_keys(Keys.DELETE)
            tag_input.send_keys(text_to_click)
            time.sleep(1)
            try:
                element_to_click = driver.find_element(By.XPATH, f"//*[contains(text(), '{text_to_click}')]")
                driver.execute_script("arguments[0].click();", element_to_click)
            except:
                tag_input.send_keys(Keys.CONTROL + "a")
                tag_input.send_keys(Keys.DELETE)

        time.sleep(1)

        publish = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="__PWS_ROOT__"]/div/div[1]/div/div[2]/div/div/div/div[2]/div[3]/div/div/div[2]/div[4]/div[2]/div/button')))
        driver.execute_script("arguments[0].click();", publish)

        time.sleep(2)

pinterest_upload(False)
 