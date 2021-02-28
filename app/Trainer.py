import random
import sqlite3
from tkinter import messagebox

import easygui
import numpy as np

from RecNN import RecNN
from matplotlib import pyplot as plt


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
        res = {}
        nb_batch = 0
        for k in range(len(data)):
            key = list(data.keys())[k]
            res[key] = []
            for n in range(len(data[key]) - batch_size):
                r = {'x': [], 'y': []}
                for i in range(batch_size):
                    r['x'].append(data[key][n + i])
                if sum(r['x']) != 0:
                    r['y'].append(data[key][n + i + 1])
                    res[key].append(r)
                    nb_batch += 1
        print(f"{nb_batch} batchs générés")
        return res


    def create_test_sets(self, d, batch_lenght):
        """ Créer les paquets pour l'entrainement
        ---
        param :

            - d (dict) les données
            - batch_lenght (int) la longueur du paquets
        """
        l = []
        for key in d:
            l += d[key]
        random.shuffle(l)
        k = 0
        while (k + 2) * batch_lenght < len(l):
            self.train_data.append(l[k * batch_lenght: (k + 1) * batch_lenght])
            k += 1
        self.test_data = l[k * batch_lenght:]


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


    def train(self, nb_iteration):
        """ Entraine le réseau
        ---
        param :

            - nb_iteration (int) le nombre d'itération du réseau
        """
        for k in range(nb_iteration):
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
        print(o[0][0] * 2000, y[0][0] * 2000)


    def extract_prediction_sequence(self, category):
        key = random.choice(self.table)
        return [x[0] for x in self.cursor.execute(f"SELECT {category} from '{key}'").fetchall()]


    def predict(self, nb_iteration, start):
        """ Lance une prédiction d'évolution en fonction de l'entrée sur un nombre d'itération donné
        ---
        param :

            - nb_iteration (int) le nombre d'itération
            - start ([list(float)]) les données en entrée

        result :

            list(float)
        """
        res = []
        for _ in range(nb_iteration):
            n = NN.feedforward(start).tolist()[0][0]
            res.append(n)
            start[0].pop(0)
            start[0].append(n)
        return res


NB_INPUT = 50
START = 0


#NN = RecNN([NB_INPUT, 500, 500, 500, 500, 500, 500, 500, 50, 1], 0, 1e-3)
NN = RecNN.load_from_file("./Model/struct(50-500-500-500-500-500-500-500-50-1)-lr(0.001)-tr(1000).json")
T = Trainer(NN)
T.in_connect("./Simulation-0/result.db")
res = T.create_batch(NB_INPUT, "Infectés")
T.create_test_sets(res, 256)

real = T.extract_prediction_sequence("Infectés")
i = [real[START:START + NB_INPUT]]
x = list(range(len(real)))
xx = x[START + NB_INPUT:]

T.train(100)
y = T.predict(len(real) - NB_INPUT - START, i)

plt.plot(x, real, label="Réel")
plt.plot(xx, y, label=f"Après itérations")
plt.legend()
plt.show()
NN.save()
