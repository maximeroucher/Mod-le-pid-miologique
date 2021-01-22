import math
import os
import random
import time
from enum import Enum

from tools import *

# Mute l'import de pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'True'
# Postionne la fenêtre de l'application
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
        return "Comportement de la population : " + self._name_.capitalize()


class Person:

    def __init__(self, x, y, vx, vy, ax, ay, p):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.ax = ax
        self.ay = ay
        self.p = p
        self.TPS_INFECTE = random.randint(40, 60)
        self.etat = Etat.SAIN
        self.comportement = Comportement.NORMAL
        self.VMAX = 5
        self.RAYON = 6


    def correction_vitesse(self):
        v = self.vx ** 2 + self.vy ** 2
        if v > self.VMAX ** 2:
            r = self.VMAX / math.sqrt(v)
            self.vx *= r
            self.vy *= r


    def update(self, w, h, person):
        if self.comportement == Comportement.QUARANTAINE:
            self.repulsion(person)
        self.correction_vitesse()
        self.ax = self.ay = 0
        self.vx += self.ax
        self.vy += self.ay
        if self.x > w or self.x < 0:
            self.vx = - self.vx
        if self.y > h or self.y < 0:
            self.vy = - self.vy
        self.x += int(self.vx)
        self.y += int(self.vy)
        if self.etat == Etat.INFECTE:
            self.TPS_INFECTE -= 1
        if self.TPS_INFECTE == 0:
            self.etat = Etat.RETABLI


    def position(self, other):
        pos = [1, 1]
        if self.x < other.x:
            pos[0] = -1
        if self.y < other.y:
            pos[1] = -1
        return pos


    def end_quarantine(self):
        self.VMAX = 5
        self.vx = (self.vx / 2) * self.VMAX
        self.vy = (self.vy / 2) * self.VMAX


    def start_quarantine(self):
        self.vx = (self.vx / self.VMAX) * 2
        self.vy = (self.vy / self.VMAX) * 2
        self.VMAX = 2


    def repulsion(self, person): #TODO:
        ax = ay = 0
        for other in person:
            dx = abs(self.x - other.x)
            if dx < 20 * self.RAYON:
                dy = abs(self.y - other.y)
                if dy < 20 * self.RAYON:
                    ndx = abs(self.x + self.vx - other.x - other.vx)
                    ndy = abs(self.y + self.vy - other.y - other.vy)
                    r = dx ** 2 + dy ** 2 + 1e-9
                    pos = self.position(other)
                    ax += dx ** 2 / r
                    ay += dy ** 2 / r
        self.ax = ax
        self.ay = ay


    def get_color(self):
        if self.etat == Etat.SAIN:
            return colors[0]
        elif self.etat == Etat.INFECTE:
            return colors[1]
        return colors[2]


    def collision(self, other):
        dx = self.x - other.x
        if dx < 1.5 * 2 * self.RAYON:
            dy = self.y - other.y
            if dy < 1.5 * 2 * self.RAYON:
                return dx ** 2 + dy ** 2 <= 3 * 4 * self.RAYON ** 2
            return False
        return False


    def show(self, scree, t):
        pygame.draw.circle(screen, self.get_color(), (self.x, self.y + t), self.RAYON)


    def copy(self):
        return Person(self.x, self.y, self.vx, self.vy, self.ax, self.ay, self.p)


class Simulation:

    def __init__(self, person, w, h, screen, top, taux_incidence):
        """ Initialisation de la simulation
        ---
        param :

            - nb_person (int) le nombre de personne de la simulation
            - w (int) la largeur de l'espace de la simulation
            - h (int) la hauteur de l'espace de la simulation
            - screen (Pygame.Surface) la surface sur laquelle afficher la simulation
        """
        self.person = [Person.copy(p) for p in person]
        self.person[0].etat = Etat.INFECTE
        self.sains = self.person[0:-1]
        self.infectes = [self.person[0]]
        self.retablis = []
        self.w = w
        self.h = h
        self.y = [0]
        self.data = {"Sains": [], "Infectés": [], "Rétablis": []}
        self.data_font = pygame.font.SysFont("montserrat", 18)
        self.font = pygame.font.SysFont("montserrat", 24)
        self.split()
        self.update_data()
        self.screen = screen
        self.comportement = Comportement.NORMAL
        self.TAUX_INCIDENCE = taux_incidence
        self.quarantine_time = []

        # Largeur de la fenêtre
        self.WIDTH = 700
        # Hauteur de la fenêtre
        self.HEIGHT = 390
        # Marge entre les bords de la fenêtre et le graphique
        self.MARGIN = 30
        # Hauteur maximale du graphique
        self.HAUT = self.HEIGHT - self.MARGIN
        # Longeur d'un trait
        self.DHAUT = self.HAUT + 5
        # La largeur du graphique
        self.W = self.WIDTH - 2 * self.MARGIN
        # la hauteur du grpahique
        self.H = self.HEIGHT - 2 * self.MARGIN
        # La distance au haut de la fenêtre
        self.TOP = top
        # La distance à gauche du graphique du pays
        self.LEFT = 1100
        self.no_action = taux_incidence == 0
        self.ended = False


    def init_affichage(self):
        """ Initialisation de l'affichage de la simulation
        ---
        """
        if self.no_action:
            center_text(self.screen, self.data_font, "Aucunes mesures", FG, 500, 20, self.TOP - 30, 1200)
        for x, key in enumerate(self.data):
            pygame.draw.line(
                self.screen, colors[x],
                (1150 + 250 * x, self.TOP + 440),
                (1250 + 250 * x, self.TOP + 440),
                2)
            center_text(self.screen, self.font, key, FG, 100, 50, self.TOP + 400, 1150 + 250 * x)

        mx = len(self.person)
        dx = self.H / mx

        pygame.draw.line(self.screen, FG, (self.MARGIN + self.LEFT, self.MARGIN - 10 + self.TOP),
                         (self.MARGIN + self.LEFT, self.HAUT + self.TOP), 2)

        x_coord = get_scale_value(0, mx, 10)
        for x in x_coord:
            form = str(int(x))
            w = self.data_font.size(form)[0]
            Y = self.HAUT - int(x * dx)
            pygame.draw.line(self.screen, FG, (self.MARGIN + self.LEFT, Y + self.TOP),
                             (self.MARGIN - 5 + self.LEFT, Y + self.TOP), 2)
            self.screen.blit(
                self.data_font.render(form, True, FG),
                ((self.MARGIN - w) + self.LEFT - 10, Y - 10 + self.TOP))


    def display_country(self):
        """ Affiche le graphique du pays donné
        ---
        """
        mx = len(self.person)
        my = max(self.y[-1], 1)

        dx = self.H / mx
        dy = self.W / my

        create_mask(self.TOP + self.MARGIN, self.LEFT + self.MARGIN + 2,
                    self.WIDTH - 2 * self.MARGIN, self.HEIGHT - 2 * self.MARGIN, BG, self.screen)
        # Update barre nombres
        create_mask(self.TOP + self.HEIGHT - self.MARGIN + 2, self.LEFT + self.MARGIN - 10,
                    self.WIDTH - self.MARGIN + 10, self.MARGIN, BG, self.screen)

        c_y = [x * dy + self.MARGIN + self.LEFT for x in self.quarantine_time]
        pts = [[[c_y[x], self.HAUT + 3 * self.MARGIN - self.TOP + 10], [c_y[x], self.TOP + self.MARGIN]] for x in range(len(c_y))]
        for x in range(len(pts)):
            pygame.draw.line(self.screen, FG, pts[x][0], pts[x][1], 2)

        for key in self.data:
            c_x = [(mx - x) * dx + self.MARGIN + self.TOP for x in self.data[key]]
            c_y = [x * dy + self.MARGIN + self.LEFT for x in self.y]
            pts = list(zip(c_y, c_x))
            for x in range(len(pts) - 1):
                pygame.draw.line(self.screen, colors[list(self.data.keys()).index(key)], pts[x], pts[x + 1], 2)

        y_coord = get_scale_value(0, my, 10)
        for y in y_coord:
            X = self.MARGIN + int(y * dy)
            d = str(int(y))
            w, _ = self.font.size(d)
            pygame.draw.line(self.screen, FG, (self.LEFT + X, self.HAUT + self.TOP),
                             (self.LEFT + X, self.DHAUT + self.TOP), 2)
            self.screen.blit(self.data_font.render(d, True, FG), (self.LEFT + X - w // 2 + 7, self.DHAUT + self.TOP))

        pygame.draw.line(self.screen, FG, (self.MARGIN + self.LEFT, self.HAUT + self.TOP),
                         (self.WIDTH - self.MARGIN + 10 + self.LEFT, self.HAUT + self.TOP), 2)


    def update_data(self):
        """ Met à jour les données de la simulation
        ---
        """
        self.data["Sains"].append(len(self.sains))
        self.data["Infectés"].append(len(self.infectes))
        self.data["Rétablis"].append(len(self.retablis))


    def split(self):
        """ Assigne les personnes dans leurs compartiments respectifs en fonction de leur état
        ---
        """
        p = 0
        while len(self.infectes) - p > 0:
            if self.infectes[p].etat == Etat.RETABLI:
                self.retablis.append(self.infectes[p])
                self.infectes.pop(p)
            else:
                p += 1
        p = 0
        while len(self.sains) - p > 0:
            if self.sains[p].etat == Etat.INFECTE:
                self.infectes.append(self.sains[p])
                self.sains.pop(p)
            else:
                p += 1


    def show(self):
        """ Affiche la simulation
        ---
        """
        create_mask(self.TOP - 50, -20, self.w + 30, self.h + 20, BG, self.screen)
        pygame.draw.line(self.screen, pygame.Color(200, 200, 200), (0, self.TOP - 50), (self.w, self.TOP - 50))
        pygame.draw.line(
            self.screen, pygame.Color(200, 200, 200),
            (self.w, self.TOP - 50),
            (self.w, self.h + self.TOP - 50))
        pygame.draw.line(
            self.screen, pygame.Color(200, 200, 200),
            (self.w, self.h + self.TOP - 50),
            (0, self.h + self.TOP - 50))
        pygame.draw.line(self.screen, pygame.Color(200, 200, 200), (0, self.h + self.TOP - 50), (0, self.TOP - 50))
        [p.show(self.screen, self.TOP - 50) for p in self.person]
        # dernière action du tour
        self.y.append(len(self.y))


    def update_text(self):
        """ Change les chiffres de la simulation
        ---
        """
        if not self.no_action:
            create_mask(self.TOP - 30, 1200, 500, 100, BG, self.screen)
            center_text(self.screen, self.data_font, str(self.comportement), FG, 500, 20, self.TOP - 30, 1200)
            center_text(self.screen, self.data_font,
                        f"Taux d'incidence : {self.TAUX_INCIDENCE}", FG, 500, 20, self.TOP, 1200)
        for x, key in enumerate(self.data):
            create_mask(self.TOP + 455, 1150 + 250 * x, 100, 20, BG, self.screen)
            center_text(
                self.screen, self.data_font, str(self.data[key][-1]),
                FG, 100, 20, self.TOP + 455, 1150 + 250 * x)


    def update(self):
        """ Met à jour la simulation
        ---
        """
        for p in self.person:
            p.update(self.w, self.h, self.person)
        for p in self.infectes:
            if random.randint(0, 100) <= p.p * 100:
                for n in self.sains:
                    if p.collision(n):
                        n.etat = Etat.INFECTE
        if len(self.infectes) > 0:
            self.split()
            self.update_comportement()
            self.update_data()
            self.update_text()
            self.display_country()
        else:
            if not self.ended:
                self.ended = True
        pygame.display.update()


    def update_comportement(self):
        if not self.no_action:
            if len(self.infectes) > self.TAUX_INCIDENCE and self.comportement == Comportement.NORMAL:
                self.comportement = Comportement.QUARANTAINE
                self.quarantine_time.append(self.y[-1])
                for p in self.person:
                    p.comportement = Comportement.QUARANTAINE
                    p.start_quarantine()
            elif len(self.infectes) < self.TAUX_INCIDENCE * .9 and self.comportement == Comportement.QUARANTAINE:
                self.comportement = Comportement.NORMAL
                for p in self.person:
                    p.comportement = Comportement.NORMAL
                    p.end_quarantine()
                    self.quarantine_time.append(self.y[-1])


pygame.init()
info = pygame.display.Info()
screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)
screen.fill(BG)

w = info.current_w // 2 - 10
h = info.current_h // 2 - 10

person = []
NB_PERSON = 750
S1 = 50
S2 = 0
SAVE = False

for _ in range(NB_PERSON):
    v, theta = random.randint(0, 500) / 100, random.randint(0, 628) / 100
    vx, vy = v * math.cos(theta), v * math.sin(theta)
    person.append(
        Person(
            random.randint(0, w),
            random.randint(0, h),
            vx, vy, 0, 0, .5))

if SAVE:
    titre = f"E:\\Python\\Projet\\TIPE\\Modele_epidemiologique\\app\\Simulation-{S1}-{S2}"
    if not os.path.exists(titre):
        os.makedirs(titre)

Sim = Simulation(person, info.current_w // 2 - 10, info.current_h // 2 - 10, screen, 50, S1)
Sim2 = Simulation(person, info.current_w // 2 - 10, info.current_h // 2 - 10, screen, 599, S2)
Sim.init_affichage()
Sim2.init_affichage()
x = 0

while True:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            quit()
    time.sleep(.01)
    Sim.update()
    Sim2.update()
    Sim.show()
    Sim2.show()
    if SAVE:
        if not Sim.ended and not Sim2.ended:
            pygame.image.save(screen, f"E:\\Python\\Projet\\TIPE\\Modele_epidemiologique\\app\\Simulation-{S1}-{S2}\\img{x}.jpg")
    x += 1

