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


    def __call__(self, numero_bloc, taille_bloc, taille_totale):
        """ On met à jour la barre de progression
        ---
        paramètres :

            - numero_bloc (int)
            - taille_bloc (int)
            - taille_totale (int)
        """
        # Créer la barre de progression si elle n'existe pas
        if not self.pbar:
            self.pbar = progressbar.ProgressBar(maxval=taille_totale)
            self.pbar.start()

        # la portion téléchargée
        deja_telecharge = numero_bloc * taille_bloc
        # On met à jour ou on arrête si c'est fini
        if deja_telecharge < taille_totale:
            self.pbar.update(deja_telecharge)
        else:
            self.pbar.finish()


class RecuperationDesDonnees:

    def __init__(self):
        pass


    def enregistrer_donnees(self, donnees):
        """ Enregistre les données
        ---
        paramètre :

            - donnees (dict)
        """
        fichier = open("donnees.msgpack", "wb")
        donnees_binaires = msgpack.packb(donnees)
        fichier.write(donnees_binaires)


    def json_vers_sql(self, json):
        """ Enregistre dans une base de donnée les données fournies
        ---
        paramètre :

            - json (dict)
        """
        # Le nom de la base de donnée
        filename = f"""Epidémie-COVID-{datetime.now().strftime("%Y:%m:%d").replace(":", "-")}.db"""
        # On supprime le fichier si il existe
        if filename in os.listdir():
            os.remove(filename)
        # On se connecte à la base de donnée
        bdd = sqlite3.connect(filename, check_same_thread=False)
        curseur = bdd.cursor()
        # On récupère les clées des tables
        ex_tab = json[list(json.keys())[0]]['days'][0]
        # On construit la liste de clées de la requête SQL pour créer une table pour chaque pays
        table_clee = ", ".join([f"{x.replace(' ', '_')} {self.clee_sql_depuis_type(ex_tab[x])}" for x in [x for x in ex_tab]])
        # On Crée une table pour enregistrer le nom et le tag de chaque pays
        curseur.execute("""CREATE TABLE IF NOT EXISTS name (id integer PRIMARY KEY, tag string, pays string)""")
        # On itère sur chaque pays
        for pays in json:
            # Si on a toutes les informations nécessaires
            if pays is not None and len(pays) == 3:
                # On ajoute le pays dans la table name
                curseur.execute(f"INSERT INTO name VALUES (NULL, ?, ?)", [pays, json[pays]['name']])
                # On crée une table qui contiendra les informations données
                curseur.execute(
                    f"""CREATE TABLE IF NOT EXISTS "{pays}" (id integer PRIMARY KEY, {table_clee})""")
                # Pour chaque jour
                for m in json[pays]['days']:
                    # On enregistre les données du jour
                    parametres = ", ".join(['?' for n in range(len(m.keys()))])
                    curseur.execute(f"""INSERT INTO "{pays}" VALUES (NULL, {parametres})""", [m[x] for x in list(m.keys())])

        # On exécute la requête et on ferme la base de donnée
        bdd.commit()
        bdd.close()


    def clee_sql_depuis_type(self, tag):
        """ Donne l'équivalent SQLITE du type Python
        paramètre :

            - tag (Object) : l'objet dont on veut avoir l'équivalent SQLITE

        résultat :

            - str
        """
        t = type(tag).__name__
        if t == "int":
            return "integer"
        if t == "str":
            return "string"
        if t == "float":
            return "real"


    def recuperer_donnees(self):
        """ Récupère les données du site
        ---
        résultat :

            - dict
        """
        # Le lien d'où sont extraites les informations
        url = "https://covid.ourworldindata.org/data/owid-covid-data.json"
        print("Chargement des données")
        # On va faire passer la requête pour une requête faite depuis une utilisateur humain
        en_tete = {
            'User-Agent':
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3', 'Accept-Encoding': 'none',
                'Accept-Language': 'en-US,en;q=0.8', 'Connection': 'keep-alive'}

        # On récupère la réponse du site
        resp = requests.get(url, headers=en_tete, stream=True)

        # Le texte contenant les données
        texte = ""
        taille = 0

        # On récupère les données par paquets de 8 192 octets
        for partie in resp.iter_content(8192):
            # On les convertit en texte
            texte += partie.decode()
            taille += len(partie)
            print(taille, end='\r')

        print("Données récupérées")

        # On convetit les donnée en un dictionnaire
        return json.loads(texte)


    def extraire_donnees(self, donnees):
        """ Extrait les données utiles pour l'étude
        ---
        paramètre :

            - donnees (dict)

        résultat :

            - dict
        """
        # Le dictionnaire contenant les données pour chaque pays
        countries = {}
        # Les pays
        keys = list(donnees.keys())
        for k in keys:
            # Les données concernant ce pays
            d = donnees[k]
            # La population
            p = d.get('population')
            # Certain territoires des données n'int pas d'habitant
            if p is not None:
                pop = int(d['population'])
                # Le dictionnaire des données du pays
                countries[k] = {"pop": pop, 'days': [], 'name': d['location']}
                # Le tableau contenant le nombre de nouveaux infectés les 14 derniers jours
                inf_mem = []
                d = d['data']
                # Pour chaque jour
                for i in range(len(d)):
                    # Le dictionnaire des données du jour
                    day_track = {}
                    # On rensaigne la date
                    day_track['Date'] = d[i]['date']
                    # le nombre de nouveaux cas
                    t = d[i].get('new_cases_smoothed_per_million')
                    # Le nombre de nouveaux décès
                    m = d[i].get('new_deaths_smoothed_per_million')
                    # Le nombre total de cas
                    r = d[i].get('total_cases')
                    # Les informatios sont soit données en pour un million soit non renseignées
                    inf =  int(t  * p / 1000000) if t is not None else 0
                    # On enregistre le nombre de nouvelle personnes infectées
                    inf_mem.append(inf)
                    # On corrige le nombre total de cas depuis le début de la pandémie
                    ttl = int(r) if r is not None else 0
                    # On calcule le nombre de personnes saines
                    sns = int(pop - t * p / 1000000) if t is not None else pop
                    # On corrige le nombre de décès
                    mrt = int(m * p / 1000000) if m is not None else 0
                    # On calcul le nombre total de décès et d'infectés en fonction des données du jour précédent
                    if i != 0:
                        mrt += countries[k]['days'][i - 1]['Morts']
                        inf += countries[k]['days'][i - 1]['Infectés']
                    # En approximant le durée de l'infection à 14 jour, oncorrige le nombre caculé juste avant en retirant le nombre de cas datant de plus de 14 jours
                    if i > 14:
                        inf -= inf_mem.pop(0)
                    # On en déduit le nombre de personnes rétablies
                    ret = int(ttl - inf)
                    # On renseigne les informations dans le dictionnaire
                    day_track['Total_cas'] = ttl
                    day_track['Infectés'] = inf
                    day_track['Rétablis'] = ret
                    day_track['Sains'] = sns
                    day_track['Morts'] = mrt
                    # On ajoute le dictionnaire du jour à la liste des dicionnaires des jours
                    countries[k]['days'].append(day_track)
        return countries


    def lancer(self):
        """ La fonction principale
        ---
        """
        donnees = self.recuperer_donnees()
        self.enregistrer_donnees(donnees)
        countries = self.extraire_donnees(donnees)
        self.json_vers_sql(countries)


RDD = RecuperationDesDonnees()
RDD.lancer()
