import datetime
import random
import sqlite3
import time
from tkinter import messagebox

import easygui
import numpy as np
from matplotlib import pyplot as plt

from RecNN import RecNN


class Trainer:

    def __init__(self, NN):
        """ Initialisation du Trainer
        ---
        param :

            - NN (RecNN) le réseau à entrainer
            - nb_test (int) le nombre de donnée sur lequel tester le réseau
        """
        self.NN = NN
        self.data_base = None
        self.connected = False
        self.table = []
        self.train_data = []
        self.test_data = []
        self.sorted_batchs = {}
        self.all_batchs = []


    def out_connect(self):
        """ Ouvre la fenêtre de sélection de la base de donnée et charge la base de donnée
        ---
        result :

                bool
        """
        f = easygui.fileopenbox("test", default=".", filetypes=["*.db"])
        if f:
            if not f.endswith(".db"):
                messagebox.showerror("Erreur", "L'extension du fichier n'est pas correcte")
                return False
            else:
                self.in_connect(f)
                return True
        return False


    def in_connect(self, f):
        """ Charge la base de donnée fournie
        ---
        result :

                bool
        """
        self.data_base = sqlite3.connect(f, check_same_thread=False)
        self.cursor = self.data_base.cursor()
        self.table = [x[0] for x in self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';").fetchall() if x[0] != "name"]
        self.connected = True


    def extract_data_from_db(self, category):
        """ Récupère les données de la base de données relative à la catégorie donnée
        ---
        param :

            - category (str) la catégorie à récupérer

        result :
            dict(clée de la base de donnée (str): data list(int))
        """
        assert self.connected
        res = {}
        if category in [x[1] for x in self.cursor.execute(f"PRAGMA table_info({self.table[0]});").fetchall()]:
            for key in self.table:
                res[key] = [x[0] for x in self.cursor.execute(f"SELECT {category} from '{key}'").fetchall()]
        return res


    def create_batch(self, batch_size, key):
        """ Créer les paquets de données depuis la base de donnée de la catégorie demandé
        ---
        param :

            - batch_size (int) le nombre de donnée en entrée de l'IA
            - key (str) la catégorie avec laquelle créer les paquets

        result :

            dict(clée de la base de donnée (str): list(dict(x : list(int), y  : list(int))))
        """
        data = self.extract_data_from_db(key)
        nb_batch = 0
        for k in range(len(data)):
            key = list(data.keys())[k]
            self.sorted_batchs[key] = []
            for n in range(len(data[key]) - batch_size):
                r = {'x': [], 'y': []}
                for i in range(batch_size):
                    r['x'].append(data[key][n + i])
                if sum(r['x']) != 0:
                    r['y'].append(data[key][n + i + 1])
                    self.sorted_batchs[key].append(r)
                    nb_batch += 1
        print(f"{nb_batch} batchs générés")
        for key in self.sorted_batchs:
            self.all_batchs += self.sorted_batchs[key]


    def create_test_sets(self, batch_lenght):
        """ Créer les paquets pour l'entrainement
        ---
        param :

            - d (dict) les données
            - batch_lenght (int) la longueur du paquets
        """
        random.shuffle(self.all_batchs)
        k = 0
        self.train_data = []
        while (k + 2) * batch_lenght < len(self.all_batchs):
            self.train_data.append(self.all_batchs[k * batch_lenght: (k + 1) * batch_lenght])
            k += 1
        self.test_data = self.all_batchs[k * batch_lenght:]


    def extract_data_from_batch(self, batch):
        """ Transforme les données dans un format correct pour le réseau
        ---
        param :

            - batch (list(dict)) les données à formatter

        result :

            list, list
        """
        x, y = [], []
        for k in range(len(batch)):
            x.append(batch[k]['x'])
            y.append(batch[k]['y'])
        return x, y


    def train(self, nb_iteration, batch_lenght):
        """ Entraine le réseau
        ---
        param :

            - nb_iteration (int) le nombre d'itération du réseau
        """
        err_list = []
        t = time.perf_counter()
        for k in range(nb_iteration):
            T.create_test_sets(batch_lenght)
            for n in range(len(self.train_data)):
                x, y = self.extract_data_from_batch(self.train_data[n])
                NN.train(x, y)
            self.NN.nb_train += 1
            x, y = self.extract_data_from_batch(self.test_data)
            err = y - NN.feedforward(x)
            e = sum(abs(err)) / len(err)
            print(f"Itération n° {k + 1}  \tPrécision : {(1 - e[0]) * 100}\t%")
        x, y = self.extract_data_from_batch([self.test_data[0]])
        o = NN.feedforward(x)
        print(
            f"--- Fin de l'entrainement ---\nNombre d'itération : \t{nb_iteration}\nDurée : \t{datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.perf_counter() - t), '%H h %M m %S s')}\nPrédiction : {o[0][0] * 2000}\t\tAtendu : {y[0][0] * 2000}")


    def extract_prediction_sequence(self, category):
        """ Récupère une liste de donnée d'une simulation choisie aléatoirement
        ---
        param :

            - category (str) la catégorie dont on doit tirer les données

        result :

            list(float)
        """
        key = random.choice(self.table)
        return [x[0] for x in self.cursor.execute(f"SELECT {category} from '{key}'").fetchall()]


    def predict(self, nb_iteration, start, NN=None):
        """ Lance une prédiction d'évolution en fonction de l'entrée sur un nombre d'itération donné
        ---
        param :

            - nb_iteration (int) le nombre d'itération
            - start ([list(float)]) les données en entrée
            - NN (RecNN) le réseau à tester (par défaut self.NN)

        result :

            list(float)
        """
        NN = self.NN if NN is None else NN
        res = []
        for _ in range(nb_iteration):
            n = NN.feedforward(start).tolist()[0][0]
            n = int(n * 2000) / 2000
            res.append(n)
            start[0].pop(0)
            start[0].append(n)
        return res


    def compare(self, n, ecart):
        """ Compare différents modèles
        ---
        param :

            - n (int) le nombre de modèle à comparer
        """
        real = T.extract_prediction_sequence(TYPE)
        x = list(range(len(real)))
        xx = x[START + NB_INPUT:]
        plt.plot(x, real, label="Réel")
        for k in range(n // ecart):
            i = [real[START:START + NB_INPUT]]
            # struct(30-100-50-1)-lr(0.001)-tr(32000).msgpack
            # f"./Model/struct(50-500-500-500-500-500-500-500-50-1)-lr(0.001)-tr({2 * (k + 1)}000).json"
            # struct(50-100-100-100-50-1)-lr(0.001)-tr(9400).msgpack
            NN = RecNN.load_from_file(f"./Model/struct(50-100-100-100-50-1)-lr(0.001)-tr({ecart * (k + 1)}000).msgpack")
            y = T.predict(len(real) - NB_INPUT - START, i, NN)
            plt.plot(xx, y, label=f"Après {ecart * (k + 1)}000 itérations")
            plt.legend()
        plt.show()



NB_INPUT = 50
START = 0
TYPE = "Infectés"


#NN = RecNN([NB_INPUT, 100, 100, 100, 50, 1], 0, 1e-3)

# ./Model/struct(30-100-50-1)-lr(0.001)-tr(32000).msgpack marche pas bien du tout ~ 2 min
# ./Model/struct(50-500-500-500-500-500-500-500-50-1)-lr(0.001)-tr(17600).json ~ 60 min
# ./Model/struct(50-100-100-100-50-1)-lr(0.001)-tr(9400).msgpack peut le faire ~ 6 min (à voir)
NN = RecNN.load_from_file("./Model/struct(50-100-100-100-50-1)-lr(0.001)-tr(9500).msgpack")

T = Trainer(NN)
T.in_connect("./Simulation-0/result.db")
T.create_batch(NB_INPUT, TYPE)

T.compare(9, 2)


real = T.extract_prediction_sequence(TYPE)
i = [real[START:START + NB_INPUT]]
x = list(range(len(real)))
xx = x[START + NB_INPUT:]

""" for _ in range(200):
    T.train(100, 512)
    NN.save()
 """

y = T.predict(len(real) - NB_INPUT - START, i)

plt.plot(x, real, label="Réel")
plt.plot(xx, y, label="Après itérations")
plt.legend()
plt.show()


# TODO:
#   - test s/ nvl sim
#   - comparer != modèles
