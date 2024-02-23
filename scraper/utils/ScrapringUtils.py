import os, schedule, time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from urllib.error import URLError

global city_ids
city_ids = pd.read_csv(r"../data/big_cities_dict.csv").iloc[:, 1].to_list()

def get_trains():
    global scraping_schedule_list
    all_links = []

    for i in city_ids:
        html_page = urlopen(Request("https://infopasazer.intercity.pl/?p=station&id=" + str(i)))
        content = BeautifulSoup(html_page)

        links = []
        for link in content.findAll("a"):
            if len(link) > 0 and link.get("href")[-9:].isnumeric():
                links.append("https://infopasazer.intercity.pl/" + link.get("href"))

        all_links.append(list(set(links)))

    all_links = list(set([subitem for item in all_links for subitem in item]))

    plan_arrive = []
    for x in range(len(all_links)):
        start_date = pd.to_datetime(
            pd.read_html(all_links[x])[0].iloc[1, 1] + " " + pd.read_html(all_links[x])[0].iloc[1, 4], dayfirst=True)
        end_date = pd.to_datetime(
            pd.read_html(all_links[x])[0].iloc[-1, 1] + " " + pd.read_html(all_links[x])[0].iloc[-1, 4], dayfirst=True)

        if (end_date - start_date).days == -1:
            plan_arrive.append((end_date + timedelta(hours=24)))
        else:
            plan_arrive.append(end_date)

    temp_table_sorted = pd.DataFrame(zip(all_links, plan_arrive), columns=("href", "arrive_date"))

    for x in range(len(temp_table_sorted)):
        temp_table_sorted.iloc[x, 1] = temp_table_sorted.iloc[x, 1] + timedelta(
            seconds=int(np.random.choice(np.arange(-55, 60, 2))))

    temp_table_sorted = temp_table_sorted[
        (temp_table_sorted["arrive_date"] > datetime.now()) &
        (temp_table_sorted["arrive_date"] < datetime.now() + timedelta(hours=24))] \
        .sort_values("arrive_date") \
        .assign(arrive_date=lambda x: x["arrive_date"].dt.strftime("%d.%m.%Y %H:%M:%S"))

    scraping_schedule_list = list(zip(temp_table_sorted["href"].to_list(), temp_table_sorted["arrive_date"].to_list()))

    return scraping_schedule_list


def scrape_data(path):
    try:
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        time_to_save = current_time \
            .replace(".", "") \
            .replace(":", "")
        rand_suffix = str(np.random.choice(np.arange(0, 10000), 1).item())

        for x in scraping_schedule_list:
            runTime = x[1]
            if x and current_time == str(runTime):
                pd.read_html(x[0])[0] \
                    .to_parquet(fr"{path}\data\save_{time_to_save}_file_{rand_suffix}.parquet", index=False)
    except ValueError as e1:
        print(e1)
        pass
    except URLError as e2:
        print(e2)
        pass


def get_scraped_data():
    # global data
    import os
    import pandas as pd
    import numpy as np

    parent_path = os.getcwd() + "\\02_data_scraping"
    subfolders = [item for item in next(os.walk(parent_path))[1] if "scraper_" in item]
    data_folders = "data"

    folders = []
    for x in range(len(subfolders)):
        folders.append(os.path.join(parent_path, subfolders[x], data_folders))

    files = []
    for x in range(len(folders)):
        files.append(os.listdir(folders[x]))

    for x in range(len(folders)):
        folders[x] = np.repeat(folders[x], len(files[x]))

    full_paths = []
    for x in range(len(folders)):
        for y in range(len(folders[x])):
            full_paths.append("\\".join(list(zip(folders[x], files[x]))[y]))

    dfs = []

    for file in full_paths:
        dfs.append(pd.read_parquet(file))

    # data = pd.concat(dfs)
    return pd.concat(dfs)


def save_df_list(df_list, path, filename):
    f = open(path + "\\" + filename, "a")
    for df in df_list:
        df.to_csv(f, index=False)
    f.close()


def split_frames(frame_to_split):
    header = list(frame_to_split.columns)
    header_index = [0]

    for row in range(len(frame_to_split)):
        if frame_to_split.iloc[row].values.tolist() == header:
            header_index.append(row)

    splitted_dfs = []

    for x in range(len(header_index)):
        # first iter
        if x == 0:
            temp_df = frame_to_split.iloc[header_index[x]:header_index[x + 1]]
        # last iter
        elif x == len(header_index) - 1:
            temp_df = frame_to_split.iloc[header_index[x] + 1:len(frame_to_split)]
        else:
            temp_df = frame_to_split.iloc[header_index[x] + 1:header_index[x + 1]]

        splitted_dfs.append(temp_df)

    return splitted_dfs
