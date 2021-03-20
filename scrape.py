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

# DataFrame for new Tesla Data
newdata = pd.DataFrame(
    {
        "link": [],
        "date": [],
        "id": [],
        "category": [],
        "location": [],
    }
)

# get date
today = datetime.datetime.now()

# find all links which contain "job"
links = soup.find_all(href=re.compile("job"))

# extract data for each row and add it to DataFrame
for link in links:
   
   linktext = link.get("href")

   td = link.find_parent("td")
   category = td.find_next_sibling("td")
   location = category.find_next_sibling("td")
   #date = location.find_next_sibling("td") ->has been removed by Tesla

   L = len(linktext)
   idstring = linktext[L-5]+linktext[L-4]+linktext[L-3]+linktext[L-2]+linktext[L-1]

   datatemp = pd.DataFrame(
        {
           "link": ["https://www.tesla.com"+str(linktext)],
           "date": [today.strftime("%Y-%m-%d")],
           "id": [int(idstring)],
           "category": [str(category.string)],
           "location": [str(location.string)],
        }
   )

   newdata = pd.concat([newdata,datatemp], ignore_index=True, sort=False)

# Close the browser
driver.quit()

# DataFrame for old Tesla Data
yesterday = today - datetime.timedelta(days=1)
olddata = pd.read_csv("gigacareersdata/"+yesterday.strftime("%Y-%m-%d")+"-giga_careers.csv")

# transfer date from old to new data
for row in newdata.itertuples():
    if olddata.id.isin([row[3]]).any(): # check if newdata ID (in 4th position) is also in olddata
        olddate = olddata.loc[olddata['id']==row[3], "date"].iloc[0]
        newdata.loc[newdata['id']==row[3], "date"] = olddate
        
# sort by date
#newdata["date"] = pd.to_datetime(newdata["date"], dayfirst=True)
newdata = newdata.sort_values(by="date", ascending=False)

# count how many times a date appears (= number of jobs per day)
#dfc = df["date"].value_counts().rename_axis("countdates").reset_index(name="counts")

#df = pd.concat([df, dfc.reindex(df.index)], axis=1)

# save to csv file with current date
newdata.to_csv("gigacareersdata/" + today.strftime("%Y-%m-%d") + "-giga_careers.csv")

# save to html file
text = "Changes: as of 2021-03-20 Tesla doesn't put dates anymore, so I am adding them every day for the new IDs<br><br>\n Last updated on "+today.strftime("%c")+" from <a href=""https://www.tesla.com/de_DE/careers/search/?country=DE&location=Gr%C3%BCnheide%20(Gigafactory%20Berlin)&region=3"">https://www.tesla.com/de_DE/careers/search/?country=DE&location=Gr%C3%BCnheide%20(Gigafactory%20Berlin)&region=3</a><br><br>\n"

html = newdata.to_html(columns=["link","date","id","category","location"], float_format="{0:.0f}".format, index=False, justify="center", render_links=True)

f = open("giga_careers.html", "w")
f.write(text+html)
f.close()