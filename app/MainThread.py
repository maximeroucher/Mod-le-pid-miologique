import json
import os
import random
import sqlite3
import time
from threading import Thread
from tkinter import messagebox

# Mute l'import de pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'True'
# Postionne la fenêtre de l'application
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

import easygui
import pygame

from tools import *

from TableManager import CustomTableManager


# Couleur de fond
BG = (32, 34, 37)
# Couleur du texte, des axes des graphiques et des bords des pays
FG = (182, 185, 190)


class MainThread(Thread):

    def __init__(self, screen, countries, c_tag, font, data_font, num_country, on_world, zoomed):
        """ Initialisation d'un graphique
        ---
        param :

            - screen (pygame.Surface) la surface sur laquelle écrire
            - countries (list(Pays)) la liste des pays de la simulation
            - c_tag (list(str)) la liste des tags des pays
            - font (pygame.font.SysFont) la font des textes
            - data_font (pygame.font.SysFont) la font des graphiques
            - num_country (int) le numéro du pays séléctionné
            - on_world (bool) afficher le monde entier
            - zoomed (bool) l'affichage est celui d'un pays
        """
        ## Init Thread

        Thread.__init__(self)
        self.daemon = True

        # Les fonts
        self.font = font
        self.data_font = data_font

        # Liste des tags des pays
        self.c_tag = c_tag

        # Pays séléctionné
        self.num_country = num_country

        ## Manager de base de donnée

        self.use_db = None
        self.param = []
        #self.tbm = TableManager(countries)
        self.tbm = CustomTableManager(countries)

        ## Surface

        self.screen = screen
        self.need_mask = False

        ## Constantes

        # Temps d'une journée de simulation
        self.SLEEP_TIME = .001
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
        self.TOP = 680
        # La distance à gauche du graphique du pays
        self.LEFT_1 = 920
        # La distance à gauche du graphique du monde
        self.LEFT_2 = 100
        # Coordonnées du graphique pays
        self.COUNTRY_GRAPH_BOUND = (self.LEFT_1 + self.MARGIN, self.TOP + self.HAUT,
                                    self.LEFT_1 + self.WIDTH - self.MARGIN, self.TOP + self.MARGIN)
        # Coefficient entre la largeur du graphique et sa valeur en ce point
        self.COEF_WIDTH = 1.08 / self.WIDTH
        # Coefficient entre la hauteur du graphique et sa valeur en ce point
        self.COEF_HEIGHT = 1.189 / self.HEIGHT
        # Coordonnées du graphique mondial
        self.WORLD_GRAPH_BOUND = (self.LEFT_2 + self.MARGIN, self.TOP + self.HAUT,
                                  self.LEFT_2 + self.WIDTH - self.MARGIN, self.TOP + self.MARGIN)

        self.on_world = on_world
        self.zoomed = zoomed


    def gen_data(self, day):
        """ Fait avancer la simulation d'un jour
        ---
        param :

            - day (int) le jour de la simulation
        """
        data = [0 for _ in range(self.nb_param)]
        self.N = 0
        for n in range(len(self.models)):
            model = self.models[n]
            model.update(self.tbm, day + 1)
            for x in range(self.nb_param):
                val = model.param_dict[self.keys[x]]["value"]
                self.data[n][x].append(val)
                data[x] += val
            self.N += model.N
        for x in range(self.nb_param):
            self.world_data[x].append(data[x])


    def change_countries(self, n):
        """ Change le graphique du pays donnés
        ---
        param :

            - n (int) le numéro du pays donné
        """
        tag = self.c_tag[n]
        self.num_country = n
        self.num_model = [n for n in range(len(self.models)) if self.models[n].country.tag == tag][0]
        create_mask(650, self.LEFT_1 - 5, self.WIDTH, 30, BG, self.screen)
        center_text(
            self.screen, self.font, f"Evolution locale ({self.models[self.num_model].country.name})", FG, self.WIDTH, 30,
            650, self.LEFT_1 - 5)
        if len(self.data[self.num_model][0]) >= 2:
            self.display_graph(1)
        create_mask(self.TOP + 10, self.LEFT_1 - 80, 100, self.HEIGHT - self.MARGIN, BG, self.screen)
        create_mask(self.TOP - 10, self.LEFT_1 + 25, 5, self.HEIGHT - self.MARGIN, BG, self.screen)
        x_coord = self.get_scale_value(0, self.models[self.num_model].N, 10)
        mx = max([max(x) for x in self.data[self.num_model]])
        dx = self.H / mx
        for x in x_coord:
            form = "{:.2e}".format(int(x))
            w = self.data_font.size(form)[0]
            Y = self.HAUT - int(x * dx)
            pygame.draw.line(self.screen, FG, (self.MARGIN + self.LEFT_1, Y + self.TOP),
                             (self.MARGIN - 5 + self.LEFT_1, Y + self.TOP), 2)
            self.screen.blit(
                self.data_font.render(form, True, FG),
                ((self.MARGIN - w) + self.LEFT_1 - 10, Y - 10 + self.TOP))


    def get_scale_value(self, m, M, nb_pt):
        """ Créer une échelle de valeur
        ---
        param :

            - m (int) la valeur minimale de l'échelle
            - M (int) la valeur maximale de l'échelle
            - nb_pt (int) le nombre de point de l'échelle

        result :

            - list(int)
        """
        if M - m < nb_pt:
            return [m + x for x in range(M - m + 1)]
        delta = (M - m) / nb_pt
        return [x * delta + m for x in range(nb_pt + 1)]


    def display_graph(self, nb):
        """ Affiche un graphique
        ---
        param :

            - nb (0 / 1) : 0 -> monde, 1 -> pays séléctionné
        """
        if nb == 1:
            self.display_country()
        else:
            self.display_world()
        time.sleep(self.SLEEP_TIME)
        pygame.display.update()


    def display_country(self):
        """ Affiche le graphique du pays donné
        ---
        """
        mx = max([max(x) for x in self.data[self.num_model]])
        my = self.y[-1]

        dx = self.H / mx
        dy = self.W / my

        create_mask(self.TOP, self.LEFT_1 + self.MARGIN + 2, self.WIDTH - 2 * self.MARGIN, self.HEIGHT - self.MARGIN, BG, self.screen)
        create_mask(self.TOP + self.HEIGHT - self.MARGIN + 2, self.LEFT_1 + self.MARGIN - 10,
                    self.WIDTH - self.MARGIN + 10, self.MARGIN, BG, self.screen)

        for n in range(len(self.data[self.num_model])):
            c_x = [(mx - x) * dx + self.MARGIN + self.TOP for x in self.data[self.num_model][n]]
            c_y = [x * dy + self.MARGIN + self.LEFT_1 for x in self.y]
            pts = list(zip(c_y, c_x))
            for x in range(len(pts) - 1):
                pygame.draw.line(self.screen, self.color_data[n], pts[x], pts[x + 1], 2)

        pygame.draw.line(self.screen, FG, (self.MARGIN + self.LEFT_1, self.HAUT + self.TOP),
                         (self.WIDTH - self.MARGIN + 10 + self.LEFT_1, self.HAUT + self.TOP), 2)

        y_coord = self.get_scale_value(0, my, 10)
        for y in y_coord:
            X = self.MARGIN + int(y * dy)
            d = str(round(y, 2))
            w, _ = self.font.size(d)
            pygame.draw.line(self.screen, FG, (self.LEFT_1 + X, self.HAUT + self.TOP),
                             (self.LEFT_1 + X, self.DHAUT + self.TOP), 2)
            self.screen.blit(self.data_font.render(d, True, FG), (self.LEFT_1 + X - w // 2 + 7, self.DHAUT + self.TOP))


    def display_world(self):
        """ Affiche le graphique du monde
        ---
        """
        mx = max([max(x) for x in self.world_data])
        my = self.y[-1]

        dx = self.H / mx
        dy = self.W / my

        create_mask(self.TOP + self.MARGIN, self.LEFT_2 + self.MARGIN + 2,
                    self.WIDTH - 2 * self.MARGIN, self.HEIGHT - 2 * self.MARGIN, BG, self.screen)
        create_mask(self.TOP + self.HEIGHT - self.MARGIN + 2, self.LEFT_2 + self.MARGIN - 10,
                    self.WIDTH - self.MARGIN + 10, self.MARGIN, BG, self.screen)

        for n in range(len(self.world_data)):
            c_x = [(mx - x) * dx + self.MARGIN + self.TOP for x in self.world_data[n]]
            c_y = [x * dy + self.MARGIN + self.LEFT_2 for x in self.y]
            pts = list(zip(c_y, c_x))
            for x in range(len(pts) - 1):
                pygame.draw.line(self.screen, self.color_data[n], pts[x], pts[x + 1], 2)

        y_coord = self.get_scale_value(0, my, 10)
        for y in y_coord:
            X = self.MARGIN + int(y * dy)
            d = str(round(y, 2))
            w, _ = self.font.size(d)
            pygame.draw.line(self.screen, FG, (self.LEFT_2 + X, self.HAUT + self.TOP),
                             (self.LEFT_2 + X, self.DHAUT + self.TOP), 2)
            self.screen.blit(self.data_font.render(d, True, FG), (self.LEFT_2 + X - w // 2 + 7, self.DHAUT + self.TOP))

        pygame.draw.line(self.screen, FG, (self.MARGIN + self.LEFT_2, self.HAUT + self.TOP),
                         (self.WIDTH - self.MARGIN + 10 + self.LEFT_2, self.HAUT + self.TOP), 2)


    def update(self, back_arrow):
        """ Change les informations à l'écran et la couleur du pays séléctionné
        ---
        param :

            - back_arrow (pygame.Image) la flèche de retour
        """
        model = self.models[self.num_model]
        N = len(model.param_dict)
        update_mask(N, self.screen)
        create_mask(0, 1550, 400, 120, BG, self.screen)
        blit_text(self.screen, model.country.name, (1600, 30), 60, 300, 80)
        center_text(self.screen, self.data_font, f"{model.N}", FG, 300, 50, 160, 1600)
        x = 1
        for key in model.param_dict:
            center_text(self.screen, self.data_font,
                        f"{int(model.param_dict[key]['value'])}", FG, 300, 40, 175 + self.DELTA * x, 1600)
            x += 1
        create_mask(30, 10, 1540, 620, BG, self.screen)
        border = get_scale(model.country, 1500, 500, 50, 20)
        for c in border:
            pygame.draw.polygon(self.screen, (model.country.r, model.country.g, model.country.b), c)
            pygame.draw.lines(self.screen, FG, True, c, 1)
        pygame.draw.rect(self.screen, FG, (40, 520, 70, 70), 1)
        self.screen.blit(back_arrow, (50, 530))


    def update_world(self):
        """ Met à jour les informations mondiales
        ---
        """
        create_mask(0, 1550, 400, 120, BG, self.screen)
        blit_text(self.screen, "Monde", (1600, 30), 60, 300, 80)
        self.update_world_info()


    def update_country_info(self):
        """ Affiche les valeurs du pays sélétionnné
        ---
        """
        n = len(self.world_data)
        update_mask(n, self.screen)
        model = self.models[self.num_model]
        center_text(self.screen, self.data_font, f"{model.N}", FG, 300, 50, 160, 1600)
        x = 1
        for key in model.param_dict:
            center_text(self.screen, self.data_font,
                        f"{int(model.param_dict[key]['value'])}", FG, 300, 40, 175 + self.DELTA * x, 1600)
            x += 1


    def update_world_info(self):
        """ Affiche les valeurs mondiales
        ---
        """
        n = len(self.world_data)
        update_mask(n, self.screen)
        center_text(self.screen, self.data_font, f"{self.N}", FG, 300, 50, 160, 1600)
        x = 1
        for key in self.world_data:
            center_text(self.screen, self.data_font, f"{int(key[-1])}", FG, 300, 40, 175 + self.DELTA * x, 1600)
            x += 1


    def graph_value(self):
        """ Affiche les valeurs du graphique à la position de la souris
        ---
        result :

            - int, int
        """
        # Si un masque doit être créé pour réécrire les valeur au point de la souris
        if self.need_mask:
            create_mask(600, 10, 150, 70, BG, self.screen)
            self.need_mask = False

        x, y = pygame.mouse.get_pos()
        # Si la souris est sur le graphique pays
        if in_rect(self.COUNTRY_GRAPH_BOUND, x, y):
            center_text(
                self.screen, self.data_font,
                f"x : {int((x - self.COUNTRY_GRAPH_BOUND[0]) * self.COEF_WIDTH * len(self.world_data[0]))}",
                FG, 150, 50, 600, 15)
            center_text(
                self.screen, self.data_font, "y : {:.2e}".format(
                    int((self.COUNTRY_GRAPH_BOUND[1] - y) * self.COEF_HEIGHT * self.models[self.num_model].N)),
                FG, 150, 50, 630, 15)
            self.need_mask = True

        # Si la souris est sur le graphique mondial
        elif in_rect(self.WORLD_GRAPH_BOUND, x, y):
            center_text(
                self.screen, self.data_font,
                f"x : {int((x - self.WORLD_GRAPH_BOUND[0]) * self.COEF_WIDTH * len(self.world_data[0]))}",
                FG, 150, 50, 600, 15)
            center_text(
                self.screen, self.data_font, "y : {:.2e}".format(
                    int((self.WORLD_GRAPH_BOUND[1] - y) * self.COEF_HEIGHT * self.N)),
                FG, 150, 50, 630, 15)
            self.need_mask = True
        return x, y


    def init_affichage(self):
        """ Affiche les paramètres de la simulation
        ---
        """
        ## Init info fenêtre

        x = 1
        for key in self.ex_param:
            pygame.draw.line(
                self.screen, self.ex_param[key]['color'],
                (1700, 175 + self.DELTA * x),
                (1800, 175 + self.DELTA * x),
                2)
            center_text(self.screen, self.font, key, FG, 300, 50, 130 + self.DELTA * x, 1600)
            x += 1

        center_text(
            self.screen, self.font, f"Evolution locale ({self.models[self.num_model].country.name})", FG, self.WIDTH, 30,
            650, self.LEFT_1 - 5)

        # Echelle du monde
        mx = max([max(x) for x in self.world_data])
        dx = self.H / mx

        # Droites du graphique
        pygame.draw.line(self.screen, FG, (self.MARGIN + self.LEFT_2, self.MARGIN - 10 + self.TOP),
                         (self.MARGIN + self.LEFT_2, self.HAUT + self.TOP), 2)

        x_coord = self.get_scale_value(0, self.N, 10)
        for x in x_coord:
            form = "{:.2e}".format(int(x))
            w = self.data_font.size(form)[0]
            Y = self.HAUT - int(x * dx)
            pygame.draw.line(self.screen, FG, (self.MARGIN + self.LEFT_2, Y + self.TOP),
                             (self.MARGIN - 5 + self.LEFT_2, Y + self.TOP), 2)
            self.screen.blit(
                self.data_font.render(form, True, FG),
                ((self.MARGIN - w) + self.LEFT_2 - 10, Y - 10 + self.TOP))

        # Pays
        pygame.draw.line(self.screen, FG, (self.MARGIN + self.LEFT_1, self.MARGIN - 10 + self.TOP),
                         (self.MARGIN + self.LEFT_1, self.HAUT + self.TOP), 2)


    def init_model(self):
        """ Initialise les paramètres d'affichage
        ---
        """
        self.ex_param = self.models[0].param_dict
        self.nb_param = len(self.ex_param)
        self.keys = list(self.ex_param.keys())
        self.N = 0
        self.data = []
        for model in self.models:
            self.data.append([[model.param_dict[key]["value"]] for key in self.keys])
            self.N += model.N
        self.y = [0]
        self.num_model = 0
        self.world_data = [[0] for _ in range(self.nb_param)]
        for x in range(len(self.data)):
            for n in range(self.nb_param):
                self.world_data[n][0] += self.data[x][n][0]
        self.color_data = [model.param_dict[x]["color"] for x in self.ex_param]
        self.nb_iterations = [model.nb_iterations for model in self.models]
        self.DELTA = 750 / self.nb_param


    def run(self):
        """ Lance la simulation et l'affichage du graphique
        ---
        """
        # Affiche les pays
        for c in self.tbm.countries:
            c.show(self.screen)
        # Affiche mes textes
        center_text(self.screen, self.font, "Evolution mondiale", FG, 700, 50, 650, 100)
        center_text(self.screen, self.font, "Population de départ", FG, 300, 50, 130, 1600)
        self.screen.blit(self.font.render("Simulation d'une épidémie de ...", True, FG), (20, 0))
        # Récupère les modèles et initialise la simulatio
        self.models = self.tbm.models
        self.init_model()
        self.update_world()
        self.change_countries(self.num_country)
        #if not self.use_db:
        #self.tbm.save_model_param()
        x = 0
        self.init_affichage()
        self.gen_data(x)
        for _ in range(int(self.nb_iterations[self.num_model])):
            x += 1
            self.y.append(len(self.y))
            self.gen_data(x)
            self.graph_value()
            if self.num_country == self.num_model and (not self.on_world or self.zoomed):
                self.update_country_info()
            else:
                self.update_world_info()
            if len(self.data[self.num_model][0]) >= 2:
                self.display_graph(1)
                self.display_graph(2)
        self.tbm.end()
