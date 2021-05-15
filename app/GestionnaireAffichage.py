import os
import time
from threading import Thread

# Empêche l'import de pygame d'afficher du texte
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'True'

import pygame

from GestionnaireBDD import GestionnaireBDD
from outils import (BG, FG, afficher_texte, centrer_texte, creer_masque,
                    creer_masque_information, dans_rect, echelloner_valeur,
                    redimensionner_pays)


class GestionnaireAffichage(Thread):

    def __init__(self, ecran, pays, liste_tag, police, police_donnee, pays_selectione, sur_pays, liste_noire):
        """ Initialisation d'un graphique
        ---
        paramètres :

            - ecran (pygame.Surface) la surface sur laquelle écrire
            - pays (list(Pays)) la liste des pays de la simulation
            - liste_tag (list(str)) la liste des tags des pays
            - police (pygame.font.SysFont) la police des textes
            - police_donnee (pygame.font.SysFont) la police des graphiques
            - pays_selectione (int) le numéro du pays séléctionné
            - sur_pays (bool) l'affichage est celui d'un pays
            - liste_noire (list(str)) la liste des clées que l'on ne doit pas afficher
        """
        ## Initialisation du programme auxiliaire

        # Initialisation héréditaire
        Thread.__init__(self)
        # Le programme s'arrêtera quand on quittea le programme
        self.daemon = True

        # Les polices
        self.police = police
        self.police_donnee = police_donnee

        # Liste des tags des pays
        self.liste_tag = liste_tag

        # Pays séléctionné
        self.pays_selectione = pays_selectione

        # Pays où débute la simulation
        self.pays_pour_date = None
        self.liste_date = []


        ## Gestionnaire de base de donnée

        self.gbdd = GestionnaireBDD(pays)
        # Les compartiments à ne pas afficher
        self.liste_noire = liste_noire


        ## Surface

        self.ecran = ecran
        self.mettre_masque = False


        ## Les constantes

        # Largeur de la fenêtre
        self.LARGEUR = 700
        # Hauteur de la fenêtre
        self.HAUTEUR = 390
        # Marge entre les bords de la fenêtre et le graphique
        self.MARGE = 30
        # Hauteur maximale du graphique
        self.HAUT = self.HAUTEUR - self.MARGE
        # Longeur d'un trait
        self.LONGEUR_TRAIT = self.HAUT + 5
        # La largeur du graphique
        self.W = self.LARGEUR - 2 * self.MARGE
        # la hauteur du grpahique
        self.H = self.HAUTEUR - 2 * self.MARGE
        # La distance au haut de la fenêtre
        self.DIST_HAUT = 680
        # La distance à gauche du graphique du pays
        self.GAUCHE = 100 #920
        # Coordonnées du graphique pays
        self.BORD_GRAPHIQUE = (self.GAUCHE + self.MARGE, self.DIST_HAUT + self.HAUT,
                                    self.GAUCHE + self.LARGEUR - self.MARGE, self.DIST_HAUT + self.MARGE)
        # Coefficient entre la largeur du graphique et sa valeur en ce point
        self.COEF_LARGEUR = 1.089 / self.LARGEUR
        # Coefficient entre la hauteur du graphique et sa valeur en ce point
        self.COEF_HAUTEUR = 1.189 / self.HAUTEUR
        # Coordonnées du graphique mondial
        self.BORD_GRAPHIQUE = (self.GAUCHE + self.MARGE, self.DIST_HAUT + self.HAUT,
                                  self.GAUCHE + self.LARGEUR - self.MARGE, self.DIST_HAUT + self.MARGE)

        # Si l 'affichage est sur un pays
        self.sur_pays = sur_pays
        self.param_dict_monde = {}


    def generer_donnee(self, jour):
        """ Fait avancer la simulation d'un jour
        ---
        paramètres :

            - jour (int) le jour de la simulation
        """
        # Le dictionnaire des données mondiale
        dict_monde = {clee: 0 for clee in self.clees}
        self.N = 0
        # On vérifie si la date minimale de la base de donnée n'a pas été trouvée
        verifier_date = False
        if self.pays_pour_date is None:
            verifier_date = True
            min_date = "9999-99-99"
        # Si la date n'a pas été trouvé
        if verifier_date:
            # On initialize chaque pays en récupérant le premier jour des données fournies
            for n in range(len(self.models)):
                model = self.models[n]
                mdate = model.jour_depuis_id(self.gbdd, 1)
                if mdate < min_date:
                    self.pays_pour_date = n
                    min_date = mdate
        # La date de cette itération
        date = self.models[self.pays_pour_date].jour_depuis_id(self.gbdd, jour)
        # On itére sur chaque pays
        for n in range(len(self.models)):
            model = self.models[n]
            # On le met à jour et on met à jour les données de l'affichage
            model.mise_a_jour(self.gbdd, date)
            for x in range(self.nb_param):
                clee = self.clees[x]
                val = model.param_dict[clee]["value"]
                self.param_dict[n][clee].append(val)
                # On ajoute les valeurs du pays à celle du monde
                dict_monde[clee] += val
            # On ajoute le nombre de personnes vivantes du pays à celui du monde
            self.N += model.N
        # On met à jour les données mondiale et la date
        for x in range(self.nb_param):
            self.param_dict_monde[self.clees[x]].append(dict_monde[self.clees[x]])
        self.liste_date = self.models[self.pays_pour_date].date


    def retour_monde(self):
        """ Change le graphique pour afficher les données mondiales
        ---
        """
        self.mettre_a_jour_monde()
        self.afficher_monde()


    def changer_pays(self, numero_pays):
        """ Change le graphique du pays donnés
        ---
        paramètres :

            - numero_pays (int) le numéro du pays donné
        """
        # Si le pays est dans la base de données
        if numero_pays < len(self.liste_tag):
            # On récupère le tag et le pays correspondant
            tag = self.liste_tag[numero_pays]
            a = [n for n in range(len(self.models)) if self.models[n].pays.tag == tag]
            # L'affichage doit désormais afficher les données de ce pays
            self.pays_selectione = numero_pays
            # Si le pays a été trouvé
            if len(a) > 0:
                self.num_model = a[0]
                # On met à jour l'intitulé du graphique
                creer_masque(650, self.GAUCHE - 5, self.LARGEUR, 30, BG, self.ecran)
                centrer_texte(
                    self.ecran, self.police, f"Evolution locale ({self.models[self.num_model].pays.nom})", FG, self.LARGEUR, 30,
                    650, self.GAUCHE - 5)
                # On met à jour la barre d'informations
                self.mettre_a_jour_information_pays()
                # Si on a au moins deux points, on peut afficher les données
                if len(self.param_dict[self.num_model][self.clees[0]]) >= 2:
                    self.afficher_pays()
                # On "efface" la barre d'information
                creer_masque(self.DIST_HAUT + 10, self.GAUCHE - 80, 100, self.HAUTEUR - self.MARGE, BG, self.ecran)
                creer_masque(self.DIST_HAUT - 10, self.GAUCHE + 25, 5, self.HAUTEUR - self.MARGE, BG, self.ecran)
                # Cherche la valeur maximale pour avoir la hauteur maximale du graphique
                mx = max([max(self.param_dict[self.num_model][x]) for x in self.param_dict[self.num_model]])
                # On affiche les traits sur le graphique et on ajoute le nombre à côté
                if mx > 0:
                    x_coord = echelloner_valeur(0, mx, 10)
                    dx = self.H / mx
                    for x in x_coord:
                        form = "{:.2e}".format(int(x))
                        w = self.police_donnee.size(form)[0]
                        Y = self.HAUT - int(x * dx)
                        pygame.draw.line(self.ecran, FG, (self.MARGE + self.GAUCHE, Y + self.DIST_HAUT),
                                        (self.MARGE - 5 + self.GAUCHE, Y + self.DIST_HAUT), 2)
                        self.ecran.blit(
                            self.police_donnee.render(form, True, FG),
                            ((self.MARGE - w) + self.GAUCHE - 10, Y - 10 + self.DIST_HAUT))

            # Par défaut on affiche le monde
            else:
                if not self.sur_pays:
                    self.retour_monde()


    def effacer_graphique(self):
        """ On "efface" le graphique
        ---
        """
        creer_masque(self.DIST_HAUT + self.MARGE, self.GAUCHE + self.MARGE + 2,
                    self.LARGEUR - 2 * self.MARGE, self.HAUTEUR - 2 * self.MARGE, BG, self.ecran)
        creer_masque(self.DIST_HAUT + self.HAUTEUR - self.MARGE + 2, self.GAUCHE + self.MARGE - 70,
                    self.LARGEUR - self.MARGE + 90, self.MARGE, BG, self.ecran)
        creer_masque(self.DIST_HAUT + 10, self.GAUCHE - 80, 112, self.HAUTEUR - self.MARGE, BG, self.ecran)


    def afficher_axes(self):
        """ Affiche les axes
        ---
        """
        # On affiche l'axe des abscisses
        pygame.draw.line(self.ecran, FG, (self.MARGE + self.GAUCHE, self.HAUT + self.DIST_HAUT),
                        (self.LARGEUR - self.MARGE + 10 + self.GAUCHE, self.HAUT + self.DIST_HAUT), 2)

        # On affiche l'axe des ordonnées
        pygame.draw.line(self.ecran, FG, (self.MARGE + self.GAUCHE, self.MARGE - 10 + self.DIST_HAUT),
                            (self.MARGE + self.GAUCHE, self.HAUT + self.DIST_HAUT), 2)


    def afficher_graphique(self, param_dict, modele):
        """ On affiche les axes, graduations et les courbes
        ---
        paramètres :

            - param_dict (dict(str: list(float))) le dictionnaire des valeurs de la courbe
            - modele (Modele) le modèle dont on doit tracer la courbe
        """
        # Cherche la valeur maximale pour avoir la hauteur maximale du graphique
        mx = max([max(param_dict[x]) for x in self.clees])
        # La valeur maximale de l'abcsisse
        my = self.y[-1]

        # On échellone les valeurs sur 10 points
        x_coord = echelloner_valeur(0, mx, 10)
        if mx > 0:
            # Le ratio pour redimesionner les courbes pour qu'elles rentrent dans le graphique
            dx = self.H / mx
            dy = self.W / my
            # On affiche les informations sur les des ordonnées
            for x in x_coord:
                # On formmatte le nombre
                texte_nombre = "{:.2e}".format(int(x))
                # On calcule la positon
                largeur = self.police_donnee.size(texte_nombre)[0]
                hauteur = self.HAUT - int(x * dx)
                # On affiche la graduation
                pygame.draw.line(self.ecran, FG, (self.MARGE + self.GAUCHE, hauteur + self.DIST_HAUT),
                                    (self.MARGE - 5 + self.GAUCHE, hauteur + self.DIST_HAUT), 2)
                # On affiche le texte
                self.ecran.blit(
                    self.police_donnee.render(texte_nombre, True, FG),
                    ((self.MARGE - largeur) + self.GAUCHE - 10, hauteur - 10 + self.DIST_HAUT))

            # Affiche les courbes
            for clee in self.clees:
                # La liste des points de la courbe
                liste_x = [(mx - x) * dx + self.MARGE + self.DIST_HAUT for x in param_dict[clee]]
                liste_y = [x * dy + self.MARGE + self.GAUCHE for x in self.y]
                # Les points de l'abcsisse
                pts = list(zip(liste_y, liste_x))
                # On trace une ligne entre deux points
                for x in range(len(pts) - 1):
                    pygame.draw.line(self.ecran, self.color_dict[clee], pts[x], pts[x + 1], 2)

            # On affiche les informations sur l'axes des abcsisses
            y_coord = echelloner_valeur(0, my, 5)
            for y in y_coord:
                # On calcule le décalage
                decalage_gauche = self.MARGE + int(y * dy)
                # On récupère le numéro de la date
                numero_date = int(y)
                # Si la date existe
                if numero_date >= len(modele.date):
                    numero_date = -1
                # On récupère la date
                date = modele.date[numero_date]
                # On calcule la position du texte
                largeur, _ = self.police.size(date)
                # On affiche la graduation
                pygame.draw.line(self.ecran, FG, (self.GAUCHE + decalage_gauche, self.HAUT + self.DIST_HAUT),
                                (self.GAUCHE + decalage_gauche, self.LONGEUR_TRAIT + self.DIST_HAUT), 2)
                # On affiche la date
                self.ecran.blit(self.police_donnee.render(date, True, FG), (self.GAUCHE + decalage_gauche - largeur // 2 + 7, self.LONGEUR_TRAIT + self.DIST_HAUT + 5))


    def afficher_pays(self):
        """ Affiche le graphique du pays donné
        ---
        """
        # Cherche la valeur maximale pour avoir la hauteur maximale du graphique
        self.effacer_graphique()
        self.afficher_graphique(self.param_dict[self.num_model], self.models[self.num_model])
        self.afficher_axes()


    def afficher_monde(self):
        """ Affiche le graphique du monde
        ---
        """
        self.effacer_graphique()
        self.afficher_graphique(self.param_dict_monde, self.models[self.pays_pour_date])
        self.afficher_axes()


    def mettre_a_jour(self, fleche_retour):
        """ Change les informations à l'écran et la couleur du pays séléctionné
        ---
        paramètres :

            - fleche_retour (pygame.Image) la flèche de retour
        """
        model = self.mettre_a_jour_information_pays()
        # On efface la carte du monde
        creer_masque(0, 1550, 400, 120, BG, self.ecran)
        # On affiche le nom
        afficher_texte(self.ecran, model.pays.nom, (1600, 30), 60, 300, 80)
        # On "efface" le monde
        creer_masque(30, 10, 1540, 620, BG, self.ecran)
        # On redimensionne le pays
        border = redimensionner_pays(model.pays, 1500, 500, 50, 20)
        # On l'affiche
        for c in border:
            # On affiche le fond du pays
            pygame.draw.polygon(self.ecran, (model.pays.r, model.pays.g, model.pays.b), c)
            # On affiche les frontières
            pygame.draw.lines(self.ecran, FG, True, c, 1)
        # On affiche le carré et la flèche de retour au centre
        pygame.draw.rect(self.ecran, FG, (40, 520, 70, 70), 1)
        self.ecran.blit(fleche_retour, (50, 530))


    def mettre_a_jour_monde(self):
        """ Met à jour les informations mondiales
        ---
        """
        # On change la barre d'information
        creer_masque(0, 1550, 400, 120, BG, self.ecran)
        afficher_texte(self.ecran, "Monde", (1600, 30), 60, 300, 80)
        self.mettre_a_jour_information_monde()
        # On change le titre du grahique
        creer_masque(650, self.GAUCHE - 5, self.LARGEUR, 30, BG, self.ecran)
        centrer_texte(
            self.ecran, self.police, f"Evolution mondiale", FG, self.LARGEUR, 30,
            650, self.GAUCHE - 5)


    def mettre_a_jour_information_pays(self):
        """ Affiche les valeurs du pays sélétionnné
        ---
        """
        # On change la barre d'information
        creer_masque_information(self.nb_param, self.ecran)
        model = self.models[self.num_model]
        # On affiche la population du monde
        centrer_texte(self.ecran, self.police_donnee, f"{model.N}", FG, 300, 50, 160, 1600)
        x = 1
        for clee in model.param_dict:
            if not clee in self.liste_noire:
                # On affiche la valeur du monde associée à la clée
                centrer_texte(self.ecran, self.police_donnee,
                            f"{int(model.param_dict[clee]['value'])}", FG, 300, 40, 175 + self.DELTA * x, 1600)
                x += 1
        return model


    def mettre_a_jour_information_monde(self):
        """ Affiche les valeurs mondiales
        ---
        """
        # On change la barre d'information
        creer_masque_information(self.nb_param, self.ecran)
        centrer_texte(self.ecran, self.police_donnee, f"{self.N}", FG, 300, 50, 160, 1600)
        x = 1
        for clee in self.param_dict_monde:
            if clee not in self.liste_noire:
                centrer_texte(self.ecran, self.police_donnee, f"{int(self.param_dict_monde[clee][-1])}", FG, 300, 40, 175 + self.DELTA * x, 1600)
                x += 1


    def valeur_sur_graphique(self):
        """ Affiche les valeurs du graphique à la position de la souris
        ---
        résultat :

            - int, int
        """
        # Si un masque doit être créé pour réécrire les valeur au point de la souris
        if self.mettre_masque:
            creer_masque(600, 10, 200, 70, BG, self.ecran)
            self.mettre_masque = False

        # la position de la souris sur l'écran
        x, y = pygame.mouse.get_pos()
        if self.sur_pays:
            # Si la souris est sur le graphique pays
            if dans_rect(self.BORD_GRAPHIQUE, x, y) and len(self.param_dict_monde):
                # On convertit l'abcsisse en un entier qui sera le numéro associé à la date
                numero_date = int((x - self.BORD_GRAPHIQUE[0]) * self.COEF_LARGEUR * len(self.param_dict_monde[self.clees[0]]))
                # Si le numéro est plus grand que les dates existantes
                if numero_date >= len(self.models[self.num_model].date):
                    numero_date = -1
                # On affiche la date
                centrer_texte(
                    self.ecran, self.police_donnee,
                    f"Date : {self.models[self.num_model].date[numero_date]}",
                    FG, 150, 50, 600, 15)
                # On affiche la valeur
                centrer_texte(
                    self.ecran, self.police_donnee, "Valeur : {:.2e}".format(
                        int((self.BORD_GRAPHIQUE[1] - y) * self.COEF_HAUTEUR * max([max(self.param_dict[self.num_model][x]) for x in self.param_dict[self.num_model]]))),
                    FG, 150, 50, 630, 15)
                self.mettre_masque = True
        else:
            # Si la souris est sur le graphique mondial
            if dans_rect(self.BORD_GRAPHIQUE, x, y) and len(self.param_dict_monde):
                # On convertit l'abcsisse en un entier qui sera le numéro associé à la date
                numero_date = int((x - self.BORD_GRAPHIQUE[0]) * self.COEF_LARGEUR * len(self.param_dict_monde[self.clees[0]]))
                # Si le numéro est plus grand que les dates existantes
                if numero_date >= len(self.liste_date):
                    numero_date = -1
                # On affiche la date
                centrer_texte(
                    self.ecran, self.police_donnee,
                    f"Date : {self.liste_date[numero_date]}",
                    FG, 150, 50, 600, 15)
                # On affiche la valeur
                centrer_texte(
                    self.ecran, self.police_donnee, "Valeur : {:.2e}".format(
                        int((self.BORD_GRAPHIQUE[1] - y) * self.COEF_HAUTEUR * max([max(self.param_dict_monde[x]) for x in self.clees]))),
                    FG, 150, 50, 630, 15)
                self.mettre_masque = True
        return x, y


    def initialisation_affichage(self):
        """ Affiche les paramètres de la simulation
        ---
        """
        x = 1
        for clee in self.clees:
            pygame.draw.line(
                self.ecran, self.color_dict[clee],
                (1700, 175 + self.DELTA * x),
                (1800, 175 + self.DELTA * x),
                2)
            centrer_texte(self.ecran, self.police, " ".join(clee.split("_")), FG, 300, 50, 130 + self.DELTA * x, 1600)
            x += 1


    def initialisation_modeles(self):
        """ Initialise les paramètres d'affichage
        ---
        """
        # On récupère les paramètres de la base de donnée
        self.ex_param = {clee: self.models[0].param_dict[clee] for clee in self.models[0].param_dict
                         if clee not in self.liste_noire}
        # Le nombre de paramètre
        self.nb_param = len(self.ex_param)
        # La liste des paramètres
        self.clees = list(self.ex_param.keys())
        # Le nombre de personne vivantes
        self.N = 0
        # La liste des paramètre de chaque pays du monde
        self.param_dict = []
        # On itère sur chaque pays
        for model in self.models:
            # On ajoute les données
            self.param_dict.append({clee : [model.param_dict[clee]["value"]] for clee in self.clees})
            # On ajoute le nombre de personne à ceux du monde
            self.N += model.N
        # La liste des abscisses
        self.y = [0]
        # Le numéro du pays qu'on affiche
        self.num_model = 0
        # Les données mondiales
        self.param_dict_monde = {clee: [0] for clee in self.clees}
        # On ajoute les données de chaque pays aux données mondiales
        for x in range(len(self.param_dict)):
            for n in range(self.nb_param):
                clee = self.clees[n]
                self.param_dict_monde[clee][0] += self.param_dict[x][clee][0]
        # Les couleurs des courbes
        self.color_dict = {x: model.param_dict[x]["color"] for x in self.ex_param}
        # Le nombre de jour dont on a les données par pays
        self.nb_iterations = [model.nb_iterations for model in self.models]
        self.DELTA = 750 / self.nb_param


    def run(self):
        """ Lance la simulation et l'affichage du graphique
        ---
        """
        # Affiche les pays
        for c in self.gbdd.liste_pays:
            c.afficher(self.ecran)
        # Affiche mes textes
        centrer_texte(self.ecran, self.police, "Population de départ", FG, 300, 50, 130, 1600)
        self.ecran.blit(self.police.render("Épidémie de COVID-19", True, FG), (20, 0))
        # Récupère les modèles et initialise la simulation
        self.models = self.gbdd.liste_modeles
        # On charge les pays
        self.initialisation_modeles()
        # On charge les donées du monde
        self.mettre_a_jour_monde()
        # On affiche les éléments qui ne bougeront jamais
        self.initialisation_affichage()
        x = 1
        # On récupère les données du premier jour
        self.generer_donnee(x)
        while x < self.nb_iterations[self.pays_pour_date]:
            # On ajoute un jour à l'abcsisse
            self.y.append(len(self.y))
            # On récupère les données du jour
            self.generer_donnee(x)
            # Met à jour les données associée à la position de la souris sur le graphique si elle y est
            self.valeur_sur_graphique()
            # Affiche soit les donnée du pays soit celles du monde
            if self.sur_pays:
                self.mettre_a_jour_information_pays()
            else:
                self.mettre_a_jour_information_monde()
            # Si on peut construire un graphique, on le fait
            if len(self.param_dict[self.num_model][self.clees[0]]) >= 2:
                # Si on est sur un pays
                if self.sur_pays:
                    self.afficher_pays()
                # Sinon on affiche le monde
                else:
                    self.afficher_monde()
                pygame.display.update()
            # On passe au jour suivant
            x += 1
        # On se déconnecte de la base de données, puisque tout a été chargé
        self.gbdd.fermer()

# Predict°
