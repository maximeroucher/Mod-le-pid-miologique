import json
import os
import re

# Mute l'import de pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'True'
# Postionne la fenêtre de l'application
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

import pygame
from shapely.geometry import Point, Polygon

from Pays import Pays

# Couleur du texte
FG = (182, 185, 190)
# Couleur de fond
BG = (32, 34, 37)
# Couleur de la quarataine
QC = (44, 56, 126)


# Vérification position point

def dans_rect(points, x, y):
    """ Vérifie si un point est dans un rectangle
    ---
    paramètres :

        - points (list) liste des points (l, b, r, t)
        - x (int) position x de la souris
        - y (int) position y de la souris

    résultat :

        - bool
    """
    return points[0] <= x and points[3] <= y and points[1] >= y and points[2] >= x


def dans_poly(point, points_poly):
    """ Vérifie si un point est dans un polygone
    ---
    paramètres :

        - point (tuple(x, y)) point à verifier
        - polypoint (list(tuple)) liste des points d'un polygone

    résultat :

        - bool
    """
    return Polygon(points_poly).contains(Point(point))


# Conservation données

def depuis_json(donnees):
    """ Charge un pays d'après un dictionnaire Json
    ---
    paramètre :

        - donnees (dict) le dictionnaire des pays

    résultat :

        - list(Pays) liste des pays
    """
    liste_pays = []
    for pays in donnees:
        nom = list(pays.keys())[0]
        donnees_pays = pays[nom]
        liste_pays.append(Pays(nom, donnees_pays["NAME_FR"], donnees_pays["POP_EST"], donnees_pays["geometry"], donnees_pays["bounds"]))
    return liste_pays


def vers_json(liste_pays):
    """ Exporte la liste de pays en liste de dictionnaire
    ---
    paramètre :

        - liste (list(Pays)) liste des pays

    résultat :

        - list(dist) liste des dictionnaires des pays
    """
    return [x.vers_json() for x in liste_pays]


### Affichage


# Texte

def formattage_texte(text, taille_police, largeur, hauteur):
    """ Met le texte en forme pour occuper tout l'espace disponnible
    ---
    paramètres :

        - text (str) le texte à afficher
        - taille_police (int) la taille maximale du texte
        - largeur (int) la largeur maximale que peut occuper le texte
        - hauteur (int) la hauteur maximale que peut occuper le texte

    résultats :

        - list(str) le texte séparer sur plusieurs lignes pour améliorer l'affichage
        - pygame.font.SysFont la font qui maximise l'espace occupé
    """
    # On récupère la liste des mots
    liste_mots = text.split(" ")
    convenable = False
    # La police par défaut
    police = pygame.font.SysFont("montserrat", taille_police)
    while not convenable:
        teminer, matrice_mots, ligne_mots = True, [], []
        # Le dictionnaire qui à chaque mot associe sa taille pour cette police
        dict_largeur_mots = {mot: police.size(mot + " ") for mot in liste_mots}
        largeur_ligne_mots = len(ligne_mots)
        for mot in liste_mots:
            # Si un mot est plus large que l'espace disponible
            if dict_largeur_mots[mot][0] > largeur:
                # On diminue la taille de la police
                taille_police -= 1
                # On ne s'arrête donc pas
                teminer = False
                # On n'as pas besoin de continuer
                break
        # Si tout les mots
        if teminer:
            for mot in liste_mots:
                # Le taille du mot
                size = dict_largeur_mots[mot][0]
                # Si la largeur des mots de la ligne avec ce mot est plus petite que la largeur
                if largeur_ligne_mots + size <= largeur:
                    # On ajoute ce mot à la ligne
                    ligne_mots.append(mot)
                    # On augmente la largeur de la ligne
                    largeur_ligne_mots += size
                else:
                    # On ajoute la ligne à la matrice de mot
                    matrice_mots.append(ligne_mots)
                    # On commence une nouvelle ligne
                    ligne_mots, largeur_ligne_mots = [mot], size
            # On ajoute la dernière ligne de mots
            matrice_mots.append(ligne_mots)
            # Si la hauteur de cet réparition de mots est supérieure à la hauteur donnée
            if len(matrice_mots) * police.size(matrice_mots[0][0])[1] > hauteur:
                # On réduit la taille de la police
                taille_police -= 1
            else:
                # Cet configuration convient
                convenable = True
        # On recrée la police
        police = pygame.font.SysFont("montserrat", taille_police)
    # On concatène la matrice de mots
    matrice_mots = [" ".join(x) for x in matrice_mots]
    return matrice_mots, police


def afficher_texte(surface, text, pos, taille_police, largeur, hauteur, color=FG):
    """ Optimise l'affichage d'un texte sur un espace donné
    ---
    paramètres :

        - surface (pygame.Surface) la surface sur laquelle écrire
        - text (str) le texte à afficher
        - pos (tuple(x, y)) la position (t, l) d'origine de l'espace
        - taille_police (int) la taille maximale du texte
        - largeur (int) la largeur de l'espace
        - hauteur (int) la hauteur de l'espace
        - color ((r, g, b)) la couleur du texte
    """
    gauche, haut = pos
    matrice_texte, police = formattage_texte(text, taille_police, largeur, hauteur)
    # On centre chaque ligne
    for n in range(len(matrice_texte)):
        largeur_ligne, hauteur_ligne = police.size(matrice_texte[n])
        surface.blit(police.render(matrice_texte[n], True, color), (gauche + (largeur - largeur_ligne) // 2, haut + n * hauteur_ligne))


def centrer_texte(surface, police, text, color, largeur, hauteur, haut, gauche):
    """ Centre le texte au milleu de l'espace donné
    ---
    paramètres :

        - surface (pygame.Surface) la surface sur laquelle écrire
        - police (pygame.font.SysFont) la police avec laquelle écrire
        - text (str) le texte à afficher
        - color ((r, g, b)) la couleur du texte à afficher
        - largeur (int) la largeur de l'espace
        - hauteur (int) la hauteur de l'espace
        - haut (int) la distance entre le haut de la fenêtre et le haut de l'espace
        - gauche (int) la distance entre la gauche de la fenêtre et la gauche de l'espace
    """
    largeur_texte, hauteur_texte = police.size(text)
    surface.blit(police.render(text, True, color), (gauche + (largeur - largeur_texte) // 2, haut + (hauteur - hauteur_texte) // 2))


# Masques

def creer_masque(haut, gauche, largeur, hauteur, color, ecran):
    """ Créer un masque pour réécrire du texte
    ---
    paramètres :

        - haut (int)
        - gauche (int)
        - largeur (int)
        - hauteur (int)
        - color ((r, g, b)) la couleur du masque
        - ecran (pygame.Surface) la surface sur laquelle afficher le pays
    """
    masque = pygame.Surface((largeur, hauteur), pygame.SRCALPHA)
    masque.fill(color)
    ecran.blit(masque, (gauche, haut))


def creer_masque_information(nombre_masque, ecran):
    """ Met des masques sur les textes qui doivent être changés
    ---
    paramètres :

        - nombre_masque (int) le nombre de masque a créer
        - ecran (pygame.Surface) la surface sur laquelle afficher le pays
    """
    w = 750 / nombre_masque
    creer_masque(170, 1695, 110, 50, BG, ecran)
    for x in range(1, nombre_masque + 1):
        creer_masque(177 + w * x, 1695, 110, 50, BG, ecran)


# Redimensionnement

def redimensionner_pays(pays, largeur, hauteur, haut, gauche):
    """ Calcule la redimension des bords du pays afin de le zoomer
    ---
    paramètres :

        - pays (Pays) le pays à redimensionner
        - largeur (int) la largeur maximale
        - hauteur (int) la hauteur maximale
        - haut (int) la distance au haut de l'écran
        - largeur (int) la distance à gauche de l'écran

    résultat :

        - list(list(tuple)) liste des frontières des parties du pays redimensionné
    """
    # Les extremas des fontières du pays
    min_gauche = min([x[0] for x in pays.carre])
    min_haut = min([x[3] for x in pays.carre])
    max_droite = max([x[2] for x in pays.carre])
    max_bas = max([x[1] for x in pays.carre])
    # la hauteur et la largeur du pays
    hauteur_pays = max_bas - min_haut
    largeur_pays = max_droite - min_gauche
    # Le ratio pour redimensionner les frontières du pays
    ratio = min(largeur / largeur_pays, hauteur / hauteur_pays)
    # L'espace à ajouter à gauche pour centrer le pays
    espace_gauche = (largeur - (largeur_pays * ratio)) // 2
    # L'espace à ajouter en haut pour centrer le pays
    espace_haut = (hauteur - (hauteur_pays * ratio)) // 2
    nouvelles_frontieres = []
    # Les pays peuvent avoir des îles donc on redimensionne tout
    for ile in pays.frontiere:
        nouvelle_frontiere = []
        # On redimensionne tout les point de l'île
        for point in ile:
            nouvelle_frontiere.append([(point[0] - min_gauche) * ratio + gauche + espace_gauche, (point[1] - min_haut) * ratio + haut + espace_haut])
        nouvelles_frontieres.append(nouvelle_frontiere)
    return nouvelles_frontieres


def echelloner_valeur(val_min, val_max, nb_pt):
    """ Créer une échelle de valeur
    ---
    paramètres :

        - val_min (int) la valeur minimale de l'échelle
        - val_max (int) la valeur maximale de l'échelle
        - nb_pt (int) le nombre de point de l'échelle

    résultat :

        - list(int)
    """
    # Si on a moins de point que le nombre de point demandés
    if val_max - val_min < nb_pt:
        return [val_min + x for x in range(val_max - val_min + 1)]
    # La différence entre deux points
    delta = (val_max - val_min) / nb_pt
    return [x * delta + val_min for x in range(nb_pt + 1)]


# Trouver la base de donnée

def trouverBdd():
    """ Trouve la base de donnée pour entrainer le réseau de neurones
    ---
    résultat :

        - str (le chemin vers la base de donnée)
    """
    # Parmis les fichiers qui saont dans le même dossier
    for fichier in os.listdir():
        # Si un fichier est de la forme Epidémie-COVID-****-**-**.db où * sont des entiers
        resultat = re.search(r"Epidémie-COVID-\d{4}-\d{2}-\d{2}.db", fichier)
        if resultat:
            # On le renvoie, "./" indique que ce fichier est dans le même dossier que ce fichier
            return "./" + resultat.group()

