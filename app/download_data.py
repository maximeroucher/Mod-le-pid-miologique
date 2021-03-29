import json
import msgpack
import os
import sqlite3
import urllib.request
from datetime import datetime

import progressbar

#data2 = json.load(open("data2.json", 'r', encoding='utf-8'))


def retrieve_data():
    """ Récupère les données du site
    ---
    result :

        - dict
    """
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
    """ Enregistre les données
    ---
    param :

        - output (dict)
    """
    with open("data.msgpack", "wb") as outfile:
        packed = msgpack.packb(output)
        outfile.write(packed)


def extract_data(data):
    """ Extrait les données utiles pour l'étude
    ---
    param :

        - data (dict)
    """
    countries = {}
    for x in range(len(data) - 1, -1, -1):
        a = data[x]
        day_track = {}
        day_track['Date'] = a['dateRep']
        prcm = a['Cumulative_number_for_14_days_of_COVID-19_cases_per_100000']
        prcm = prcm if prcm != "" else 0
        prcm = float(prcm)
        tag = a['countryterritoryCode']
        pop = a['popData2019']
        pop = pop if pop != None else 0
        inf = int(pop * prcm / 100000)
        if not tag in countries:
            countries[tag] = {"pop": pop, 'days': [], 'name' : a['countriesAndTerritories']}
            morts = a['deaths']
            ret = cas = 0
        else:
            morts = a['deaths'] + countries[tag]['days'][-1]['Morts']
            cas = countries[tag]['days'][-1]['Total_cas'] + a['cases']
            ret = cas - inf - morts
        day_track['Total_cas'] = cas
        day_track['Infetés'] = inf
        day_track['Rétablis'] = ret
        day_track['Sains'] = pop - inf
        day_track['Morts'] = morts
        countries[tag]['days'].append(day_track)
    return countries


def json_to_sql(json):
    """ Enregistre dans une base de donnée les données fournies
    ---
    param :

        - json (dict)
    """
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
    """ Donne l'équivalent SQLITE du type Python
    """
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
    """ Récupère les données du site
    ---
    result :

        - dict
    """
    link = "https://covid.ourworldindata.org/data/owid-covid-data.json"
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


def extract_data2(data):
    """ Extrait les données utiles pour l'étude
    ---
    param :

        - data (dict)
    """
    countries = {}
    keys = list(data.keys())
    for k in keys:
        d = data[k]
        p = d.get('population')
        if p is not None:
            pop = int(d['population'])
            countries[k] = {"pop": pop, 'days': [], 'name': d['location']}
            inf_mem = []
            d = d['data']
            for i in range(len(d)):
                day_track = {}
                day_track['Date'] = d[i]['date']
                t = d[i].get('new_cases_smoothed_per_million')
                m = d[i].get('new_deaths_smoothed_per_million')
                r = d[i].get('total_cases')
                inf =  int(t  * p / 1000000) if t is not None else 0
                inf_mem.append(inf)
                ttl = int(r) if r is not None else 0
                sns = int(pop - t * p / 1000000) if t is not None else pop
                mrt = int(m * p / 1000000) if m is not None else 0
                if i != 0:
                    mrt += countries[k]['days'][i - 1]['Morts']
                    inf += countries[k]['days'][i - 1]['Infectés']
                if i > 14: #Approx°
                    inf -= inf_mem.pop(0)
                ret = int(ttl - inf)
                day_track['Total_cas'] = ttl
                day_track['Infectés'] = inf
                day_track['Rétablis'] = ret
                day_track['Sains'] = sns
                day_track['Morts'] = mrt
                countries[k]['days'].append(day_track)
    return countries


#data = retrieve_data()['records']
data = retrieve_data2()
save_data(data)
#data = json.load(open("data.json", 'r', encoding='utf-8'))
countries = extract_data2(data)
json_to_sql(countries)

