import os, schedule, time, string
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

city_ids = pd.read_excel(r"../miasta_slownik.xlsx")\
    .iloc[:,1]\
        .to_list()

def get_trains():
    
    global scraping_schedule_list
    
    all_links = []

    for i in city_ids:
        html_page = urlopen(Request("https://infopasazer.intercity.pl/?p=station&id="+str(i)))
        content = BeautifulSoup(html_page)

        links = []
        for link in content.findAll("a"):
            if len(link)>0 and link.get("href")[-9:].isnumeric():
                links.append("https://infopasazer.intercity.pl/"+link.get("href"))
            
        all_links.append(list(set(links)))
    
    all_links = list(set([subitem for item in all_links for subitem in item]))

    plan_arrive = []
    for x in range(len(all_links)):
        start_date = pd.to_datetime(pd.read_html(all_links[x])[0].iloc[1,1]+" "+pd.read_html(all_links[x])[0].iloc[1,4])
        end_date = pd.to_datetime(pd.read_html(all_links[x])[0].iloc[-1,1]+" "+pd.read_html(all_links[x])[0].iloc[-1,4])
    
        if (end_date-start_date).days == -1:
            plan_arrive.append((end_date+timedelta(hours=24)).strftime("%d.%m.%Y %H:%M:%S"))
        else:
            plan_arrive.append(end_date.strftime("%d.%m.%Y %H:%M:%S"))
    
    temp_table_sorted = pd.DataFrame(zip(all_links,plan_arrive),columns=("href","arrive_date"))
    
    for x in range(len(temp_table_sorted)):
        temp_table_sorted.iloc[x,1] = (pd.to_datetime(temp_table_sorted.iloc[x,1]) + timedelta(seconds=int(np.random.choice(np.arange(-55,60,2))))).strftime("%d.%m.%Y %H:%M:%S")
        
    temp_table_sorted = temp_table_sorted[
        (pd.to_datetime(temp_table_sorted["arrive_date"])>datetime.now()) &
        (pd.to_datetime(temp_table_sorted["arrive_date"])<datetime.now()+timedelta(hours=24))]\
            .sort_values("arrive_date")
    
    scraping_schedule_list = list(zip(temp_table_sorted["href"].to_list(),temp_table_sorted["arrive_date"].to_list()))
    
    return scraping_schedule_list

def scrape_data():
    try:
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        time_to_save = current_time\
            .replace(".","")\
            .replace(":","")
        rand_suffix = str(np.random.choice(np.arange(0,10000),1).item())
    
        for x in scraping_schedule_list:
            runTime = x[1]
            if x and current_time == str(runTime):
                pd.read_html(x[0])[0]\
                    .to_parquet(fr"...\data\save_{time_to_save}_file_{rand_suffix}.parquet",index=False)
    except ValueError:
        pass

get_trains()
schedule.every().day.at("10:00").do(get_trains)
schedule.every(0.01).minutes.do(scrape_data)

while True:
    schedule.run_pending()
    time.sleep(1)
