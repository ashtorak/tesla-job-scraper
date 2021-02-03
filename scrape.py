import os
import time
import datetime
import re
import pandas as pd

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

#function for scrolling through webpage with Selenium
def scroll(driver, timeout):
    scroll_pause_time = timeout

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(scroll_pause_time)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # If heights are the same it will exit the function
            break
        last_height = new_height


# Instantiate an Options object
# and add the “ — headless” argument
opts = Options()
opts.add_argument(" — headless")

# If necessary set the path to you browser’s location
opts.binary_location= "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

# Set the location of the webdriver
chrome_driver = os.getcwd() +"\\chromedriver.exe"

# Instantiate a webdriver
driver = webdriver.Chrome(options=opts, executable_path=chrome_driver)

# Load the HTML page
driver.get("https://www.tesla.com/de_DE/careers/search/?country=DE&location=Grünheide (Gigafactory Berlin)&region=3")

# scroll through it to load all elements
scroll(driver, 0.2) # time in floating point seconds

# Put the page source into a variable and create a BS object from it
soup_file=driver.page_source
soup = BeautifulSoup(soup_file, features="lxml")

# DataFrame for Tesla Data

df = pd.DataFrame(
    {
        "link": [],
        "category": [],
        "location": [],
        "id": [],
        "date": [],
    }
)

# find all links which contain "job"
links = soup.find_all(href=re.compile("job"))

# extract data for each row and add it to DataFrame
for link in links:
   
   linktext = link.get("href")

   td = link.find_parent("td")
   category = td.find_next_sibling("td")
   location = category.find_next_sibling("td")
   date = location.find_next_sibling("td")

   L = len(linktext)
   idstring = linktext[L-5]+linktext[L-4]+linktext[L-3]+linktext[L-2]+linktext[L-1]

   dftemp = pd.DataFrame(
        {
           "link": ["https://www.tesla.com"+str(linktext)],
           "category": [str(category.string)],
           "location": [str(location.string)],
           "id": [int(idstring)],
           "date": [str(date.string)],
        }
   )

   df = pd.concat([df,dftemp], ignore_index=True, sort=False)

# Close the browser
driver.quit()

# sort by date
df["date"] = pd.to_datetime(df["date"], dayfirst=True)
df = df.sort_values(by="date", ascending=False)

# count how many times a date appears (= number of jobs per day)
dfc = df["date"].value_counts().rename_axis("countdates").reset_index(name="counts")

df = pd.concat([df, dfc.reindex(df.index)], axis=1)

# save to csv file with current date
dt = datetime.datetime.now()
df.to_csv(dt.strftime("%Y")+"-"+dt.strftime("%m")+"-"+dt.strftime("%d")+"-"+"giga_careers.csv")
