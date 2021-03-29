import json
import msgpack
import os
import random
import time

# Mute l'import de pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'True'
# Postionne la fenêtre de l'application
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

import pygame

from MainThread import MainThread
from tools import *

# Le nombre d'images par seconde
FPS = 60

# Code du clic gauche de la souris
LEFT = 1


# Couleur de fond
HEXBG = "#36393f"
# Couleur du texte, des axes des graphiques et des bords des pays
HEXFG = "#B6B9BE"

# Coordonnées du carré du bouton (l, b, r, t)
BTN_BOUND = [40, 590, 110, 520]


### Outils
with open("Country.msgpack", "rb") as data_file:
    byte_data = data_file.read()
    data = msgpack.unpackb(byte_data)

countries = from_json(data)
countries.sort()

pygame.init()

# Img
back_arrow = pygame.transform.scale(pygame.image.load("left-arrow.png"), (50, 50))

# Font
font = pygame.font.SysFont("montserrat", 24)
data_font = pygame.font.SysFont("montserrat", 18)
title_font = pygame.font.SysFont("montserrat", 44)

# Init fenêtre
info = pygame.display.Info()
# Fenêtre de 1x1 juste pour initialiser le thread
screen = pygame.display.set_mode((1, 1), pygame.NOFRAME)

# Horloge
clock = pygame.time.Clock()


changed = False
# Liste des tag des pays
c_tag = [c.tag for c in countries]

# Le Thread principale
graph = MainThread(screen, countries, c_tag, font, data_font, random.randint(0, len(c_tag)), True, False, ["Sains"])

# Les fenêtres de menu
try:
    if graph.tbm.connect():
        graph.tbm.extract_model_from_db()
    else:
        quit()
except:
    quit()

# Redimensionne la fenêtre
screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)
graph.screen = screen
screen.fill(BG)

# Lance les graphiques
graph.start()


while True:
    clock.tick(FPS)

    for event in pygame.event.get():

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            quit()

        h = graph.graph_value()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT:
            if h:
                x, y = h
                if not graph.zoomed:
                    if in_rect((40, 650, 1550, 0), x, y):
                        for c in countries:
                            for cb in c.bound:
                                if in_rect(cb, x, y):
                                    for b in c.border:
                                        if in_poly((x, y), b):
                                            n = c_tag.index(c.tag)
                                            if graph.num_country != n:
                                                graph.change_countries(n)
                                            changed = graph.zoomed = True
                                            graph.on_world = False
                                            break

                        else:
                            if not graph.on_world:
                                graph.update_world()
                                graph.on_world = True

                else:
                    if in_rect(BTN_BOUND, x, y):
                        graph.zoomed = graph.on_world = False
                        create_mask(30, 10, 1540, 620, BG, screen)
                        for c in countries:
                            c.show(screen)

    if changed:
        changed = False
        graph.update(back_arrow)

    pygame.display.update()

# TODO:
#       - afficher reg à gch (+ delta)
#       - estimation tps calcul
#       - IA classique + LSTM
