import json
import os
import random
import tkinter as tk

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

# Mute l'import de pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'True'

import pygame
import shapefile
import tqdm
from dbfread import DBF, read
from matplotlib.patches import Polygon
from shapely.geometry import LineString


FPS = 60
LEFT = 1
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BG = (32, 34, 37)
FG = (182, 185, 190)
SCALE = 4.2


def format_data():
    """ Ouvre le fichier des données mondiales et en récupère les données utiles à la simulation
    ---
    """
    shapefile = './../../res/110m_cultural/ne_110m_admin_0_countries.shp'
    gdf = gpd.read_file(shapefile)
    c_tag = gdf["ADM0_A3"]
    c_geo = gdf["geometry"]
    table = read('./../../res/110m_cultural/ne_110m_admin_0_countries.dbf', encoding='utf-8')
    tags = ["NAME_FR", "POP_EST", "GDP_MD_EST"]
    l = []
    for y in range(len(c_tag)):
        for z in range(len(table)):
            if table[z]["ADM0_A3"] == c_tag[y]:
                d = {c_tag[y]: {x: table[z][x] for x in tags}}
                if c_geo[z].__class__.__name__ is "MultiPolygon":
                    shp = []
                    bdr = []
                    for x in range(len(c_geo[z])):
                        shp.append(list(c_geo[z][x].exterior.coords))
                        bdr.append(list(c_geo[z][x].bounds))
                else:
                    shp = [list(c_geo[z].exterior.coords)]
                    bdr = [list(c_geo[z].bounds)]
                d[c_tag[y]]["geometry"] = shp
                d[c_tag[y]]["bounds"] = bdr
                l.append(d)
    json.dump(l, open("Country.json", "w"))


def create_map():
    """ Créer une carte du monde avec matplotlib
    ---
    """
    sf = shapefile.Reader("./../../res/110m_cultural/ne_110m_admin_0_scale_rank.shp")
    for x in range(len(sf)):
        pts = sf.shapes()[x].points
        pts_x, pts_y = [a for a, b in pts], [b for a, b in pts]
        b = random.randint(200, 245) / 255
        g = random.randint(100, 170) / 255
        r = random.randint(0, 70) / 255
        plt.fill(pts_x, pts_y, facecolor=(r, g, b), edgecolor=(1, 1, 1), linewidth=1)
    plt.show()


def afficher_sim(data):
    """ Affiche le résultat de la simulation
    ---
    param :

        - data (dict(label: list))
    """
    axe_x = list(range(len(list(data.values())[0])))
    for x in list(data.keys()):
        plt.plot(axe_x, data[x], label=x)
    plt.legend()
    plt.show()


def in_rect(points, x, y):
    """ Vérifie si un point est dans un rectangle
    ---
    param :

        - points (list) liste des points (l, r, t, l)
        - x (int) position x de la souris
        - y (int) position y de la souris
    """
    return points[0] <= x and points[3] <= y and points[1] >= y and points[2] >= x


def in_poly(point, polyPoints, farAwayPoint):
    """ Vérifie si un point est dans un polygone
    ---
    param :

        - point (tuple(x, y)) point à verifier
        - polypoint (list(tuple)) liste des points d'un polygone
        - farAwayPoint (tuple(x, y)) point à très longue distance
    """
    line1 = LineString(polyPoints)
    line2 = LineString([point, farAwayPoint])
    return line1.intersection(line2)


class Pays():

    def __init__(self, tag, name, pop, pib, border, bound):
        """ Initialisation d'un pays
        ---
        param :

            - tag (str) le format du nom de pays
            - name (str) le nom français du pays
            - pop (int) la population estimée du pays
            - pib (float) le PIB du pays (en dollar)
            - border (list(tuple)) le contour du pays
            - bound (list(tuple)) le carré dans lequel le pays est inscrit
        """
        self.tag = tag
        self.name = name
        self.pop = pop
        self.pib = pib
        self.border = border
        self.bound = bound
        self.r = random.randint(0, 50)
        self.g = random.randint(120, 180)
        self.b = random.randint(200, 235)
        self.sains = self.pop
        self.infectes = 0
        self.morts = 0
        self.rétablis = 0


    def show(self):
        """ Affiche le pays
        ---
        """
        for point in self.border:
            pygame.draw.polygon(screen, (self.r, self.g, self.b), point)
            pygame.draw.lines(screen, WHITE, True, point, 1)


    def show_border(self):
        """ Affiche le carré autour du pays
        ---
        """
        for rect in self.bound:
            pygame.draw.lines(screen, (255, 0, 0), True, [(rect[0], rect[1]),
                                                          (rect[2], rect[1]), (rect[2], rect[3]), (rect[0], rect[3])], 1)


    def to_json(self):
        """ Renvoie la classe sous forme Json
        ---
        """
        return {self.tag: {"NAME_FR": self.name, "POP_EST": self.pop, "GDP_MD_EST": self.pib, "geometry": self.border, "bounds": self.bound}}


def from_json(data):
    """ Charge un pays d'après un dictionnaire Json
    ---
    param :

        - data (dict) le dictionnaire des pays

    result :

        - list(Pays()) liste des pays
    """
    l_c = []
    for c in data:
        n = list(c.keys())[0]
        sc = c[n]
        l_c.append(Pays(n, sc["NAME_FR"], sc["POP_EST"], sc["GDP_MD_EST"], sc["geometry"], sc["bounds"]))
    return l_c


def to_json(liste):
    """ Exporte la liste de pays en liste de dictionnaire
    ---
    param :

        - liste (list(Pays)) liste des pays

    result :

        - list(dist) liste des dictionnaires des pays
    """
    return [x.to_json() for x in liste]


def format_text(text, font_size, width, height):
    """ Met le texte en forme pour occuper tout l'espace disponnible
    ---
    param :

        - text (str) le texte à afficher
        - font_size (int) la taille maximale du texte
        - width (int) la largeur maximale que peut occuper le texte
        - height (int) la hauteur maximale que peut occuper le texte

    result :

        - list(str) le texte séparer sur plusieurs lignes pour améliorer l'affichage, pygame.font.SysFont la font qui maximise l'espace occupé
    """
    n = text.split(" ")
    ok = False
    font = pygame.font.SysFont("montserrat", font_size)
    while not ok:
        end, m, l = True, [], []
        w_l = {w: font.size(w + " ") for w in n}
        ll = len(l)
        for w in n:
            if w_l[w][0] > width:
                font_size -= 1
                end = False
                break
        if end:
            for w in n:
                size = w_l[w][0]
                if ll + size <= width:
                    l.append(w)
                    ll += size
                else:
                    m.append(l)
                    l, ll = [w], size
            m.append(l)
            h_v = 0
            if len(m) * font.size(m[0][0])[1] > height:
                font_size -= 1
            else:
                ok = True
        font = pygame.font.SysFont("montserrat", font_size)
    m = [" ".join(x) for x in m]
    return m, font


def blit_text(surface, text, pos, font_size, w, h, color=FG):
    """ Optimise l'affichage d'un texte sur un espace donné
    ---
    param :

        - surface (pygame.Surface) la surface sur laquelle écrire
        - text (str) le texte à afficher
        - pos (tuple(x, y)) la position (t, l) d'origine de l'espace
        - font_size (int) la taille maximale du texte
        - w (int) la largeur de l'espace
        - h (int) la hauteur de l'espace
        - color ((r, g, b)) la couleur du texte
    """
    l, t = pos
    text, font = format_text(text, font_size, w, h)
    for x in range(len(text)):
        wi, he = font.size(text[x])
        surface.blit(font.render(text[x], True, color), (l + (w - wi) // 2, t + x * he))


def center_text(surface, font, text, color, w, h, t, l):
    """ Centre le texte au milleu de l'espace donné
    ---
    param :

        - surface (pygame.Surface) la surface sur laquelle écrire
        - font (pygame.font.SysFont) la font avec laquelle écrire
        - text (str) le texte à afficher
        - color ((r, g, b)) la couleur du texte à afficher
        - w (int) la largeur de l'espace
        - h (int) la hauteur de l'espace
        - t (int) la distance entre le haut de la fenêtre et le haut de l'espace
        - l (int) la distance entre la gauche de la fenêtre et la gauche de l'espace
    """
    wi, he = font.size(text)
    surface.blit(font.render(text, True, color), (l + (w - wi) // 2, t + (h - he) // 2))


def create_mask(t, l, w, h, color):
    """ Créer un masque pour réécrire du texte
    ---
    param :

        - t (int) top
        - l (int) left
        - w (int) largeur
        - h (int) hauteur
        - color ((r, g, b)) la couleur du masque
    """
    country_name_mask = pygame.Surface((w, h), pygame.SRCALPHA)
    country_name_mask.fill(color)
    screen.blit(country_name_mask, (l, t))


def update(coutry):
    """ Change les informations à l'écran et la couleur du pays donné
    ---
    param :

        - country (Pays()) le pays doit les informations doivent être affichées
    """
    create_mask(0, 1550, 400, 120, BG)
    blit_text(screen, country.name, (1600, 30), 60, 300, 80)
    create_mask(170, 1550, 400, 50, BG)
    center_text(screen, data_font, str(country.pop), FG, 300, 50, 160, 1600)
    create_mask(270, 1550, 400, 50, BG)
    center_text(screen, data_font, str(country.sains), FG, 300, 50, 260, 1600)
    create_mask(370, 1550, 400, 50, BG)
    center_text(screen, data_font, str(country.infectes), FG, 300, 50, 360, 1600)
    create_mask(470, 1550, 400, 50, BG)
    center_text(screen, data_font, str(country.morts), FG, 300, 50, 460, 1600)
    create_mask(570, 1550, 400, 50, BG)
    center_text(screen, data_font, str(country.morts), FG, 300, 50, 560, 1600)
    create_mask(30, 10, 1540, 620, BG)
    border = get_scale(country, 1600, 500, 50, 20)
    for c in border:
        pygame.draw.polygon(screen, (coutry.r, coutry.g, coutry.b), c)
        pygame.draw.lines(screen, WHITE, True, c, 1)


def get_scale(country, w, h, t, l): # TODO: rassembler les îles pour zommer encore +
    """ Calcule la redimension des bords du pays afin de le zoomer
    ---
    param :

        - country (Pays) le pays à redimensionner
        - w (int) la largeur maximale
        - h (int) la hauteur maximale
        - t (int) la distance au haut de l'écran
        - l (int) la distance à gauche de l'écran

    result :

        - list(list(tuple)) liste des frontières des parties du pays redimensionné
    """
    min_l = min([x[0] for x in country.bound])
    min_t = min([x[3] for x in country.bound])
    max_r = max([x[2] for x in country.bound])
    max_b = max([x[1] for x in country.bound])
    h_c = max_b - min_t
    w_c = max_r - min_l
    dx = w / w_c
    dy = h / h_c
    scale = min(dx, dy)
    esp_x = (w - (w_c * scale)) // 2
    esp_y = (h - (h_c * scale)) // 2
    border = []
    for c in country.border:
        f = []
        for b in c:
            f.append([(b[0] - min_l) * scale + l + esp_x, (b[1] - min_t) * scale + t + esp_y])
        border.append(f)
    return border


data = json.load(open("Country.json"))
l_c = from_json(data)

pygame.init()
font = pygame.font.SysFont("montserrat", 24)
title_font = pygame.font.SysFont("montserrat", 44)
data_font = pygame.font.SysFont("montserrat", 18)
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
info = pygame.display.Info()
screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)
clock = pygame.time.Clock()

screen.fill(BG)
screen.blit(font.render("Simulation d'une épidémie de ...", True, FG), (20, 5))

center_text(screen, font, "Population de départ", FG, 300, 50, 130, 1600)
center_text(screen, font, "Sains", FG, 300, 50, 230, 1600)
center_text(screen, font, "Infectés", FG, 300, 50, 330, 1600)
center_text(screen, font, "Morts", FG, 300, 50, 430, 1600)
center_text(screen, font, "Rétablis", FG, 300, 50, 530, 1600)

screen.blit(font.render("Evolution mondiale", True, FG), (400, 650))
create_mask(700, 150, 700, 350, FG)
screen.blit(font.render("Evolution locale", True, FG), (1350, 650))
create_mask(700, 1100, 700, 350, FG)

for c in l_c:
    c.show()

c_name = [x.name for x in l_c]
c_bound = [x.bound for x in l_c]

country = None
changed = False
zoomed = False

while True:
    clock.tick(FPS)

    for event in pygame.event.get():

        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and pygame.K_ESCAPE:
            quit()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT:
            x, y = pygame.mouse.get_pos()
            if not zoomed:
                for c in l_c:
                    for cb in c.bound:
                        if in_rect(cb, x, y):
                            for b in c.border:
                                if in_poly((x, y), b, (x + 1000, y + 1000)) and not changed:
                                    if c != country:
                                        country = c
                                    changed = True
                                    zoomed = True
                                    break


    if changed:
        changed = False
        update(country)


    pygame.display.update()

# TODO:
#       graphique
#       chgt couleur hover ?
#       Zoom (flèche retour)
