import json
import os
import sqlite3
from datetime import datetime

import msgpack
import progressbar
import requests


class BarreDeProgression():

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


class RecuperationDesDonnees:

    def __init__(self):
        pass


    def save_data(self, output):
        """ Enregistre les données
        ---
        param :

            - output (dict)
        """
        with open("data.msgpack", "wb") as outfile:
            packed = msgpack.packb(output)
            outfile.write(packed)


    def json_to_sql(self, json):
        """ Enregistre dans une base de donnée les données fournies
        ---
        param :

            - json (dict)
        """
        filename = f"""Epidémie-COVID-{datetime.now().strftime("%Y:%m:%d").replace(":", "-")}.db"""
        if filename in os.listdir():
            os.remove(filename)
        data_base = sqlite3.connect(filename, check_same_thread=False)
        cursor = data_base.cursor()
        ex_tab = json[list(json.keys())[0]]['days'][0]
        tables_keys = ", ".join([f"{x.replace(' ', '_')} {self.get_table_tag(ex_tab[x])}" for x in [x for x in ex_tab]])
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


    def get_table_tag(self, tag):
        """ Donne l'équivalent SQLITE du type Python
        param :

            - tag (Object) : l'objet dont on veut avoir l'équivalent SQLITE

        result :

            - str
        """
        t = type(tag).__name__
        if t == "int":
            return "integer"
        if t == "str":
            return "string"
        if t == "float":
            return "real"


    def retrieve_data(self):
        """ Récupère les données du site
        ---
        result :

            - dict
        """
        link = "https://covid.ourworldindata.org/data/owid-covid-data.json"
        print("Chargement des données")
        total_size = ""
        headers = {
            'User-Agent':
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3', 'Accept-Encoding': 'none',
                'Accept-Language': 'en-US,en;q=0.8', 'Connection': 'keep-alive'}

        r = requests.get(link, headers=headers, stream=True)

        if 'Content-Length' in r.headers:
            total_size = int(r.headers['Content-Length'])

        s = ""
        Size = 0
        if total_size != "":
            pgb = progressbar.ProgressBar(maxval=total_size)

        for chunk in r.iter_content(1024 * 8):
            s += chunk.decode()
            Size += len(chunk)
            if total_size != "":
                pgb.update(Size)

        print("Données récupérées")

        return json.loads(s)


    def extract_data(self, data):
        """ Extrait les données utiles pour l'étude
        ---
        param :

            - data (dict)

        result :

            - dict
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


    def main(self):
        """ Fonction principale
        ---
        """
        data = self.retrieve_data()
        self.save_data(data)
        countries = self.extract_data(data)
        self.json_to_sql(countries)


RDD = RecuperationDesDonnees()
RDD.main()

