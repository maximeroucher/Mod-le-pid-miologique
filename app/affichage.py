import os
import random

import msgpack

# Empêche l'import de pygame d'afficher du texte
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'True'
# Postionne la fenêtre de l'application
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

import pygame

from GestionnaireAffichage import GestionnaireAffichage
from outils import BG, creer_masque, dans_poly, dans_rect, depuis_json

# Le nombre d'images par seconde
FPS = 60

# Code du clic gauche de la souris
LEFT = 1


# Couleur de fond
HEXBG = "#36393f"
# Couleur du texte, des axes des graphiques et des bords des pays
HEXFG = "#B6B9BE"

# Coordonnées du carré du bouton (gauche, bas, droite, haut)
BTN_BOUND = [40, 590, 110, 520]


### Outils
fichier = open("Pays.msgpack", "rb")
donnees_binaires = fichier.read()
donnees = msgpack.unpackb(donnees_binaires)

# On récupère la liste des pays
liste_pays = depuis_json(donnees)
liste_pays.sort()

pygame.init()

# Img
fleche_retour = pygame.transform.scale(pygame.image.load("fleche_retour.png"), (50, 50))

# Font
police = pygame.font.SysFont("montserrat", 24)
police_donnees = pygame.font.SysFont("montserrat", 18)

# Initialisation de la fenêtre
info = pygame.display.Info()
# Fenêtre de 1x1 juste pour initialiser le gestionnaire d'affichage
ecran = pygame.display.set_mode((1, 1), pygame.NOFRAME)

# Horloge
clock = pygame.time.Clock()


a_change = False
# Liste des tag des pays
liste_tag = [c.tag for c in liste_pays]

# Le gestionnaire d'affichage
GA = GestionnaireAffichage(ecran, liste_pays, liste_tag, police, police_donnees, random.randint(0, len(liste_tag)), False, ["Sains"])

# Les fenêtres de menu
try:
    # Si on se connecte à la base de donnée
    if GA.gbdd.connection():
        # On en extrait les modèles
        GA.gbdd.extraire_modeles_depuis_bdd()
    else:
        quit()
except:
    quit()

# Redimensionne la fenêtre pour qu'elle prennent toute la fenêtre
ecran = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)
GA.ecran = ecran
ecran.fill(BG)

# Lance les graphiques
GA.start()


while True:
    clock.tick(FPS)

    # On gère les interactions utilisateurs
    for event in pygame.event.get():

        # On quitte le programme en appuyant sur Échap
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            quit()

        # On récupère la position de la souris et affiche les informations si elle est sur un GAique
        h = GA.valeur_sur_graphique()

        # Si on appuie avec la souris
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT:
            # Si on est sur la fenêtre
            if h:
                # on récupère la position selon les axes
                x, y = h
                # Si on voit carte du monde
                if not GA.sur_pays:
                    # Si on est dans le cadre de la carte du mode
                    if dans_rect((40, 650, 1550, 0), x, y):
                        # On regarde si on a cliqué sur un pays
                        for c in liste_pays:
                            # On commence par vérifier si on est dans la carre autour du pays
                            for cb in c.carre:
                                if dans_rect(cb, x, y):
                                    # On vérifie ensuite qu el'on est bien sur le pays
                                    for b in c.frontiere:
                                        if dans_poly((x, y), b):
                                            # On récupère le numéro associé au pays cliqué
                                            n = liste_tag.index(c.tag)
                                            # Si ce pays est différent de celui cliqué avant
                                            if GA.pays_selectione != n:
                                                # On change l'affichage des informations
                                                GA.changer_pays(n)
                                            # On est donc sur le pays, on doit donc mettre à jour les information
                                            a_change = GA.sur_pays = True
                                            # On ne peut être que sur u pays à la fois donc on s'arrête
                                            break


                else:
                    # Si on clique sur le bouton retour
                    if dans_rect(BTN_BOUND, x, y):
                        # On repasse sur la carte du monde et on affiche tout les pays
                        GA.sur_pays = False
                        GA.retour_monde()
                        creer_masque(30, 10, 1540, 620, BG, ecran)
                        for c in liste_pays:
                            c.afficher(ecran)

    # Si on doit changer les informations
    if a_change:
        a_change = False
        GA.mettre_a_jour(fleche_retour)

    # On met à jour l'image
    pygame.display.update()

# TODO:
#       - afficher reg à gch (+ delta)
#       - estimation tps calcul
