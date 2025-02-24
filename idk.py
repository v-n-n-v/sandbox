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
import time
import requests
from time import sleep
from collections import defaultdict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Take a URL from stdin (prompt)
url = input("Enter a URL: ")

# If the URL contains "www.reddit.com", replace this substring with "old.reddit.com"
if "www.reddit.com" in url:
	url = url.replace("www.reddit.com", "old.reddit.com")

# Curl the URL and extract all links matching /https:\/\/monkeytype\.com\/profile\/[^>]+/ from the html
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
links = soup.find_all('a', href=re.compile(r'https:\/\/monkeytype\.com\/profile\/[^>]+'))

# Put them in a defaultdict as the first values; for each first value, the key is the username that appears in the nearest previous p.tagline > a.author
profiles = defaultdict(list)
for link in links:
	profile_url = link['href']
	author_tag = link.find_previous('p', class_='tagline').find('a', class_='author')
	username = author_tag.text if author_tag else 'unknown'
	profiles[username].append(profile_url)

# For each first value, use Selenium to browse to the monkeytype.com/profile url; wait until 'div[class=\'pbsTime\'] div:nth-child(3) div:nth-child(1) div:nth-child(2)' is visible AND contains numbers; extract its content and assign it as the second value in the defaultdict
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
for username, urls in profiles.items():
	profile_url = urls[0]
	driver.get(profile_url)
	sleep(1)
	try:
		wpm_element = WebDriverWait(driver, 10).until(
			EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.pbsTime div:nth-child(3) div:nth-child(1) div:nth-child(2)'))
		)
		wpm = wpm_element.text
		profiles[username].append(wpm)
	except Exception as e:
		profiles[username].append('N/A')
		print(f"Error fetching WPM for {username}: {e}")
driver.quit()



# Print the defaultdict as a json object
print(json.dumps(profiles, indent=4))

