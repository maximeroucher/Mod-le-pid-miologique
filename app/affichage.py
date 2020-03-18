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
    param : data (dict[label : list])
    """
    axe_x = list(range(len(list(data.values())[0])))
    for x in list(data.keys()):
        plt.plot(axe_x, data[x], label=x)
    plt.legend()
    plt.show()


def in_rect(points, x, y):
    return points[0] <= x and points[3] <= y and points[1] >= y and points[2] >= x


def in_poly(point, polyPoints, farAwayPoint):
    line1 = LineString(polyPoints)
    line2 = LineString([point, farAwayPoint])
    return line1.intersection(line2)


class Pays():

    def __init__(self, tag, name, pop, pib, border, bound):
        self.tag = tag
        self.name = name
        self.pop = pop
        self.pib = pib
        self.border = border
        self.bound = bound
        self.r = random.randint(0, 70)
        self.g = random.randint(100, 170)
        self.b = random.randint(200, 245)

    def show(self):
        for point in self.border:
            pygame.draw.polygon(screen, (self.r, self.g, self.b), point)
            pygame.draw.lines(screen, WHITE, True, point, 1)

    def show_border(self):
        for rect in self.bound:
            pygame.draw.lines(screen, (255, 0, 0), True, [(rect[0], rect[1]),
                                                          (rect[2], rect[1]), (rect[2], rect[3]), (rect[0], rect[3])], 1)

    def to_json(self):
        return {self.tag: {"NAME_FR": self.name, "POP_EST": self.pop, "GDP_MD_EST": self.pib, "geometry": self.border, "bounds": self.bound}}


def from_json(data):
    l_c = []
    for c in data:
        n = list(c.keys())[0]
        sc = c[n]
        l_c.append(Pays(n, sc["NAME_FR"], sc["POP_EST"], sc["GDP_MD_EST"], sc["geometry"], sc["bounds"]))
    return l_c

def to_json(l_c):
    return [x.to_json() for x in l_c]


def format_text(text, font_size, width, height):
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
                    l = [w]
                    ll = size
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
    l, t = pos
    text, font = format_text(text, font_size, w, h)
    for x in range(len(text)):
        wi, he = font.size(text[x])
        surface.blit(font.render(text[x], True, color), (l + (w - wi) // 2, t + x * he))



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
pygame.display.set_caption('Name')

screen.fill(BG)
screen.blit(font.render("Simulation", True, FG), (40, 10))

country_name_mask = pygame.Surface((500, 800), pygame.SRCALPHA)
country_name_mask.fill(BG)
screen.blit(country_name_mask, (1550, 0))

screen.blit(font.render("Population de départ", True, FG), (1600, 130))
screen.blit(data_font.render("1056135", True, FG), (1670, 170))

screen.blit(font.render("Sains", True, FG), (1680, 230))
screen.blit(data_font.render("629962", True, FG), (1670, 270))

screen.blit(font.render("Infectés", True, FG), (1670, 330))
screen.blit(data_font.render("65156", True, FG), (1670, 370))

screen.blit(font.render("Morts", True, FG), (1690, 430))
screen.blit(data_font.render("616", True, FG), (1670, 470))

screen.blit(font.render("Immunisés", True, FG), (1670, 530))
screen.blit(data_font.render("3189", True, FG), (1670, 570))

screen.blit(font.render("Evolution mondiale", True, FG), (400, 650))

screen.blit(font.render("Evolution locale", True, FG), (1200, 650))


for c in l_c:
    c.show()


c_name = [x.name for x in l_c]

c_bound = [x.bound for x in l_c]

country = None
changed = False

while True:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and pygame.K_ESCAPE:
            quit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT:
            x, y = pygame.mouse.get_pos()
            for c in l_c:
                for cb in c.bound:
                    if in_rect(cb, x, y):
                        for b in c.border:
                            if in_poly((x, y), b, (x + 1000, y + 1000)):
                                if c != country:
                                    country = c
                                    changed = True
                                break
    if changed:
        changed = False
        country_name_mask = pygame.Surface((500, 800), pygame.SRCALPHA)
        country_name_mask.fill(BG)
        screen.blit(country_name_mask, (1550, 0))
        blit_text(screen, country.name, (1600, 50), 60, 300, 80)
        

    pygame.display.update()

# TODO:
#       graphique
#       chgt couleur quand séléctionné (+ border ?)
#       chgt couleur hover ?
#        
