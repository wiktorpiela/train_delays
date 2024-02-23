import schedule, time
from utils.ScrapringUtils import get_trains, scrape_data

get_trains()
schedule.every().day.at("00:00").do(get_trains)
schedule.every(0.01).minutes.do(lambda: scrape_data('../data/scraper_data'))

while True:
    schedule.run_pending()
    time.sleep(1)