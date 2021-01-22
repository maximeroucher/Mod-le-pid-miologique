import json
import os
import sqlite3
import urllib.request
from datetime import datetime

import progressbar
import requests

data2 = json.load(open("data2.json", 'r', encoding='utf-8'))


def retrieve_data():
    link = "https://opendata.ecdc.europa.eu/covid19/casedistribution/json/"
    print("Chargement des données")
    f = urllib.request.urlopen(link)
    Length = f.getheader('content-length')
    s = ""
    BlockSize = 1024

    if Length:
        Length = int(Length)
        pgb = progressbar.ProgressBar(maxval=Length)

    Size = 0
    while True:
        BufferNow = f.read(BlockSize)
        if not BufferNow:
            break
        s += BufferNow.decode()
        Size += len(BufferNow)
        if Length:
            Percent = int((Size / Length) * 100)
            pgb.update(Size)

    print("Données récupérées")
    return json.loads(s)


def save_data(output):
    json.dump(output, open("data.json", "w"))


def extract_data(data):
    countries = {}
    for x in range(len(data) - 1, -1, -1):
        a = data[x]
        day_track = {}
        day_track['Date'] = a['dateRep']
        prcm = a['notification_rate_per_100000_population_14-days']
        prcm = prcm if prcm != "" else 0
        prcm = float(prcm)
        tag = a['countryterritoryCode']
        pop = a['popData2019']
        pop = pop if pop != None else 0
        inf = int(pop * prcm / 100000)
        if not  tag in countries:
            countries[tag] = {"pop": pop, 'days': [], 'name' : a['countriesAndTerritories']}
            morts = a['deaths_weekly']
            ret = cas = 0
        else:
            morts = a['deaths_weekly'] + countries[tag]['days'][-1]['Morts']
            cas = countries[tag]['days'][-1]['Total_cas'] + a['cases_weekly']
            ret = cas - inf - morts
        day_track['Total_cas'] = cas
        day_track['Infetés'] = inf
        day_track['Rétablis'] = ret
        day_track['Sains'] = pop - inf
        day_track['Morts'] = morts
        countries[tag]['days'].append(day_track)
    return countries


def json_to_sql(json):
    filename = f"""out-{datetime.now().strftime("%Y:%m:%d").replace(":", "-")}.db"""
    if filename in os.listdir():
        os.remove(filename)
    data_base = sqlite3.connect(filename, check_same_thread=False)
    cursor = data_base.cursor()
    ex_tab = json[list(json.keys())[0]]['days'][0]
    tables_keys = ", ".join([f"{x.replace(' ', '_')} {get_table_tag(ex_tab[x])}" for x in [x for x in ex_tab]])
    cursor.execute("""CREATE TABLE IF NOT EXISTS name (id integer PRIMARY KEY, tag string, pays string)""")
    for model in json:
        if model is not None and len(model) == 3:
            cursor.execute(f"INSERT INTO name VALUES (NULL, ?, ?)", [model, json[model]['name']])
            cursor.execute(
                f"""CREATE TABLE IF NOT EXISTS "{model}" (id integer PRIMARY KEY, {tables_keys})""")
            for m in json[model]['days']:
                params = ", ".join(['?' for n in range(len(m.keys()))])
                cursor.execute(f"""INSERT INTO "{model}" VALUES (NULL, {params})""", [m[x] for x in list(m.keys())])
    data_base.commit()
    data_base.close()


def get_table_tag(tag):
    t = type(tag).__name__
    if t == "int":
        return "integer"
    if t == "str":
        return "string"
    if t == "float":
        return "real"


class MyProgressBar():

    def __init__(self):
        self.pbar = None

    def __call__(self, block_num, block_size, total_size):
        if not self.pbar:
            self.pbar = progressbar.ProgressBar(maxval=total_size)
            self.pbar.start()

        downloaded = block_num * block_size
        if downloaded < total_size:
            self.pbar.update(downloaded)
        else:
            self.pbar.finish()


def retrieve_data2():
    urllib.request.urlretrieve("https://opendata.ecdc.europa.eu/covid19/subnationalcasedaily/json/",
                       "data2.json", MyProgressBar())


def extract_data2(data):
    countries = {}
    for x in data:
        if not x["country"] in countries:
            countries[x["country"]] = {}
            print(x["country"])
        if not x["date"] in countries[x["country"]]:
            countries[x["country"]][x["date"]] = 0
        nb = x.get("rate_14_day_per_100k")
        if nb != None:
            countries[x["country"]][x["date"]] += int(nb * 100000)
    return countries


data2 = retrieve_data2()
print(extract_data2(data2)['Austria'])

#data = retrieve_data()['records']
save_data(data)

countries = extract_data(data)
json_to_sql(countries)

