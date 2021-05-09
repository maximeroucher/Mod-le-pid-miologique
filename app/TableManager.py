import sqlite3
from tkinter import messagebox

import easygui

from Model import Model


class TableManager:

    def __init__(self, countries):
        """ Gestionnaire de base de donnée pour chager les données de la simulation
        ---
        param :

            - countries (list(Pays)) la liste des pays de la simulation
        """
        self.countries = countries
        self.connected = False
        self.models = []


    def get_CI(self):
        """ Retourne la liste des catégories de la simulation
        ---
        result :

            - list(str)
        """
        assert self.connected
        self.cursor.execute(f"select * from {self.table} where id=1")
        return [member[0] for member in self.cursor.description][1:]


    def sim_length(self, tag):
        """ Retourne la longueur de la liste des données du pays donné
        ---
        param :

            - tag (str) le tag du pays de la base de donnée

        result :

            - int
        """
        assert self.connected
        return self.cursor.execute(f"""SELECT COUNT(*) FROM {tag}""").fetchone()[0]


    def get_country_data_by_id(self, id, tag):
        """ Retourne les données associées au pays donné au jour odnt l'id est donné
        ---
        param :

            - id (int) l'id du jour
            - tag (str) le pays

        result :

            - tuple / None
        """
        assert self.connected
        try:
            return self.cursor.execute(f'Select * from {tag} where id = {id}').fetchone()[1:]
        except:
            return None


    def get_country_data_by_day(self, day, tag):
        """ Retourne les données associées au pays donné au jour donné
        ---
        param :

            - day (str) le jour
            - tag (str) le pays

        result :

            - tuple / None
        """
        assert self.connected
        try:
            return self.cursor.execute(f'Select * from {tag} where Date = "{day}"').fetchone()[1:]
        except Exception as e:
            return self.get_country_data_by_id(1, tag)


    def get_day_with_id(self, id, tag):
        """ Retourne le jour associé à l'id donnée dans la table donnée
        ---
        param :

            - id (int) l'id du jour
            - tag (str) le pays

        result :

            - str
        """
        assert self.connected
        return self.cursor.execute(f'Select Date from {tag} where id = {id}').fetchone()[0]


    def connect(self):
        """ Ouvre la fenêtre de sélection de la base de donnée et charge la base de donnée
        ---
        """
        f = easygui.fileopenbox("test", default=".", filetypes=["*.db"])
        if f:
            if not f.endswith(".db"):
                messagebox.showerror("Erreur", "L'extension du fichier n'est pas correcte")
                return False
            else:
                self.data_base = sqlite3.connect(f, check_same_thread=False)
                self.cursor = self.data_base.cursor()
                self.table = self.cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table';").fetchall()[-1][0]
                self.connected = True
                return True
        return False


    def is_in(self, tag):
        """ Vérifie que le pays donné est dans la base de donnée
        ---
        param :

            - tag (str) le pays

        result :

            - bool
        """
        try:
            self.cursor.execute(f'SELECT pays from name where tag = "{tag}"').fetchone()[0]
            return True
        except:
            return False


    def extract_model_from_db(self):
        """ Créer les modèles à partir des données chargées
        ---
        """
        for c in self.countries:
            if self.is_in(c.tag):
                self.models.append(Model(c, self))


    def end(self):
        """ Déconnecte le programme de la base de donnée
        ---
        """
        self.data_base.close()
