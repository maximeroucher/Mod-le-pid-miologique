import os
import sqlite3

# Mute l'import de pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'True'
import pygame
import easygui



class SIR:

    def __init__(self, country, N0, trans, tp, nb_iterations, use_db):
        """ Simulation selon le modèle SIR
        ---
        param :

            - N (int) le nombre de personne dans la simulation
            - N0 (int) le nombre de personne infectées au début de la simulation
            - trans (float) la transmissibilité de la maladie
            - tp (int) le nombre de jour de maladie une fois infecté
            - nb_iterations (int) le nombre de jour de la simulation
        """
        assert trans >= 0 and trans <= 1
        self.use_db = use_db
        self.country = country
        self.N = self.country.pop
        self.N0 = N0
        self.S = (self.N - self.N0) / self.N
        self.I = N0 / self.N
        self.R = 0
        self.transmission = trans
        self.temps_maladie = tp
        self.nb_iterations = nb_iterations
        self.pct_malade = 1 / self.temps_maladie
        self.param_dict = {"Sains":
                           {"value": self.S, "color": (237, 203, 81)},
                           "Infectés":
                           {"value": self.I, "color": (198, 96, 55)},
                           "Rétablis":
                           {"value": self.R, "color": (77, 94, 118)}
                            }


    def update(self, tbm, jour):
        """ Avance d'un jour la simulation
        ---
        """
        if self.use_db:
            res = tbm.get_country_data(jour, self.country.tag)
            if res is not None:
                self.S, self.I, self.R = [x / self.N for x in res]
                self.update_param_dict()
        else:
            dS = -self.transmission * self.I * self.S
            dI = (self.transmission * self.S - self.pct_malade) * self.I
            dR = self.pct_malade * self.I
            self.S += dS
            self.I += dI
            self.R += dR
            self.pop_tot = self.S + self.I + self.R
            self.update_param_dict()


    def getCI(self):
        return {"N0": self.N0, "Transmission": self.transmission, "Tps_maladie": self.temps_maladie, "Nb_iteration": self.nb_iterations}


    def update_param_dict(self):
        """ Enregistre les données de la classe dans le dictionnaire
        ---
        """
        self.param_dict["Sains"]["value"] = self.S
        self.param_dict["Infectés"]["value"] = self.I
        self.param_dict["Rétablis"]["value"] = self.R


    def format_sim(self):
        """ Formmatte les données de la simulation pour l'affichage
        """
        return {'Sains': self.S, "Infectés": self.I, "Morts / Guéris": self.R}


    def __str__(self):
        d = self.format_sim()
        a = "\n\t- ".join([f"{x} : {d[x]}" for x in list(d.keys())])
        return f"Population de {self.N} personnes.\nRésultat :\n\t- {a}"



class SIRM:

    def __init__(self, country, N0, transm, tp, l, nb_iterations, use_db):
        """ Simulation selon le modèle SIR avec l'ajout de la léthalité de la maladie
        ---
        param :

            - country (Pays) le pays dans laquelle se déroule la simlation
            - N0 (int) le nombre de personne infectées au début de la simulation
            - transm (float, 0 <= t <= 1) la transmissibilité de la maladie
            - tp (int) le nombre de jour de maladie une fois infecté
            - l (float, 0 <= l <= 1) la léthalité de la maladie
            - nb_iterations (int) le nombre de jour de la simulation
        """
        assert transm >= 0 and transm <= 1
        assert l >= 0 and l <= 1
        self.use_db = use_db
        self.country = country
        self.N = self.country.pop
        self.N0 = N0
        self.S = (self.N - self.N0) / self.N
        self.I = self.N0 / self.N
        self.R = 0
        self.M = 0
        self.pop_tot = self.N
        self.transmission = transm
        self.lethalite = l
        self.temps_maladie = tp
        self.nb_iterations = nb_iterations
        self.pct_malade = 1 / self.temps_maladie
        self.param_dict = {"Sains":
                           {"value": self.S, "color": (237, 203, 81)},
                           "Infectés":
                           {"value": self.I, "color": (198, 96, 55)},
                           "Rétablis":
                           {"value": self.R, "color": (77, 94, 118)},
                           "Morts":
                           {"value": self.M, "color": (10, 100, 203)},
                           "Population totale":
                           {"value": 1, "color": (128, 179, 64)}
                          }


    def getCI(self):
        return {"N0": self.N0, "Transmission": self.transmission, "Léthalité": self.lethalite, "Tps_maladie": self.temps_maladie, "Nb_iteration": self.nb_iterations}


    def update(self, tbm, jour):
        """ Avance d'un jour la simulation
        ---
        """
        if self.use_db:
            res = tbm.get_country_data(jour, self.country.tag)
            if res is not None:
                self.S, self.I, self.R, self.M, self.pop_tot = [x / self.N for x in res]
                self.update_param_dict()
        else:
            dS = -self.transmission * self.I * self.S
            dI = (self.transmission * self.S - self.pct_malade - self.lethalite) * self.I
            dR = self.pct_malade * self.I
            dM = self.lethalite * self.I
            self.S += dS
            self.I += dI
            self.R += dR
            self.M += dM
            self.pop_tot = self.S + self.I + self.R
            self.update_param_dict()


    def update_param_dict(self):
        """ Enregistre les données de la classe dans le dictionnaire
        ---
        """
        self.param_dict["Sains"]["value"] = self.S
        self.param_dict["Infectés"]["value"] = self.I
        self.param_dict["Rétablis"]["value"] = self.R
        self.param_dict["Morts"]["value"] = self.M
        self.param_dict["Population totale"]["value"] = self.pop_tot


    def format_sim(self):
        """ Formmatte les données de la simulation pour l'affichage
        ---
        """
        return {'Sains': self.S * self.N, "Infectés": self.I * self.N, "Rétablis": self.R * self.N, "Morts": self.M * self.N}


    def __str__(self):
        d = self.format_sim()
        a = "\n- " + "\n- ".join([f"{x} : {int(d[x] * self.N)}" for x in list(d.keys())])
        return f"Population de {self.N} personnes.\nRésultat :{a}"



class Compartiment:

    def __init__(self, N, nom, color):
        """ Initialisation d'un compartiment
        ---
        param :

            - N (float 0 <= N <= 1) le pourcentage de la population dans ce compartiment
            - nom (str) le nom du compartiment
            - color ((r, g, b)) la couleur de la courbe de l'évolution dans le graphique
        """
        self.N = N
        self.nom = nom
        self.color = color


    def get_d(self, coef, include_itself, other_comp=None):
        """ Calcule le pourcentage de personne qui sont passé de ce compartiment au compartiment donné en 1 jour
        ---
        param :

            - coef (float 0 <= coef <= 1) le coef de transfert entre les deux compartiments
            - include_itself (bool) indique si le nombre de personne de ce compartiment doit faire partie du calcule
            - other_comp (None / Compartiment) le compartiment d'arrivé, si il est donné sa valeur intervient dans la calcul
        """
        c = 1 if other_comp is None else other_comp.N
        d = 1 if not include_itself else self.N
        return coef * c * d


    def give(self, d):
        """ Ajoute tout le pourcentage donné
        ---
        """
        self.N += d



class ModeleCompartimental:

    def __init__(self, comp_list):
        """ Initialisation d'un model compartimental
        ---
        param :

            - comp_list (list(Compartiment))
        """
        self.param_dict = {comp.nom : {"value": comp.N, "color": comp.color} for comp in self.comp_dict}



class Event:

    def __init__(self):
        """ Initialisation de la classe Event, évènement ponctuel qui ont un effet sur l'évolution de l'épidémie
        ---
        """



class TableManager:

    def __init__(self, name, models, overwrite):
        """ Gestionnaire de base de donnée pour sauvegarder les données de la simulation
        ---
        param :

            - name (str) le nom de la base de donnée
            - models list(ModeleCompartimental) la liste des modèles de la simulation
            - overwrite (bool) supprimer le fichier déjà existant
        """
        self.models = models
        self.keys = [s for s in self.models[0].param_dict]
        self.formated_keys = [x.replace(" ", "_") for x in self.keys]
        self.data_base_name = name

        # Création / Connection à la base de donnée
        filename = f"{self.data_base_name}.db"
        filepath = f"./{filename}"
        if overwrite or (not filename in os.listdir()):
            open(filepath, 'w').close()
        self.data_base = sqlite3.connect(filepath, check_same_thread=False)
        self.cursor = self.data_base.cursor()
        self.tables = [x[0] for x in self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
        self.ctables = self.tables
        if len(self.tables) == 0:
            self.is_empty = True
            tables_keys = ", ".join([f"{x.replace(' ', '_')} integer" for x in [x for x in self.models[0].param_dict]])
            for model in self.models:
                self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS {model.country.tag} (id integer PRIMARY KEY, {tables_keys})""")
            self.data_base.commit()
        else:
            assert self.check_bd_valid()
            self.is_empty = False


    def check_bd_valid(self):
        """ Vérifie que la base de donnée à les mêmes paramètres pour chaque table
        ---
        result :

            - bool la base est "valide"
        """
        self.ctables = self.tables
        if not "Conditions_initiales" in self.ctables:
            return False
        else:
            self.ctables.remove("Conditions_initiales")
        test_keys = [y[1] for y in self.cursor.execute(f"PRAGMA table_info ({self.ctables[0]})").fetchall()]
        x = 1
        while x < len(self.ctables):
            data = [y[1] for y in self.cursor.execute(f"PRAGMA table_info ({self.ctables[x]})").fetchall()]
            if data != test_keys:
                return False
            x += 1
        return True


    def sim_length(self):
        return self.cursor.execute(f"""SELECT COUNT(*) FROM {self.ctables[0]}""").fetchone()[0]


    def get_country_data(self, jour, tab):
        """ Récupère les données du pays le jour donné, si les donné du pays ne sont pas donné, c'est que son état n'as pas changé depuis le jour précédent
        ---
        param :

            - jour (int) le jour des données de la simulation renvoyées
        """
        try:
            return self.cursor.execute(f"""Select * from {tab} where id = {jour}""").fetchone()[1:]
        except:
            return None


    def get_CI(self):
        """ Récupère les conditons initiales de la simulation enregistrée
        """
        return self.cursor.execute("""Select * from Conditions_initiales """).fetchone()


    def save_model_param(self):
        """ Sauvegarde les conditions initiales de la simulation
        ---
        param :

            - model (ModeleCompartimental) le modèle contenant le pays d'origine de l'épidémie
        """
        model = [m for m in self.models if m.I != 0][0]
        data = model.getCI()
        k = list(data.keys())
        tables_keys = ", ".join([x + " REAL" for x in k])
        command = f"""CREATE TABLE IF NOT EXISTS Conditions_initiales (id integer PRIMARY KEY, Pays text NOT NULL, {tables_keys})"""
        self.cursor.execute(command)
        command = f"""INSERT INTO Conditions_initiales {tuple(["Pays"] + k)} VALUES {tuple([model.country.tag] + list(data.values()))}"""
        self.cursor.execute(command)
        self.data_base.commit()


    def save_data(self, jour):
        """ Sauvegarde les données de tous les pays dans la table du numéro du jour donné
        ---
        param :

            - jour (int) le numéro du jour
        """
        for model in self.models:
            if model.I != 0:
                v = [int(model.param_dict[x]["value"] * model.N) for x in self.keys]
                self.cursor.execute(f"""INSERT INTO {model.country.tag} {tuple(self.formated_keys)} VALUES {tuple(v)}""")
        self.data_base.commit()


    def end(self):
        """ Déconnecte le programme de la base de donnée
        ---
        """
        self.data_base.close()



class Country_Test:

    def __init__(self, pop, name, tag):
        """ Remplacement de la classe Pays pour les test, plus facile à init
        ---
        """
        self.pop = pop
        self.name = name
        self.tag = tag


# Test
if __name__ == "__main__":
    test = Country_Test(1379302770, 'test', "TST")
    sirm = SIRM(test, 1, .5, 6, .9, 100, True)
    tab = TableManager("Test", [sirm], False)
    sirm.update(tab, 5)
    """ f = easygui.fileopenbox("test", default=".", filetypes=["*.db"])
    if f:
        if not f.endswith(".db"):
            easygui.msgbox("L'extension du fichier n'est pas correcte")
        else:
            print(f) """
