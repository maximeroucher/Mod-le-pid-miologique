import json
import tkinter as tk
import random
import tqdm

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import shapefile
from dbfread import DBF, read
from matplotlib.patches import Polygon


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



import pygame

data = json.load(open("Country.json"))

FPS = 60
LEFT = 1
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BG = (32, 34, 37)
FG = (182, 185, 190)
SCALE = 4.2

pygame.init()
font = pygame.font.SysFont("montserrat", 24)
title_font = pygame.font.SysFont("montserrat", 44)
data_font = pygame.font.SysFont("montserrat", 18)
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
clock = pygame.time.Clock()
pygame.display.set_caption('Name')

screen.fill(BG)
screen.blit(font.render("Simulation", True, FG), (40, 10))
screen.blit(title_font.render("Test", True, FG), (1670, 40))
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


for c in data:
    for sc in list(c.values())[0]["geometry"]:
        pts = []
        for point in sc:
            c_pt = [(point[0] + 180) * SCALE + 20, (90 - point[1]) * SCALE + 15]
            pts.append(c_pt)

        b = random.randint(200, 245)
        g = random.randint(100, 170)
        r = random.randint(0, 70)
        pygame.draw.polygon(screen, (r, g, b), pts)
        pygame.draw.lines(screen, WHITE, True, pts, 1)

while True:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and pygame.K_ESCAPE:
            quit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT:
            x, y = pygame.mouse.get_pos()

    pygame.display.update()


def counterclockwise(A, B, C):
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])


def segment_intersect(A, B, C, D):
    return counterclockwise(
        A, C, D) != counterclockwise(
        B, C, D) and counterclockwise(
        A, B, C) != counterclockwise(
        A, B, D)


def in_poly(point, polyPoints, farAwayPoint):
    intersections = 0
    for i in range(len(polyPoints) - 1):
        if segment_intersect(point, farAwayPoint,  polyPoints[i], polyPoints[i + 1]):
            intersections += 1
    return intersections % 2 != 0
