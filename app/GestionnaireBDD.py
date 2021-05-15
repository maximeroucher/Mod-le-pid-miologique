import sqlite3
from tkinter import messagebox

import easygui

from Modele import Modele
from outils import trouverBdd


class GestionnaireBDD:

    def __init__(self, liste_pays):
        """ Gestionnaire de base de donnée pour chager les données de la simulation
        ---
        paramètres :

            - liste_pays (list(Pays)) la liste des pays de la simulation
        """
        self.liste_pays = liste_pays
        self.connecte = False
        self.liste_modeles = []


    def liste_clee(self):
        """ Retourne la liste des catégories de la simulation
        ---
        résultat :

            - list(str)
        """
        self.curseur.execute(f"select * from {self.table} where id=1")
        return [k[0] for k in self.curseur.description][1:]


    def taille_donnees(self, tag):
        """ Retourne la longueur de la liste des données du pays donné
        ---
        paramètres :

            - tag (str) le tag du pays de la base de donnée

        résultat :

            - int
        """
        return self.curseur.execute(f"""SELECT COUNT(*) FROM {tag}""").fetchone()[0]


    def donnees_depuis_id(self, id, tag):
        """ Retourne les données associées au pays donné au jour odnt l'id est donné
        ---
        paramètres :

            - id (int) l'id du jour
            - tag (str) le pays

        résultat :

            - tuple / None
        """
        try:
            return self.curseur.execute(f'Select * from {tag} where id = {id}').fetchone()[1:]
        except:
            return None


    def donnees_depuis_jour(self, day, tag):
        """ Retourne les données associées au pays donné au jour donné
        ---
        paramètres :

            - day (str) le jour
            - tag (str) le pays

        résultat :

            - tuple / None
        """
        try:
            return self.curseur.execute(f'Select * from {tag} where Date = "{day}"').fetchone()[1:]
        except Exception as e:
            return self.donnees_depuis_id(1, tag)


    def jour_depuis_id(self, id, tag):
        """ Retourne le jour associé à l'id donnée dans la table donnée
        ---
        paramètres :

            - id (int) l'id du jour
            - tag (str) le pays

        résultat :

            - str
        """
        return self.curseur.execute(f'Select Date from {tag} where id = {id}').fetchone()[0]


    def connection(self):
        """ Ouvre la fenêtre de sélection de la base de donnée et charge la base de donnée
        ---
        résultat :

            - bool (Si on s'est connecté à la base de donnée)
        """
        # Si on trouve la base de donnée dans le dossier, on s'y connecte
        f = trouverBdd()
        if f is not None:
            self.data_base = sqlite3.connect(f, check_same_thread=False)
            self.curseur = self.data_base.cursor()
            self.table = self.curseur.execute(
                "SELECT name FROM sqlite_master WHERE type='table';").fetchall()[-1][0]
            self.connecte = True
            return True
        # Si ce n'est pas le cas, on demande à l'utilisateur d'indiquer l'emplacement de la base de donnée
        else:
            f = easygui.fileopenbox("test", default=".", filetypes=["*.db"])
            if f:
                # Si le fichier donné n'est pas au bon format
                if not f.endswith(".db"):
                    messagebox.showerror("Erreur", "L'extension du fichier n'est pas correcte")
                    return False
                # Sinon on s'y connecte
                else:
                    self.data_base = sqlite3.connect(f, check_same_thread=False)
                    self.curseur = self.data_base.cursor()
                    self.table = self.curseur.execute(
                        "SELECT name FROM sqlite_master WHERE type='table';").fetchall()[-1][0]
                    self.connecte = True
                    return True
            return False


    def est_enregistre(self, tag):
        """ Vérifie que le pays donné est dans la base de donnée
        ---
        paramètre :

            - tag (str) le pays

        résultat :

            - bool
        """
        try:
            self.curseur.execute(f'SELECT pays from name where tag = "{tag}"').fetchone()[0]
            return True
        except:
            return False


    def extraire_modeles_depuis_bdd(self):
        """ Créer les modèles à partir des données chargées
        ---
        """
        for c in self.liste_pays:
            if self.est_enregistre(c.tag):
                self.liste_modeles.append(Modele(c, self))


    def fermer(self):
        """ Déconnecte le programme de la base de donnée
        ---
        """
        self.data_base.close()
