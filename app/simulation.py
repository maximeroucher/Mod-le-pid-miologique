from __future__ import print_function

import datetime
import math
import os
import random
import sqlite3
import time
from enum import Enum

from tqdm import tqdm

from outils import BG, FG, QC, centrer_texte, creer_masque, echelloner_valeur

# Empêche l'import de pygame d'afficher du texte
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'True'
# Postionne la fenêtre de l'application en haut à droite
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

import pygame

colors = [pygame.Color(20, 100, 255), pygame.Color(255, 100, 20), pygame.Color(100, 100, 100)]


class Etat(Enum):
    SAIN = 1
    INFECTE = 2
    RETABLI = 3


class Comportement(Enum):
    NORMAL = 1
    QUARANTAINE = 2
    DEPLACEMENT = 3

    def __str__(self):
        return self._name_.capitalize()


class Personne:

    def __init__(self, id, x, y, vx, vy, ax, ay, p, rayon):
        """ Initialisation de la personne
        ---
        paramètres :

            - id (int) l'identifiant de la personne
            - x (int) la position en absisce
            - y (int) la position en ordonnée
            - vx (float) la vitesse en absisce
            - vy (float) la vitesse en ordonnée
            - ax (float) l'accélération en absisce
            - ay (float) l'accélération en ordonnée
            - p (float 0 <= p <= 1) la probabilité de contaminer une personne
        """
        # L'identifiant de la personne
        self.id = id
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.ax = ax
        self.ay = ay
        self.p = p
        # En cas d'infection, la personne restera infecté pendant self.TPS_INFECTE itérations
        self.TPS_INFECTE = random.randint(40, 60)
        # État d'origine de la personne
        self.etat = Etat.SAIN
        self.comportement = Comportement.NORMAL
        # La vitesse maximale de déplacement de la personne
        self.VMAX = 5
        # La taille de la personne
        self.RAYON = rayon
        # Coefficient de frottement fluide
        self.f = 1
        # Coefficient de rappel de ressort
        self.k = 1


    def __eq__(self, autre):
        """ Égalité entre deux personnes
        ---
        paramètre :

            - autre (Personne) la personne dont on veut vérifier si c'est l'autre

        résultat :

            - bool (si la personne est l'autre)
        """
        return self.id == autre.id


    def correction_vitesse(self):
        """ Renormalise la vitesse si elle dépasse la vitesse maximale
        ---
        """
        v = self.vx ** 2 + self.vy ** 2
        if v > self.VMAX ** 2:
            r = self.VMAX / math.sqrt(v)
            self.vx *= r
            self.vy *= r


    def mise_a_jour(self, largeur_sim, hauteur_sim, personnes):
        """ Calcul de l'étape suivante
        ---
        paramètres :

            - largeur_sim (int) la largeur de l'espace de simulation
            - hauteur_sim (int) la hauteur de l'espace de simulation
            - personnes (list(Personne)) la liste des personnes de la simulation
        """
        # On remet l'accelération à zéro
        self.ax = self.ay = 0
        # Pendant une quarantaine, on introduit une force de répulsion pour éviter les contacts, et une force de frottement fluide pour stabiliser le mouvement
        if self.comportement == Comportement.QUARANTAINE:
            self.repulsion(personnes)
        # On applique le schéma d'Euler pour la vitesse
        self.vx += self.ax
        self.vy += self.ay
        # On renormalise la vitesse
        self.correction_vitesse()
        # Si on touche un bord, on part dans l'autre sens
        if self.x > largeur_sim or self.x < 0:
            self.vx = - self.vx
        if self.y > hauteur_sim  or self.y < 0:
            self.vy = - self.vy
        # On applique le schéma d'Euler pour la position
        self.x += int(self.vx)
        self.y += int(self.vy)
        # Si la personne est infectée
        if self.etat == Etat.INFECTE:
            # Un jour en étant infecté s'est écoulé
            self.TPS_INFECTE -= 1
        # Si la personne n'est plus infecté
        if self.TPS_INFECTE == 0:
            self.etat = Etat.RETABLI


    def repulsion(self, personnes):
        """ Calcule une force de répulsion entre les autres particules et celle-ci, dans le cas d'un confinement
        ---
        paramètre :

            - personnes (list(Personne)) la liste des personnes de la simulation
        """
        ax = ay = 0
        for autre in personnes:
            # On vérifie que l'on intergait pas avec la personne elle-même
            if autre is not self:
                # On vérifie que l'on est suffisament proche de la personne
                dx = abs(self.x - autre.x)
                if dx < 5 * self.RAYON:
                    dy = abs(self.y - autre.y)
                    if dy < 5 * self.RAYON:
                        # On calcule l'angle et la distance entre self et autre
                        angle = math.atan2(self.y - autre.y, self.x - autre.x)
                        d = math.hypot(dy, dx)
                        # La vitesse de la personne
                        v = math.hypot(self.vx, self.vy)
                        # La force causée par autre sur la personne
                        f = self.k * (d - 2 * self.RAYON)
                        # On calcule les composante selon les axes
                        ax += f * math.cos(angle)
                        ay += f * math.sin(angle)

        # On assigne les nouvelles valeurs d'accelération
        self.ax = ax - self.f * self.vx
        self.ay = ay - self.f * self.vy


    def couleur(self):
        """ Indique la couleur d'affichage en fonction de l'état
        ---
        résultat :

            - pygame.Color
        """
        if self.etat == Etat.SAIN:
            return colors[0]
        elif self.etat == Etat.INFECTE:
            return colors[1]
        return colors[2]


    def collision(self, autre):
        """ Vérifie s'il y a collision
        ---
        paramètre :

            - autre (Personne) la personne dont on veut vérifiée si elle est en collision avec self

        résultat :

            - bool (s'il y a collision entre les deux particules)
        """
        # On regarde si les particules sont suffisament proches
        dx = self.x - autre.x
        if dx < 1.5 * 2 * self.RAYON:
            dy = self.y - autre.y
            if dy < 1.5 * 2 * self.RAYON:
                # On regarde si la distance est inférieur à celle entre 2 diamètres
                return dx ** 2 + dy ** 2 <= 4 * 4 * self.RAYON ** 2
            return False
        return False


    def afficher(self, ecran, haut):
        """ Affiche la personne
        ---
        paramètres :

            - ecran (pygame.Surface) l'écran
            - haut (int) la distance au bord supérieur de la fenêtre
        """
        pygame.draw.circle(ecran, self.couleur(), (self.x, self.y + haut), self.RAYON)


class Simulation:

    def __init__(self, personnes, largeur_sim, hauteur_sim, ecran, taux_incidence, seuil):
        """ Initialisation de la simulation
        ---
        paramètres :

            - personnes (list(Personne)) la liste de personne de la simulation
            - largeur_sim (int) la largeur de l'espace de la simulation
            - hauteur_sim (int) la hauteur de l'espace de la simulation
            - ecran (Pygame.Surface) la surface sur laquelle afficher la simulation
            - taux_incidence (int) le nombre de personnes infectés simultanément avant de mettre en place une quarantaine
            - seuil (float 0 <= seuil <= 1) le pourcentage de taux_incidence à atteindre afin de mettre fin à la quarantaine
            - comportement_urgence (Comportement) le comportement de la simulation si le nombre d'inféctés est supérieur à taux_incidence
        """
        self.personnes = personnes
        # On infecte une personne
        self.personnes[0].etat = Etat.INFECTE
        # On assigne les personnes
        self.sains = self.personnes[0:-1]
        self.infectes = [self.personnes[0]]
        self.retablis = []

        # les dimensions de l'espace de la simulation
        self.largeur_sim = largeur_sim
        self.hauteur_sim = hauteur_sim

        # La liste de l'abscisse
        self.y = [0]

        # Les données de la simulation
        self.donnees = {"Sains": [], "Infectés": [], "Rétablis": []}
        # Les polices d'écriture pour l'affichage
        self.police_donnees = pygame.font.SysFont("montserrat", 18)
        self.police = pygame.font.SysFont("montserrat", 24)

        # On met à jour et on enregistre les données
        self.reassignation()
        self.mise_a_jour_donnees()

        # L'écran pour afficher les points
        self.ecran = ecran
        # Le comportement par défaut de la simulation
        self.comportement = Comportement.NORMAL
        # Le nombre d'infectés au dessus duquel une quarantaine est déclarée, si elle doit l'être
        self.TAUX_INCIDENCE = taux_incidence
        # Les dates de début et fin de quarantaine
        self.dates_quarantaine = []
        # La proportion d'infecté en dessous de laquelle le comportement redevient un comportement normal
        self.seuil = seuil

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
        self.largeur_graph = self.LARGEUR - 2 * self.MARGE
        # la hauteur du grpahique
        self.hauteur_graph = self.HAUTEUR - 2 * self.MARGE
        # La distance au haut de la fenêtre
        self.DIST_HAUT = 50
        # La distance à gauche du graphique du pays
        self.GAUCHE = 1100
        # Si on doit prendre des mesures d'urgence
        self.mesure_urgence = taux_incidence != 0
        # Si la simulation est termin
        self.terminee = False


    def initialisation_affichage(self):
        """ Initialisation de l'affichage de la simulation
        ---
        """
        # On affiche une fois pour toute le comportement de la simulation si il ne changera pas
        if not self.mesure_urgence:
            centrer_texte(self.ecran, self.police_donnees, "Aucunes mesures", FG, 500, 20, self.DIST_HAUT - 30, 1200)
        # Affichage de la légende
        for x, clee in enumerate(self.donnees):
            pygame.draw.line(
                self.ecran, colors[x],
                (1150 + 250 * x, self.DIST_HAUT + 440),
                (1250 + 250 * x, self.DIST_HAUT + 440),
                2)
            centrer_texte(self.ecran, self.police, clee, FG, 100, 50, self.DIST_HAUT + 400, 1150 + 250 * x)

        # la valeur maximale du graphique
        mx = len(self.personnes)
        # Le coefficient de proportionalité pour ramener les valeurs sur le graphique
        dx = self.hauteur_graph / mx

        # L'axe des ordonnées
        pygame.draw.line(self.ecran, FG, (self.MARGE + self.GAUCHE, self.MARGE - 10 + self.DIST_HAUT),
                         (self.MARGE + self.GAUCHE, self.HAUT + self.DIST_HAUT), 2)

        # 10 points équirépartis sur l'axe des ordonnées
        x_coord = echelloner_valeur(0, mx, 10)
        for x in x_coord:
            form = str(int(x))
            largeur = self.police_donnees.size(form)[0]
            Y = self.HAUT - int(x * dx)
            # On affiche les graduations et le nombre associé
            pygame.draw.line(self.ecran, FG, (self.MARGE + self.GAUCHE, Y + self.DIST_HAUT),
                             (self.MARGE - 5 + self.GAUCHE, Y + self.DIST_HAUT), 2)
            self.ecran.blit(
                self.police_donnees.render(form, True, FG),
                ((self.MARGE - largeur) + self.GAUCHE - 10, Y - 10 + self.DIST_HAUT))


    def mise_a_jour_graphique(self):
        """ Affiche le graphique du pays donné
        ---
        """
        # La valeur maximale des ordonées
        mx = len(self.personnes)
        # La valeur maximale de l'abcsisse (1 pour éviter une division par 0)
        my = max(self.y[-1], 1)

        # Les proporotions pour remettre les données à l'échelle
        dx = self.hauteur_graph / mx
        dy = self.largeur_graph / my

        # On "efface" le graphique
        creer_masque(self.DIST_HAUT + self.MARGE, self.GAUCHE + self.MARGE + 2,
                    self.LARGEUR - 2 * self.MARGE, self.HAUTEUR - 2 * self.MARGE, BG, self.ecran)
        # On "efface" la barre de l'abcsisse
        creer_masque(self.DIST_HAUT + self.HAUTEUR - self.MARGE + 2, self.GAUCHE + self.MARGE - 10,
                    self.LARGEUR - self.MARGE + 10, self.MARGE, BG, self.ecran)

        # les abcsisses des date de quarantaine
        c_y = [x * dy + self.MARGE + self.GAUCHE for x in self.dates_quarantaine]

        # On affiche en violet les périodes de quarantaine
        for x in range((len(c_y) + 1) // 2):
            # Si il existe un point après celui-ci, on sait où s'arrête
            if 2 * x + 1 < len(c_y):
                creer_masque(self.DIST_HAUT + self.MARGE, c_y[2 * x], c_y[2 * x + 1] - c_y[2 * x], self.HAUTEUR - 2 * self.MARGE, QC, self.ecran)
            # Sinon on s'arrête au bord du graphique
            else:
                creer_masque(self.DIST_HAUT + self.MARGE, c_y[2 * x], self.GAUCHE + self.LARGEUR - self.MARGE - c_y[2 * x], self.HAUTEUR - 2 * self.MARGE, QC, self.ecran)

        # On trace les courbes
        for clee in self.donnees:
            c_x = [(mx - x) * dx + self.MARGE + self.DIST_HAUT for x in self.donnees[clee]]
            c_y = [x * dy + self.MARGE + self.GAUCHE for x in self.y]
            pts = list(zip(c_y, c_x))
            for x in range(len(pts) - 1):
                pygame.draw.line(self.ecran, colors[list(self.donnees.keys()).index(clee)], pts[x], pts[x + 1], 2)

        # On affiche la légende de l'abcsisse
        y_coord = echelloner_valeur(0, my, 10)
        for y in y_coord:
            X = self.MARGE + int(y * dy)
            d = str(int(y))
            largeur, _ = self.police.size(d)
            pygame.draw.line(self.ecran, FG, (self.GAUCHE + X, self.HAUT + self.DIST_HAUT),
                             (self.GAUCHE + X, self.LONGEUR_TRAIT + self.DIST_HAUT), 2)
            self.ecran.blit(self.police_donnees.render(d, True, FG), (self.GAUCHE + X - largeur // 2 + 7, self.LONGEUR_TRAIT + self.DIST_HAUT))

        # On affiche l'axe des abcsisse
        pygame.draw.line(self.ecran, FG, (self.MARGE + self.GAUCHE, self.HAUT + self.DIST_HAUT),
                         (self.LARGEUR - self.MARGE + 10 + self.GAUCHE, self.HAUT + self.DIST_HAUT), 2)


    def mise_a_jour_donnees(self):
        """ Met à jour les données de la simulation
        ---
        """
        self.donnees["Sains"].append(len(self.sains))
        self.donnees["Infectés"].append(len(self.infectes))
        self.donnees["Rétablis"].append(len(self.retablis))


    def reassignation(self):
        """ Assigne les personnes dans leurs compartiments respectifs en fonction de leur état
        ---
        """
        p = 0
        # Tant que l'on a pas regarde chaque personne de self.infectes
        while len(self.infectes) - p > 0:
            # Si la personne est rétablie on la déplace
            if self.infectes[p].etat == Etat.RETABLI:
                self.retablis.append(self.infectes[p])
                self.infectes.pop(p)
            # Sinon on passe à la personne suivante
            else:
                p += 1
        p = 0
        # On fait de même avec les personnes saines
        while len(self.sains) - p > 0:
            if self.sains[p].etat == Etat.INFECTE:
                self.infectes.append(self.sains[p])
                self.sains.pop(p)
            else:
                p += 1


    def afficher(self):
        """ Affiche la simulation
        ---
        """
        # On "efface" l'espace de simulation
        creer_masque(self.DIST_HAUT - 50, -20, self.largeur_sim + 100, self.hauteur_sim + 20, BG, self.ecran)
        # On trace les ligne du contour de l'espace
        pygame.draw.line(self.ecran, pygame.Color(200, 200, 200), (0, self.DIST_HAUT - 50), (self.largeur_sim, self.DIST_HAUT - 50))
        pygame.draw.line(
            self.ecran, pygame.Color(200, 200, 200),
            (self.largeur_sim, self.DIST_HAUT - 50),
            (self.largeur_sim, self.hauteur_sim + self.DIST_HAUT - 50))
        pygame.draw.line(
            self.ecran, pygame.Color(200, 200, 200),
            (self.largeur_sim, self.hauteur_sim + self.DIST_HAUT - 50),
            (0, self.hauteur_sim + self.DIST_HAUT - 50))
        pygame.draw.line(self.ecran, pygame.Color(200, 200, 200), (0, self.hauteur_sim + self.DIST_HAUT - 50), (0, self.DIST_HAUT - 50))
        # On affiche chaque personne
        [p.afficher(self.ecran, self.DIST_HAUT - 50) for p in self.personnes]
        # On enregistre ce tour
        self.y.append(len(self.y))


    def mise_a_jour_texte(self):
        """ Change les chiffres de la simulation
        ---
        """
        # On change les informations si elles sont susceptibles de changer
        if self.mesure_urgence:
            # On "efface" l'en-tête du graphique et on affiche les informations
            creer_masque(self.DIST_HAUT - 30, 1200, 500, 100, BG, self.ecran)
            centrer_texte(self.ecran, self.police_donnees, "Comportement de la population : " + str(self.comportement), FG, 500, 20, self.DIST_HAUT - 30, 1200)
            centrer_texte(self.ecran, self.police_donnees,
                        f"Taux d'incidence : {self.TAUX_INCIDENCE}", FG, 500, 20, self.DIST_HAUT, 1200)
        # On met à jour le nombre de personnes dans chaque partie
        for x, clee in enumerate(self.donnees):
            creer_masque(self.DIST_HAUT + 455, 1150 + 250 * x, 100, 20, BG, self.ecran)
            centrer_texte(
                self.ecran, self.police_donnees, str(self.donnees[clee][-1]),
                FG, 100, 20, self.DIST_HAUT + 455, 1150 + 250 * x)


    def mise_a_jour(self):
        """ Met à jour la simulation
        ---
        """
        # On met à jour chaque personne
        for personnne in self.personnes:
            personnne.mise_a_jour(self.largeur_sim, self.hauteur_sim, self.personnes)
        # On regarde si il y a collision entre une personne infectée et une personne saine
        for personnne in self.infectes:
            # On a une probabilité p d'infecter une personne saine
            if random.randint(0, 100) <= personnne.p * 100:
                # Si le conctact doit infecter, on regarde la collision avec chaque personne saine
                for sain in self.sains:
                    # Si il y a collision
                    if personnne.collision(sain):
                        # La personne est alors infectée
                        sain.etat = Etat.INFECTE
        # Tant qu'il y a des infectés, il peut se passer quelque chose
        if len(self.infectes) > 0:
            # On réassigne les personnes et on fait avancer la simulation d'une itération
            self.reassignation()
            self.mise_a_jour_comportement()
            self.mise_a_jour_donnees()
            self.mise_a_jour_texte()
            self.mise_a_jour_graphique()
        # Sinon, la simulation est terminée
        else:
            self.terminee = True
        # On met à jour l'affichage
        pygame.display.update()


    def mise_a_jour_comportement(self):
        """ Met à jour le comportement de la simulation
        ---
        """
        # Si des mesures doivent être prises
        if self.mesure_urgence:
            # Si le nombre d'infecté dépasse le seuil critique et qu'aucune mesures n'est actuellement appliquée
            if len(self.infectes) > self.TAUX_INCIDENCE and self.comportement == Comportement.NORMAL:
                # On commence une quarantaine
                self.dates_quarantaine.append(self.y[-1])
                self.comportement = Comportement.QUARANTAINE
                # Toutes les personnes doivent s'éviter
                for p in self.personnes:
                    p.comportement = Comportement.QUARANTAINE
            # Si le nombre d'infecté est en dessous d'une proportion du seuil critique est qu'une quarantaine est en cours, on y met fin
            elif len(self.infectes) < self.TAUX_INCIDENCE * self.seuil and self.comportement == Comportement.QUARANTAINE:
                # On met fin à la quarantaine
                self.dates_quarantaine.append(self.y[-1])
                self.comportement = Comportement.NORMAL
                # Les personnes peuvent se déplacer normallement
                for p in self.personnes:
                    p.comportement = Comportement.NORMAL


# On lance le moteur graphique
pygame.init()
info = pygame.display.Info()

# On crée l'écran
ecran = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)
ecran.fill(BG)

# On récupère les dimensios de l'espace de simulation
largeur_sim = info.current_w // 2 - 10
hauteur_sim = info.current_h - 10

# Le nombre de simulation à faire
NB_SIM = 1
# Le fraction du seuil critique pour arrêter la quarantaine
SEUIL = 0.3
# Si on doit sauvegarder
SAUVEGARDER = False
# Le nombre de personnes de la simulation
NB_PERSONNES = 1200
# Le nombre de personnes infectés critique
TAUX_INCIDENCE = 100
# Le dossier de sauvegarde
NOM_DOSSIER = f"E:\\Python\\Projet\\TIPE\\Modele_epidemiologique\\app\\Simulation\\Taux incidence {TAUX_INCIDENCE}"


for _ in range(NB_SIM):
    # On crée aléatoirment les personnes
    personnes = []
    for k in range(NB_PERSONNES):
        v, theta = random.randint(0, 500) / 100, random.randint(0, 628) / 100
        vx, vy = v * math.cos(theta), v * math.sin(theta)
        personnes.append(
            Personne(k,
                random.randint(0, largeur_sim),
                random.randint(0, hauteur_sim),
                vx, vy, 0, 0, .5, 6))

    # On initialise la simulation
    Sim = Simulation(personnes, largeur_sim, hauteur_sim, ecran, TAUX_INCIDENCE, SEUIL)
    Sim.initialisation_affichage()

    # On crée une table dans la base de donnée pour enregistrer les donnée de la simulation
    if SAUVEGARDER:
        # On crée le dossier s'il n'existe pas
        if not os.path.exists(NOM_DOSSIER):
            os.makedirs(NOM_DOSSIER)
        # On se déplace dans ce dossier
        os.chdir(NOM_DOSSIER)
        # On se connecte à la base de donnée
        bdd = sqlite3.connect("result.db", check_same_thread=False)
        curseur = bdd.cursor()
        # On récupère le nombre de simulation
        l = len(curseur.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall())
        # On crée une table portant le numéro suivant
        curseur.execute(f"""CREATE TABLE IF NOT EXISTS Sim{l} (id integer PRIMARY KEY, {",".join([f'{clee} int' for clee in Sim.donnees])})""")


    x = 0
    # Boucle principale de la simulation
    while not Sim.terminee:
        # On gère les interactions avec l'utilisateur
        for event in pygame.event.get():
            # Si on appuie sur Échap
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # On ferme le programme
                quit()

        # On attend entre chaque itération
        time.sleep(.01)
        # On met à jour la simulation
        Sim.mise_a_jour()
        # On l'affiche
        Sim.afficher()
        if SAUVEGARDER:
            # On sauvegarde les nouvelles données
            curseur.execute(f"""INSERT INTO Sim{l} VALUES (NULL, {",".join([str(Sim.donnees[clee][x] / NB_PERSONNES) for clee in Sim.donnees])})""")
            bdd.commit()
            x += 1

    # On ferme la base de donnée
    if SAUVEGARDER:
        bdd.close()

    # On crée le dossier s'il n'existe pas
    if not os.path.exists(NOM_DOSSIER):
        os.makedirs(NOM_DOSSIER)

    # On sauvegarde la dernière image de la simulation
    pygame.image.save(Sim.ecran, f"{NOM_DOSSIER}\\Résultat - Personnes {NB_PERSONNES}, SEUIL {SEUIL}.jpg")


# TODO:
#       - opti affichage (au centre)

# pb test
# https://jamanetwork.com/journals/jama/fullarticle/2762130
