import io
import json
import math
import os
import sqlite3
import time
import urllib.request
from datetime import datetime

import numpy as np
import progressbar
import requests

data = json.load(open("data.json"))


def retrieve_data():
    link = "https://opendata.ecdc.europa.eu/covid19/casedistribution/json/"
    print("Chargement des données")
    f = urllib.request.urlopen(link)
    Length = f.getheader('content-length')
    s = ""
    BlockSize = 2048

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
        prcm = a['Cumulative_number_for_14_days_of_COVID-19_cases_per_100000']
        prcm = prcm if prcm != "" else 0
        prcm = float(prcm)
        tag = a['countryterritoryCode']
        pop = a['popData2019']
        pop = pop if pop != None else 0
        inf = int(pop * prcm / 100000)
        if not  tag in countries:
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


def get_table_tag(tag):
    t = type(tag).__name__
    if t == "int":
        return "integer"
    if t == "str":
        return "string"
    if t == "float":
        return "real"


class Fonction:

    def __init__(self, R, A, K):
        self.R = R
        self.A = A
        self.K = K


    def calcul(self, x):
        return self.K / (1 + self.A * math.exp(self.R * x))


class Regression:

    def __init__(self, pts, f, min_pts):
        """ Régression linéaire de la simulation
        ---
        param :

            - pts (list(str, int)) la liste des points
            - f (fonction) la fonction de régression
            - min_pts (int) le nombre minimal de points pour le calcul de la régression
        """
        self.pts = pts
        self.f = f
        self.nb_pts = min(min_pts, len(pts))
        self.K = 0
        self.R = 0
        self.A = 0


    def get_function(self, pts):
        # TODO:
        """ Retourne la fonction la plus proche de la courbe de la simulation
        ---
        param :

            - pts (list) la liste des points de la courbe
        """
        self.K = pts[0][1] * 2
        self.R, self.A = self.regression()
        return self.f


    def delta_time_to_int(self, j):
        """ Calcul le nombre de jour entre deux date
        ---
        param :

            - pt (list(date, value)) le jour

        result :

            - int
        """
        t0 = datetime.strptime(pts[0][0].replace("-", ":"), "%Y:%m:%d")
        t = datetime.strptime(j[0].replace("-", ":"), "%Y:%m:%d")
        dt = t - t0
        return dt.day


    def sq_error(self):
        """ Calcul le carré de l'erreur
        ---
        result :

            - int
        """
        r = 0
        d = int(len(self.pts) / self.nb_pts)
        for x in range(self.nb_pts):
            r += (self.pts[x * d][1] - f(self.K, self.R, self.A, self.delta_time_to_int(self.pts[x * d])))**2
        return r


    def regression(self, minR, maxR, minA, maxA, nb_iteration):
        """ Calcul la régression de le courbe donnée
        ---
        param :

            - minR (int) la borne inférieure de R
            - maxR (int) la borne supérieure de R
            - minA (int) la borne inférieure de A
            - maxA (int) la borne supérieure de A
            - nb_iteration (int) le nombre d'itération de calcul

        result :

            - R, A (int, int)
        """
        minS = -1
        minCouple = (0,0)
        for _ in range(nb_iteration):
            dR = (maxR - minR) / 5
            dA = (maxA - minA) / 5
            for k in range(5):
                for n in range(5):
                    m = self.sq_error(pts, f, minR + k * dR, minA + n * dA)
                    if minS == -1 or minS > m:
                        minS = m
                        minCouple = (minR + k * dR, minA + n * dA)
            nR, nA = minCouple
            maxR = nR + dR
            minR = nR - dR
            maxA = nA + dA
            minA = nA - dA
        return minCouple


#data = retrieve_data()['records']
#save_data(data)
countries = extract_data(data)
json_to_sql(countries)

