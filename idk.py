# Take a URL from stdin (prompt)
# If the URL contains "www.reddit.com", replace this substring with "old.reddit.com"
# Curl the URL and extract all links matching /https:\/\/monkeytype\.com\/profile\/[^>]+/ from the html; 
# put them in a defaultdict as the first values; 
# for each first value, the key is the username that appears in the nearest previous p.tagline > a.author 
# For each first value, use Selenium to browse to the monkeytype.com/profile url;
# wait until 'div[class=\'pbsTime\'] div:nth-child(3) div:nth-child(1) div:nth-child(2)' is visible AND contains numbers;
# assign this value as the second value in the defaultdict
# Print the defaultdict as a json object

import re
import json
import requests
from time import sleep
from collections import defaultdict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait

# Grab the URL, swap to old.reddit.com if needed
url = input("Enter a URL: ")
if "www.reddit.com" in url:
    url = url.replace("www.reddit.com", "old.reddit.com")

response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
links = soup.find_all('a', href=re.compile(r'https:\/\/monkeytype\.com\/profile\/[^>]+'))

# Build a dict: username -> [profile_url]
profiles = defaultdict(list)
for link in links:
    profile_url = link['href']
    author_tag = link.find_previous('p', class_='tagline').find('a', class_='author')
    username = author_tag.text if author_tag else 'unknown'
    profiles[username].append(profile_url)

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
for username, urls in profiles.items():
    profile_url = urls[0]
    driver.get(profile_url)
    sleep(1)
    try:
        # Wait until the target element is on the page...
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.CSS_SELECTOR, 'div.pbsTime div:nth-child(3) div:nth-child(1) div:nth-child(2)')
        )

        # Then wait until its text matches a number (i.e. contains at least one digit)
        def wpm_ready(d):
            try:
                elem = d.find_element(By.CSS_SELECTOR, 'div.pbsTime div:nth-child(3) div:nth-child(1) div:nth-child(2)')
                return elem if re.search(r'\d+', elem.text) else False
            except Exception:
                return False

        wpm_element = WebDriverWait(driver, 10).until(wpm_ready)
        wpm = wpm_element.text
        profiles[username].append(wpm)
    except Exception as e:
        profiles[username].append('N/A')
        print(f"Error fetching WPM for {username}: {e}")
driver.quit()

print(json.dumps(profiles, indent=4))

# --- Reddit API integration stub ---
# When you're ready to assign flairs, you can use PRAW.
# The idea is to iterate over the profiles dict and, for users with a valid numeric WPM,
# call the subreddit.flair.set() method to update their flair.
#
# import praw
#
# reddit = praw.Reddit(client_id='your_client_id',
#                      client_secret='your_client_secret',
#                      user_agent='your_user_agent',
#                      username='your_mod_username',
#                      password='your_mod_password')
#
# subreddit = reddit.subreddit('your_subreddit')
#
# for username, data in profiles.items():
#     if len(data) > 1 and re.search(r'\d+', data[1]):
#         wpm = data[1]
#         try:
#             subreddit.flair.set(username, text=f"{wpm} WPM")
#             print(f"Flair set for {username} to {wpm} WPM")
#         except Exception as e:
#             print(f"Error setting flair for {username}: {e}")
