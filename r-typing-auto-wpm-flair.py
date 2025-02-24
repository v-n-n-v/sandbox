import re
import json
import praw
import requests
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from collections import defaultdict
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

url = input("Enter a URL: ")
if "www.reddit.com" in url:
    url = url.replace("www.reddit.com", "old.reddit.com")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')
links = soup.find_all('a', href=re.compile(r'https?://monkeytype\.com/profile/[-\w]+'))
link_hrefs = [link['href'] for link in links]

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
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.CSS_SELECTOR, 'div.pbsTime div:nth-child(3) div:nth-child(1) div:nth-child(2)')
        )

        def wpm_ready(d):
            try:
                error_elem = d.find_element(By.CSS_SELECTOR, 'div.error > div.message')
                if error_elem and "not found" in error_elem.text.lower():
                    return "USER NOT FOUND"
            except Exception:
                pass

            try:
                elem = d.find_element(By.CSS_SELECTOR, 'div.pbsTime div:nth-child(3) div:nth-child(1) div:nth-child(2)')
                return elem if re.search(r'\d+', elem.text) else False
            except Exception:
                return False

        result = WebDriverWait(driver, 10).until(wpm_ready)
        if isinstance(result, str):
            profiles[username].append(result)
        else:
            wpm = result.text
            profiles[username].append(wpm)

    except Exception as e:
        profiles[username].append('N/A')
        print(f"Error fetching WPM for {username}: {e}")
driver.quit()

#print(json.dumps(profiles, indent=4))

reddit = praw.Reddit(client_id='', # ID under "personal use script" on https://www.reddit.com/prefs/apps
                     client_secret='', # secret on https://www.reddit.com/prefs/apps
                     user_agent='', # e.g. "/r/typing auto WPM flair assigner 0.1, /u/854490, https://github.com/v-n-n-v/sandbox"
                     username='', # subreddit moderator username
                     password='') # subreddit moderator password

subreddit = reddit.subreddit('typing')

for username, data in profiles.items():
    if len(data) > 1 and re.search(r'\d+', data[1]):
        wpm = data[1]
        try:
            subreddit.flair.set(username, text=f"{wpm}wpm")
            print(f"Flair set for {username} to {wpm}wpm")
        except Exception as e:
            print(f"Error setting flair for {username}: {e}")
