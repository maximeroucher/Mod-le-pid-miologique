import datetime
import random
import sqlite3
import time

import numpy as np
from matplotlib import pyplot as plt
from tqdm import tqdm

from outils import trouverBdd
from RecNN import RNN


class Entraineur:

    def __init__(self, NN):
        """ Initialisation de l'Entraineur
        ---
        paramètres :

            - NN (RNN) le réseau à entrainer
        """
        self.NN = NN
        self.bdd = None
        self.connecte = False
        self.liste_pays = []
        self.donnee_d_entrainement = []
        self.donnee_de_test = []
        self.paquets_tries = {}
        self.liste_paquets = []


    def connnection(self, f):
        """ Charge la base de donnée fournie
        ---
        paramètre :

            - f (str) le nom du fichier

        résultat :

            - bool
        """
        # On se connecte à la base de donnée
        self.bdd = sqlite3.connect(f, check_same_thread=False)
        self.cursor = self.bdd.cursor()
        # La liste des clées
        self.liste_pays = [x[0] for x in self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';").fetchall() if x[0] != "name"]
        # On est connecté
        self.connecte = True


    def extraire_donnees_depuis_bdd(self, categorie):
        """ Récupère les données de la base de données relative à la catégorie donnée
        ---
        paramètre :

            - categorie (str) la catégorie à récupérer

        résultat :
            dict(clée de la base de donnée (str): donnees list(int))
        """
        res = {}
        # On vérifie que la catégorie demandée est dans la base de donnée
        if categorie in [x[1] for x in self.cursor.execute(f"PRAGMA table_info({self.liste_pays[0]});").fetchall()]:
            # On récupère pour chaque pays, la listes des valeurs normalisées
            for pays in self.liste_pays:
                N = self.cursor.execute(f"SELECT Sains from '{pays}' where id = 1").fetchone()[0]
                res[pays] = [x[0] / N for x in self.cursor.execute(f"SELECT {categorie} from '{pays}'").fetchall()]
        return res


    def creer_paquets(self, taille_paquets, pays):
        """ Créer les paquets de données de la catégorie demandé depuis la base de donnée
        ---
        paramètres :

            - taille_paquets (int) le nombre de donnée en entrée de l'IA
            - pays (str) la catégorie avec laquelle créer les paquets

        résultat :

            dict(clée de la base de donnée (str): list(dict(x : list(int), y  : list(int))))
        """
        # La liste des valeurs normalisées pour la catégorie par pays
        donnees = self.extraire_donnees_depuis_bdd(pays)
        nb_paquets = 0
        # Pour chaque pays
        for pays in donnees:
            # On crée une liste vide dans le dictionnaire
            self.paquets_tries[pays] = []
            # On itère sur des blocs de taille taille_paquets
            for n in range(len(donnees[pays]) - taille_paquets):
                # Le dictionnaire qui contient les entrées dans x et les sorties dans y
                dict_donnee = {'x': [], 'y': []}
                # On ajoute chaque donnée d'entrée
                for i in range(taille_paquets):
                    dict_donnee['x'].append(np.asarray(donnees[pays][n + i], dtype=np.float64))
                # Si on reste à 0 tout le long, ce n'est pas intéressant
                if sum(dict_donnee['x']) != 0:
                    # On ajoute la sorite souhaitée
                    dict_donnee['y'].append(np.asarray(donnees[pays][n + i + 1], dtype=np.float64))
                    # On ajoute ce dictionnaire à la liste des données
                    self.paquets_tries[pays].append(dict_donnee)
                    nb_paquets += 1
        print(f"{nb_paquets} paquets générés")
        # On concatène le dictionnaire en liste
        for pays in self.paquets_tries:
            self.liste_paquets += self.paquets_tries[pays]


    def creer_paquets_de_test(self, longeur_paquets):
        """ Créer les paquets pour l'entrainement
        ---
        paramètres :

            - d (dict) les données
            - longeur_paquets (int) la longueur du paquets
        """
        # On mélange la liste
        random.shuffle(self.liste_paquets)
        k = 0
        self.donnee_d_entrainement = []
        # On utilise tout les paquets sauf les 2 derniers comme paquets d'entrainement
        while (k + 2) * longeur_paquets < len(self.liste_paquets):
            self.donnee_d_entrainement.append(self.liste_paquets[k * longeur_paquets: (k + 1) * longeur_paquets])
            k += 1
        # Le reste est utilisé comme paquets de test
        self.donnee_de_test = self.liste_paquets[k * longeur_paquets:]


    def extraire_donnees_depuis_paquet(self, paquet):
        """ Transforme les données dans un format correct pour le réseau
        ---
        paramètre :

            - paquet (list(dict)) les données à formatter

        résultat :

            list, list
        """
        # On concatène les dictionnaires en liste
        x, y = [], []
        for k in range(len(paquet)):
            x.append(paquet[k]['x'])
            y.append(paquet[k]['y'])
        return x, y


    def entrainer(self, nb_iteration, longeur_paquets):
        """ Entraine le réseau
        ---
        paramètres :

            - nb_iteration (int) le nombre d'itération du réseau
            - longeur_paquets (int) la longeur des paquets
        """
        # On regarde le moment du début de l'entrainement
        t = time.perf_counter()
        for k in range(nb_iteration):
            T.creer_paquets_de_test(longeur_paquets)
            # On entrainer le réseau sur tout les paquets
            for n in range(len(self.donnee_d_entrainement)):
                donnee_entrainement, donnee_test = self.extraire_donnees_depuis_paquet(self.donnee_d_entrainement[n])
                NN.entrainer(donnee_entrainement, donnee_test)
            self.NN.nb_entrainement += 1
            # On récupère les données de test
            donnee_entrainement, donnee_test = self.extraire_donnees_depuis_paquet(self.donnee_de_test)
            # On calcule la prédiction du réseau
            erreur = donnee_test - NN.calcule_sortie(donnee_entrainement)
            # On calcule l'erreur de la prédiction
            moyenne_erreur = sum(abs(erreur)) / len(erreur)
            print(f"Itération n° {k + 1}  \tPrécision : {(1 - moyenne_erreur[0]) * 100}\t%")
        # On extrait une séquence de test
        donnee_entrainement, donnee_test = self.extraire_donnees_depuis_paquet([self.donnee_de_test[0]])
        sortie = NN.calcule_sortie(donnee_entrainement)
        # On affiche les résultats
        print(
            f"--- Fin de l'entrainement ---\nNombre d'itération : \t{nb_iteration}\nDurée : \t{datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.perf_counter() - t), '%H h %M m %S s')}\nPrédiction : {sortie[0][0]}\t\tAtendu : {donnee_test[0][0]}")


    def extraire_sequence_test(self, categorie):
        """ Récupère une liste de donnée d'une simulation choisie aléatoirement
        ---
        paramètre :

            - categorie (str) la catégorie dont on doit tirer les données

        résultat :

            list(float), int
        """
        pays = random.choice(self.liste_pays)
        N = self.cursor.execute(f"SELECT Sains from '{pays}' where id = 1").fetchone()[0]
        return [x[0] for x in self.cursor.execute(f"SELECT {categorie} from '{pays}'").fetchall()], N


    def prediction(self, nb_iteration, sequence_depart, N, NN=None):
        """ Lance une prédiction d'évolution en fonction de l'entrée sur un nombre d'itération donné
        ---
        paramètres :

            - nb_iteration (int) le nombre d'itération
            - sequence_depart ([list(float)]) les données en entrée
            - N (int) le nombre de personnes
            - NN (RNN) le réseau à tester (par défaut self.NN)

        résultat :

            list(float)
        """
        # On récupère le réseau
        NN = self.NN if NN is None else NN
        res = []
        for _ in range(nb_iteration):
            # La prédiction du réseau
            n = NN.calcule_sortie(sequence_depart).tolist()[0][0] * N
            # On ajoute la donnée au résultat
            res.append(n)
            # On élimine la première valeur, et on ajoute la dernière, pour toujours avoir le même nombre d'entrée
            sequence_depart[0].pop(0)
            sequence_depart[0].append(n)
        return res


    def comparer(self, n, nb_model):
        """ Compare différents modèles
        ---
        paramètres :

            - n (int) le numéro maximal du modèle à comparer
            - nb_model (int) le nombre de model à comparer
        """
        # Le nombre de réseau à tester
        nb_model = min(nb_model, self.NN.nb_entrainement // 1000)
        # Le numéro maximale du réseau
        n = min(n, self.NN.nb_entrainement // 1000)
        # L'écart entre le numéro de deux réseau
        ecart = n // nb_model
        # Les données de test
        donnees_reeles = T.extraire_sequence_test(TYPE)
        # La liste des abcsisses
        abcsisse = list(range(len(donnees_reeles)))
        # L'abcsisse des valeurs prédite pas le réseau
        extraction_abcsisse = abcsisse[START + NB_INPUT:]
        # Affiche les données réelles
        plt.plot(abcsisse, donnees_reeles, label="Réel")
        # On récupère le morceau avant et après le nombre d'entrainemet dans le nom du fichier
        pref, suf = self.NN.nom_fichier.split(str(self.NN.nb_entrainement))
        # Pour tout les réseaux que l'on doit tester
        for k in tqdm(range(n // ecart)):
            # Les données initiales
            i = [donnees_reeles[START:START + NB_INPUT]]
            # On charge le réseau
            NN = RNN.charger_depuis_fichier(pref + str(ecart * (k + 1) * 1000) + suf)
            # La prédiction du réseau
            y = T.prediction(len(donnees_reeles) - NB_INPUT - START, i, NN)
            # On affiche les données
            plt.plot(extraction_abcsisse, y, label=f"Après {ecart * (k + 1)}000 itérations")
            plt.legend()
        plt.show()


if __name__ == "__main__":
    # On donne 50 nombres successifs au réseau pour qu'il prédise le 51e
    NB_INPUT = 50
    # On commence au premier jour
    START = 0
    # On essaie de prédire l'évolution du nombre d'infectés
    TYPE = "Infectés"


    NN = RNN([NB_INPUT, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 100, 1], 0, 1e-3)

    # ./Model/struct(50-500-500-500-500-500-500-500-50-1)-lr(0.001)-tr(17600).json ~ 60 min
    # ./Model/struct(50-100-100-100-50-1)-lr(0.001)-tr(38800).msgpack peut le faire ~ 3/4 min
    # ./Model/struct(50-100-100-100-100-100-50-1)-lr(0.001)-tr(7000).msgpack
    # ./Model/struct(50-100-100-100-100-100-100-100-100-100-100-50-1)-lr(0.001)-tr(42700).msgpack
    #NN = RNN.charger_depuis_fichier("./Model/struct(50-200-200-200-200-200-200-200-200-200-200-100-1)-lr(0.001)-tr(42700).msgpack")

    T = Entraineur(NN)
    # On charge les données mondiale de l'épidémie
    T.connnection(trouverBdd())
    # On créer les paquets pour le réseau
    T.creer_paquets(NB_INPUT, TYPE)

    # On compare différents le même modèle avec différents nombre d'itération
    #T.comparer(40, 5)

    # On entrainer le réseau
    for _ in range(1000):
        # On entraine le réseau sur 100 itérations
        T.entrainer(100, 512)
        # On le sauvegarde
        NN.sauvegarder()

    # On extrait des données de test
    donnees_reeles, N = T.extraire_sequence_test(TYPE)
    # On extrait les valeurs de départ pour le réseaau
    i = [donnees_reeles[START:START + NB_INPUT]]
    # On récupère la liste des abcsisses
    abcsisse = list(range(len(donnees_reeles)))
    # On récupère la liste des abcsisses des données générées par le réseau
    extraction_abcsisse = abcsisse[START + NB_INPUT:]

    # Les données générées par le réseau
    y = T.prediction(len(donnees_reeles) - NB_INPUT - START, i, N)

    # On affiche les données
    plt.plot(abcsisse, donnees_reeles, label="Réel")
    plt.plot(extraction_abcsisse, y, label="Après itérations")
    plt.legend()
    plt.show()


