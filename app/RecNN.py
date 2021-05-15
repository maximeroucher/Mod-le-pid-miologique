import json
import os

import msgpack
import numpy as np
# Cette bibliothète convertit le code python en code C pour accelérer les calculs
from numba import njit


def relu(x):
    """ La fonction de régression linéaire
    ---
    paramètre :

        - x (float)

    résultat :

        float
    """
    return max(x, 0)


def relu_der(x):
    """ La dérivée de la régression linéaire
    ---
    paramètre :

        - x (float)

    résultat :

        float
    """
    return 0 if x <= 0 else 1


@njit
def sigmoid(x):
    """ La fonction sigmoid
    ---
    paramètre :

        - x (float)

    résultat :

        float
    """
    return 1 / (1 + np.exp(-x))


@njit
def sigmoid_der(x):
    """ La dérivé de la fonction sigmoid (x = sigmoid(y))
    ---
    paramètre :

        - x (float)

    résultat :

        float
    """
    return x * (1 - x)


def _calcule_sortie(entree, poids, biais):
    """ Calcul la sortie du réseau en fonction de l'entrée
    ---
    paramètres :

        - entree (np.matrix) la matrice des valeurs d'entrée
        - poids (np.matrix) la matrice de poids
        - biais (np.matrix) la matrice des biais

    résultat :

        - np.matrix
    """
    return sigmoid(np.dot(entree, poids) + biais)


@njit
def _retropropagation(erreur, input, poids, biais, lr, activations):
    """ Calcule la rétropropagation des poids et biais
    ---
    paramètres :

        - erreur (np.matrix) la matrice d'erreur
        - input (np.matrix) la matrice des valeurs d'entrées
        - poids (np.matrix) la matrice des poids
        - biais (np.matrix) la matrice des biais
        - lr (float, 0 <= lr <= 1) le taux d'apprentissage
        - activations (np.matrix) la matrice de sortie de _calcule_sortie

    résultats :

        - np.matrix (la matrice de poids modifiée)
        - np.matrix (la matrice de biais modifiée)
        - np.matrix (la nouvelle matrice d'erreur)
    """
    # Calcul l'erreur de chaque coefficient
    erreur = np.multiply(erreur, sigmoid_der(activations))
    # Calcule la jacobienne des poids
    d_poids = np.dot(input.T, erreur)
    # Calcule la jacobienne des biais
    d_biais = d_poids.sum(axis=0)
    # Calcule l'erreur d'entrée
    n_erreur = np.dot(erreur, poids.T)
    # Met à jour les poids et biais
    poids += lr * d_poids
    biais += lr * d_biais
    return poids, biais, n_erreur


# https://dustinstansbury.github.io/theclevermachine/derivation-backpropagation

class RNN:

    def __init__(self, dimension_couche, n, lr):
        """ Initialisation récursive du réseau de neurone
        ---
        paramètres :

            - dimension_couche (list(int), len >= 2) l'architecture du réseau
            - n (int) le numéro de la couche
            - lr (float, 0 < lr <= 1) le taux d'apprentissage
        """
        self.nb_entrainement = 0
        self.dernier_enfant = None
        self.parent = None
        self.enfant = None
        self.num = n
        self.lr = lr
        # De manière récursive le nb de neurones de cette couche est celui d'entrée de la couche suivante
        self.nb_entree, self.nb_neurones = dimension_couche[0], dimension_couche[1]
        # On crée la matrice de poids de manière aléatoire
        self.poids = np.random.randn(self.nb_entree, self.nb_neurones)
        # On initialisee les poids à 0 par défaut
        self.biais = np.zeros(dimension_couche[1])
        self.dimension_couche = dimension_couche
        # Le type de fichier de sauvegarde, par défaut les fichier msgpack sont plus compactes et plus précis, mais json est lisible
        self.utiliser_json = False
        self.nom_fichier = ""
        # Si on peut encore crée une couche
        if len(dimension_couche) > 2:
            # le réseau enfant
            self.enfant = RNN(dimension_couche[1:], n + 1, lr)
            # On met en place les relation d'hérédité
            self.enfant.parent = self
            self.dernier_enfant = self.enfant.dernier_enfant
        else:
            self.dernier_enfant = self


    def __str__(self):
        """ Représentation écrite du réseau
        ---
        résultat :

            str
        """
        s = f"Couche n° {self.num}\npoids :\n{self.poids}\nbiais :\n{self.biais}"
        if self.enfant:
            s += "\n\n" + self.enfant.__str__()
        return s


    def calcule_sortie(self, entree):
        """ Calcul de la prédiction du réseau
        ---
        paramètre :

            - entree (list(list(float)), len = dimension_couche[0]) les donnée en entrée du réseau

        résultat :

            list(list(float))
        """
        # On sauvegarde les données en entrée
        self.input = entree
        # On calcule la répoonse de la couche
        self.activations = _calcule_sortie(entree, self.poids, self.biais)
        # Si c'est la derniere couche
        if not self.enfant:
            return self.activations
        # Sinon on utilise la récursivité
        return self.enfant.calcule_sortie(self.activations)


    def retropropagation(self, erreur):
        """ Réévaluation des poids et biais du réseau en fonction de l'erreur
        ---
        paramètre :

            - erreur (list(list(float)), dim = dimension_couche[-1]) l'erreur commise par le réseau
        """
        # On modifie les poids et biais et on transmet l'erreur récursivement
        self.poids, self.biais, n_erreur = _retropropagation(erreur, self.input, self.poids, self.biais, self.lr, self.activations)
        if self.parent:
            self.parent.retropropagation(n_erreur)


    def entrainer(self, donnee_entrainement, donnee_test):
        """ Lance une prédiction et corrige en fonction du résultat
        ---
        paramètres :

            - x (list(list(float))) les données en entrée du réseau
            - y (list(list(float))) les données attendue en fin de réseau
        """
        # Prédiction du réseau
        sortie = self.calcule_sortie(np.array(donnee_entrainement))
        # Calcul de l'erreur
        erreur = 2 * (donnee_test - sortie)
        # Corrige le réseau
        self.dernier_enfant.retropropagation(erreur)


    def sauvegarde_rec(self, donnee):
        """ Fonction récursive auxilliare de sauvegarde du réseau
        ---
        paramètre :

            - donnee (dict(numéro de la couche (str): {w : list(list(float)), b : list(list(float))}))

        résultat :

            dict(numéro de la couche (str): {w : list(list(float)), b : list(list(float))})
        """
        # On ajoute les données au dictionnaire
        donnee[f'{self.num}'] = {"w": self.poids.tolist(), "b": self.biais.tolist()}
        # On le complète récursivement
        if not self.enfant:
            return donnee
        return self.enfant.sauvegarde_rec(donnee)


    def sauvegarder(self, utiliser_json=True):
        """ Enregistre le réseau
        ---
        paramètre :

            - utiliser_json (bool) choix du type de fichier de sauvegarde
        """
        # On crée le dossier s'il n'existe pas
        if not os.path.exists("./Model"):
            os.makedirs("./Model")
        # On crée le dictionnaire des données
        donnee = self.sauvegarde_rec({'lr': self.lr})
        # On sauvegarde
        if self.utiliser_json:
            json.dump(donnee, open(f"./Model/{self.nom}.json", "w"))
        else:
            fichier_sortie = open(f"./Model/{self.nom}.msgpack", "wb")
            donnees_binaires = msgpack.packb(donnee)
            fichier_sortie.write(donnees_binaires)


    @property
    def nom(self):
        """ Donne le nom du réseau
        ---
        résultat :

            - str (le nom)
        """
        return "struct(" + "-".join([str(x) for x in self.dimension_couche]
                                         ) + ")-lr(" + str(self.lr) + ")" + f"-tr({self.nb_entrainement})"


    def charger(self, nom_fichier):
        """ Charge le réseau depuis le fichier
        ---
        paramètre :

            - nom_fichier (str) le nom du fichier
        """
        self.nom_fichier = nom_fichier
        # On ouvre le fichier en fonction de son type
        if nom_fichier.endswith(".json"):
            donnee = json.load(open(nom_fichier))
            self.json = True
        elif nom_fichier.endswith(".msgpack"):
            with open(nom_fichier, "rb") as donnee_file:
                byte_donnee = donnee_file.read()
                donnee = msgpack.unpackb(byte_donnee)
        # le nom du fichier
        self.name = os.path.basename(nom_fichier)
        # On paramètre le réseau
        self.parametrer(donnee)


    def parametrer(self, donnee):
        """ Assigne au poids et biais les valeurs données
        ---
        paramètre :

            - donnee (dict(numéro de la couche (str): {w : list(list(float)), b : list(list(float))}))
        """
        # On assigne les poids et biais en fonction des valeurs
        couche = donnee[f'{self.num}']
        self.poids = np.array(couche['w'])
        self.biais = np.array(couche['b'])
        # On complète récursivement
        if self.enfant:
            self.enfant.parametrer(donnee)


    @staticmethod
    def charger_depuis_fichier(nom_fichier):
        """ Charge le réseau depuis le fichier donné
        ---
        paramètre :

            - nom_fichier (str) le nom du fichier
        """
        # On extrait les informations du réseau depuis le nom du fichier
        dimension_couche = [int(x) for x in nom_fichier.split("struct(")[1].split(")")[0].split("-")]
        lr = float(nom_fichier.split("lr(")[1].split(")")[0])
        t = int(nom_fichier.split("tr(")[1].split(")")[0])
        # On crée un réseaau
        NN = RNN(dimension_couche, 0, lr)
        # On charge les valeurs enregistrées
        NN.charger(nom_fichier)
        NN.nb_entrainement = t
        return NN
