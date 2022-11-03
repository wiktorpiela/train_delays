import sys, schedule, time
sys.path.insert(0, r"...\my_utils")
from my_utils import get_trains, scrape_data

get_trains()
schedule.every().day.at("08:00").do(get_trains)
schedule.every(0.01).minutes.do(lambda: scrape_data(r"....\scraper_8"))

while True:
    schedule.run_pending()
    time.sleep(1)
