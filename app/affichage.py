import json
import os
import random
import time
from tkinter import *
from tkinter import ttk
from threading import Thread

# Mute l'import de pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'True'
# Postionne la fenêtre de l'application
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

#import geopandas as gpd
import matplotlib.pyplot as plt
import pygame
import shapefile
from dbfread import DBF, read
from shapely.geometry import Point, Polygon

from sim import SIR, SIRM, TableManager


# Le nombre d'images par seconde
FPS = 60

# Code du clic gauche de la souris
LEFT = 1


# Couleur de fond
BG = (32, 34, 37)
HEXBG = "#36393f"
# Couleur du texte, des axes des graphiques et des bords des pays
FG = (182, 185, 190)
HEXFG = "#B6B9BE"

# Coordonnées du carré du bouton (l, b, r, t)
BTN_BOUND = [40, 590, 110, 520]


### Outils


# Extraction de données

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


# Vérification position point

def in_rect(points, x, y):
    """ Vérifie si un point est dans un rectangle
    ---
    param :

        - points (list) liste des points (l, b, r, t)
        - x (int) position x de la souris
        - y (int) position y de la souris
    """
    return points[0] <= x and points[3] <= y and points[1] >= y and points[2] >= x


def in_poly(point, polyPoints):
    """ Vérifie si un point est dans un polygone
    ---
    param :

        - point (tuple(x, y)) point à verifier
        - polypoint (list(tuple)) liste des points d'un polygone
    """
    return Polygon(polyPoints).contains(Point(point))


# Conservation données

def from_json(data):
    """ Charge un pays d'après un dictionnaire Json
    ---
    param :

        - data (dict) le dictionnaire des pays

    result :

        - list(Pays) liste des pays
    """
    countries = []
    for c in data:
        n = list(c.keys())[0]
        sc = c[n]
        countries.append(Pays(n, sc["NAME_FR"], sc["POP_EST"], sc["GDP_MD_EST"], sc["geometry"], sc["bounds"]))
    return countries


def to_json(liste):
    """ Exporte la liste de pays en liste de dictionnaire
    ---
    param :

        - liste (list(Pays)) liste des pays

    result :

        - list(dist) liste des dictionnaires des pays
    """
    return [x.to_json() for x in liste]


### Affichage


# Texte

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


# Masques

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


def update_mask(n):
    """ Met des masques sur les textes qui doivent être changés
    ---
    param :

        - n (int) le nombre de masque a créer
    """
    w = 750 / n
    create_mask(170, 1550, 400, 50, BG)
    for x in range(1, n + 1):
        create_mask(177 + w * x, 1550, 400, 50, BG)


# Redimensionnement

def get_scale(country, w, h, t, l):
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
    scale = min(w / w_c, h / h_c)
    esp_x = (w - (w_c * scale)) // 2
    esp_y = (h - (h_c * scale)) // 2
    border = []
    for c in country.border:
        f = []
        for b in c:
            f.append([(b[0] - min_l) * scale + l + esp_x, (b[1] - min_t) * scale + t + esp_y])
        border.append(f)
    return border



### Classes

class Pays:

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


    def show(self):
        """ Affiche le pays
        ---
        """
        for point in self.border:
            pygame.draw.polygon(screen, (self.r, self.g, self.b), point)
            pygame.draw.lines(screen, FG, True, point, 1)


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


    def toggle_close(self):
        self.r, self.b = self.b, self.r
        self.swoh()


    def __lt__(self, value):
        return self.name < value.name


class MainThread(Thread):

    def __init__(self, screen, countries):
        """ Initialisation d'un graphique
        ---
        param :

            - screen (pygame.Surface) la surface sur laquelle écrire
            - model (modèle compartimentale) le modèle dont le graphique doit afficher l'évolution
        """
        ## Init Thread

        Thread.__init__(self)
        self.daemon = True


        ## Manager de base de donnée

        self.use_db = None
        self.param = []
        self.tbm = TableManager(countries)


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
        self.COUNTRY_GRAPH_BOUND = (self.LEFT_1 + self.MARGIN, self.TOP + self.HAUT, self.LEFT_1 + self.WIDTH - self.MARGIN, self.TOP + self.MARGIN)
        # Coefficient entre la largeur du graphique et sa valeur en ce point
        self.COEF_WIDTH = 1.08 / self.WIDTH
        # Coefficient entre la hauteur du graphique et sa valeur en ce point
        self.COEF_HEIGHT = 1.189 / self.HEIGHT
        # Coordonnées du graphique mondial
        self.WORLD_GRAPH_BOUND = (self.LEFT_2 + self.MARGIN, self.TOP + self.HAUT, self.LEFT_2 + self.WIDTH - self.MARGIN, self.TOP + self.MARGIN)


    def gen_data(self, day):
        """ Fait avancer la simulation d'un jour
        ---
        """
        data = [0 for _ in range(self.nb_param)]
        for n in range(len(self.models)):
            model = self.models[n]
            if model.I != 0:
                model.update(self.tbm, day + 1)
            for x in range(self.nb_param):
                val = model.param_dict[self.keys[x]]["value"] * model.N
                self.data[n][x].append(val)
                data[x] += val
        for x in range(self.nb_param):
            self.world_data[x].append(data[x])
        if not self.use_db:
            self.tbm.save_data(day)


    def change_countries(self, n):
        """ Change le graphique du pays donnés
        ---
        param :

            - n (int) le numéro du pays donné
        """
        assert n <= len(self.models)
        self.num_model = n
        create_mask(650, self.LEFT_1 - 5, self.WIDTH, 30, BG)
        center_text(
            self.screen, font, f"Evolution locale ({self.models[self.num_model].country.name})", FG, self.WIDTH, 30,
            650, self.LEFT_1 - 5)
        if len(self.data[self.num_model][0]) >= 2:
            self.display_graph(1)
        create_mask(self.TOP + 10, self.LEFT_1 - 80, 100, self.HEIGHT - self.MARGIN, BG)
        x_coord = self.get_scale_value(0, self.models[self.num_model].N, 10)
        mx = max([max(x) for x in self.data[self.num_model]])
        dx = self.H / mx
        for x in x_coord:
            form = "{:.2e}".format(int(x))
            w = data_font.size(form)[0]
            Y = self.HAUT - int(x * dx)
            pygame.draw.line(self.screen, FG, (self.MARGIN + self.LEFT_1, Y + self.TOP),
                            (self.MARGIN - 5 + self.LEFT_1, Y + self.TOP), 2)
            self.screen.blit(
                data_font.render(form, True, FG),
                ((self.MARGIN - w) + self.LEFT_1 - 10, Y - 10 + self.TOP))


    def get_scale_value(self, m, M, nb_pt):
        """ Créer une échelle de valeur
        ---
        param :

            - m (int) la valeur minimale de l'échelle
            - M (int) la valeur maximale de l'échelle
            - nb_pt (int) le nombre de point de l'échelle
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

        create_mask(self.TOP, self.LEFT_1 + self.MARGIN + 2, self.WIDTH - 2 * self.MARGIN, self.HEIGHT - self.MARGIN, BG)
        create_mask(self.TOP + self.HEIGHT - self.MARGIN + 2, self.LEFT_1 + self.MARGIN - 10, self.WIDTH - self.MARGIN + 10, self.MARGIN, BG)

        for n in range(len(self.data[self.num_model])):
            c_x = [(mx - x) * dx + self.MARGIN + self.TOP for x in self.data[self.num_model][n]]
            c_y = [x * dy + self.MARGIN + self.LEFT_1 for x in self.y]
            pts = list(zip(c_y, c_x))
            for x in range(len(pts) - 1):
                pygame.draw.line(self.screen, self.color_data[n], pts[x], pts[x + 1], 2)

        pygame.draw.line(self.screen, FG, (self.MARGIN + self.LEFT_1, self.HAUT + self.TOP),
                        (self.WIDTH - self.MARGIN + 10 + self.LEFT_1, self.HAUT+ self.TOP), 2)

        y_coord = self.get_scale_value(0, my, 10)
        for y in y_coord:
            X = self.MARGIN + int(y * dy)
            d = str(round(y, 2))
            w, _ = font.size(d)
            pygame.draw.line(self.screen, FG, (self.LEFT_1 + X, self.HAUT + self.TOP),
                            (self.LEFT_1 + X, self.DHAUT + self.TOP), 2)
            self.screen.blit(data_font.render(d, True, FG), (self.LEFT_1 + X - w // 2 + 7, self.DHAUT + self.TOP))


    def display_world(self):
        """ Affiche le graphique du monde
        ---
        """
        mx = max([max(x) for x in self.world_data])
        my = self.y[-1]

        dx = self.H / mx
        dy = self.W / my

        create_mask(self.TOP + self.MARGIN, self.LEFT_2 + self.MARGIN + 2, self.WIDTH - 2 * self.MARGIN, self.HEIGHT - 2 * self.MARGIN, BG)
        create_mask(self.TOP + self.HEIGHT - self.MARGIN + 2, self.LEFT_2 + self.MARGIN - 10,
                    self.WIDTH - self.MARGIN + 10, self.MARGIN, BG)

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
            w, _ = font.size(d)
            pygame.draw.line(self.screen, FG, (self.LEFT_2 + X, self.HAUT + self.TOP),
                            (self.LEFT_2 + X, self.DHAUT + self.TOP), 2)
            self.screen.blit(data_font.render(d, True, FG), (self.LEFT_2 + X - w // 2 + 7, self.DHAUT + self.TOP))

        pygame.draw.line(self.screen, FG, (self.MARGIN + self.LEFT_2, self.HAUT + self.TOP),
                         (self.WIDTH - self.MARGIN + 10 + self.LEFT_2, self.HAUT + self.TOP), 2)


    def update(self):
        """ Change les informations à l'écran et la couleur du pays séléctionné
        ---
        """
        model = self.models[self.num_model]
        N = len(model.param_dict)
        update_mask(N)
        create_mask(0, 1550, 400, 120, BG)
        blit_text(screen, model.country.name, (1600, 30), 60, 300, 80)
        center_text(screen, data_font, "{:.2e}".format(model.N), FG, 300, 50, 160, 1600)
        x = 1
        for key in model.param_dict:
            center_text(screen, data_font, "{:.2e}".format(
                int(model.param_dict[key]['value'] * model.N)), FG, 300, 40, 175 + self.DELTA * x, 1600)
            x += 1
        create_mask(30, 10, 1540, 620, BG)
        border = get_scale(model.country, 1500, 500, 50, 20)
        for c in border:
            pygame.draw.polygon(screen, (model.country.r, model.country.g, model.country.b), c)
            pygame.draw.lines(screen, FG, True, c, 1)
        pygame.draw.rect(screen, FG, (40, 520, 70, 70), 1)
        screen.blit(back_arrow, (50, 530))


    def update_world(self):
        """ Met à jour les informations mondiales
        ---
        """
        create_mask(0, 1550, 400, 120, BG)
        blit_text(screen, "Monde", (1600, 30), 60, 300, 80)
        self.update_world_info()


    def update_country_info(self):
        """ Affiche les valeurs du pays sélétionnné
        ---
        """
        n = len(self.world_data)
        update_mask(n)
        model = self.models[self.num_model]
        center_text(screen, data_font, "{:.2e}".format(model.N), FG, 300, 50, 160, 1600)
        x = 1
        for key in model.param_dict:
            center_text(screen, data_font,
                        "{:.2e}".format(int(model.param_dict[key]['value'] * model.N)), FG, 300, 40, 175 + self.DELTA * x, 1600)
            x += 1


    def update_world_info(self):
        """ Affiche les valeurs mondiales
        ---
        """
        n = len(self.world_data)
        update_mask(n)
        center_text(screen, data_font, "{:.2e}".format(self.N), FG, 300, 50, 160, 1600)
        x = 1
        for key in self.world_data:
            center_text(screen, data_font,
                        "{:.2e}".format(int(key[-1])), FG, 300, 40, 175 + self.DELTA * x, 1600)
            x += 1


    def graph_value(self):
        """ Affiche les valeurs du graphique à la position de la souris
        ---
        """
        # Si un masque doit être créé pour réécrire les valeur au point de la souris
        if self.need_mask:
            create_mask(600, 10, 150, 70, BG)
            self.need_mask = False

        x, y = pygame.mouse.get_pos()
        # Si la souris est sur le graphique pays
        if in_rect(self.COUNTRY_GRAPH_BOUND, x, y):
            center_text(
                screen, data_font,
                f"x : {int((x - self.COUNTRY_GRAPH_BOUND[0]) * self.COEF_WIDTH * len(graph.world_data[0]))}",
                FG, 150, 50, 600, 15)
            center_text(
                screen, data_font, "y : {:.2e}".format(
                    int((self.COUNTRY_GRAPH_BOUND[1] - y) * self.COEF_HEIGHT * graph.models[graph.num_model].N)),
                FG, 150, 50, 630, 15)
            self.need_mask = True

        # Si la souris est sur le graphique mondial
        elif in_rect(self.WORLD_GRAPH_BOUND, x, y):
            center_text(
                self.screen, data_font,
                f"x : {int((x - self.WORLD_GRAPH_BOUND[0]) * self.COEF_WIDTH * len(self.world_data[0]))}",
                FG, 150, 50, 600, 15)
            center_text(
                self.screen, data_font, "y : {:.2e}".format(
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
            center_text(screen, font, key, FG, 300, 50, 130 + self.DELTA * x, 1600)
            x += 1

        center_text(
            self.screen, font, f"Evolution locale ({self.models[self.num_model].country.name})", FG, self.WIDTH, 30,
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
            w = data_font.size(form)[0]
            Y = self.HAUT - int(x * dx)
            pygame.draw.line(self.screen, FG, (self.MARGIN + self.LEFT_2, Y + self.TOP),
                             (self.MARGIN - 5 + self.LEFT_2, Y + self.TOP), 2)
            self.screen.blit(
                data_font.render(form, True, FG),
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
            self.N += model.N
            self.data.append([[model.param_dict[key]["value"] * model.N] for key in self.keys])
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
            c.show()
        # Affiche mes textes
        center_text(screen, font, "Evolution mondiale", FG, 700, 50, 650, 100)
        center_text(screen, font, "Population de départ", FG, 300, 50, 130, 1600)
        screen.blit(font.render("Simulation d'une épidémie de ...", True, FG), (20, 0))
        # Récupère les modèles et initialise la simulatio
        self.models = self.tbm.models
        self.init_model()
        self.update_world()
        self.change_countries(num_country)
        if not self.use_db:
            self.tbm.save_model_param()
        x = 0
        self.init_affichage()
        self.gen_data(x)
        for _ in range(int(self.nb_iterations[self.num_model])):
            x += 1
            self.y.append(len(self.y))
            self.gen_data(x)
            self.graph_value()
            if num_country == self.num_model and (not on_world or zoomed):
                self.update_country_info()
            else:
                self.update_world_info()
            if len(self.data[self.num_model][0]) >= 2:
                self.display_graph(1)
                self.display_graph(2)
        self.tbm.end()


class ScrollableFrame(Frame):

    def __init__(self, fen, *args, **kwargs):
        """ Frame mobile  liée à la molette de la souris
        ---
        """
        super().__init__(fen, *args, **kwargs)

        self.canvas = Canvas(self, width=228, height=160, bg=HEXBG, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack()
        scrollbar.pack_forget()
        self.bind('<Enter>', self.mouse_wheel_bind)
        self.bind('<Leave>', self.mouse_wheel_unbind)


    def mouse_wheel_bind(self, event):
        """ Créer le lien de la molette avec self.mousewheel
        ---
        """
        self.canvas.bind_all("<MouseWheel>", self.mouse_wheel)


    def mouse_wheel_unbind(self, event):
        """ Supprime le lien de la molette avec self.mousewheel
        ---
        """
        self.canvas.unbind_all("<MouseWheel>")


    def mouse_wheel(self, event):
        """ Déplace la frame avec la molette
        """
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class Menu:

    def __init__(self):
        """ Fenêtre de menu
        ---
        """
        self.use_db = None
        self.param = []
        self.event_list = []
        self.start_c = 0


    def select(self, b):
        """ Au clic d'un des deux boutons "Base de donnée" / "Paramètres"
        ---
        param :

            - b (bool) True utilise une base de donnée / False utilise des paramètres
        """
        # Renseigne la valeur et détruit la fenêtre
        self.use_db = b
        self.fen.destroy()
        self.fen.quit()
        # Action en fonction de la valeur
        if not self.use_db:
            self.ask_param()


    def ask_use_db(self):
        """ Ouvre la fenêtre de demande d'initialisation de la simulation
        ---
        """
        self.fen = Tk()
        self.fen.geometry("300x150")
        self.fen.minsize(300, 150)
        self.fen.configure(bg=HEXBG)
        self.fen.title("Initialisation")

        label = Label(self.fen, text="Comment initialiser la simulation ?")
        label.configure(bg=HEXBG, fg=HEXFG)
        label.place(x=50, y=30)

        bdd_btn = Button(self.fen, text="Base de donnée", command=lambda: self.select(True))
        bdd_btn.configure(bg="#202225", fg=HEXFG, activebackground="#40444B",
                        activeforeground=HEXFG,  borderwidth=0, highlightthickness=0)
        bdd_btn.place(x=30, y=80)

        param_btn = Button(self.fen, text="Paramètre", command=lambda: self.select(False))
        param_btn.configure(bg="#202225", fg=HEXFG, activebackground="#40444B",
                        activeforeground=HEXFG,  borderwidth=0, highlightthickness=0)
        param_btn.place(x=180, y=80)

        self.fen.focus_force()
        self.fen.mainloop()


    def get_param(self):
        """ Récupère les paramètres de la fenêtre des paramètres
        ---
        """
        self.start_c = self.list_start_box.curselection()[0]


    def on_close(self):
        """ A la fermeture de la fenêtre des paramètres
        ---
        """
        self.get_param()
        self.fen2.destroy()
        if self.param == []:
            self.ask_use_db()


    def add_event(self):
        """ Ajoute un événement
        ---
        """
        self.event_list.append("salut")
        a = Label(self.event_frame.scrollable_frame, text="salut" + str(len(self.event_list)), width=10)
        a.configure(fg=HEXFG, bg=HEXBG)
        a.pack()


    def ask_param(self):
        """ Ouvre la fenêtre des paramètres
        ---
        """
        self.fen2 = Tk()
        self.fen2.minsize(800, 500)
        self.fen2.configure(bg=HEXBG)
        self.fen2.title("Paramètres de simulation")
        self.fen2.protocol("WM_DELETE_WINDOW", self.on_close)

        self.lblf_event = LabelFrame(self.fen2, text=" Événements ", padx=10, pady=10)
        self.lblf_event.configure(bg=HEXBG, fg=HEXFG)
        self.lblf_event.place(x=520, y=20)

        self.event_frame = ScrollableFrame(self.lblf_event)
        self.event_frame.pack()

        self.add_event_btn = Button(self.fen2, text="Ajouter un événement", command=self.add_event)
        self.add_event_btn.configure(bg="#202225", fg=HEXFG, activebackground="#40444B", activeforeground=HEXFG, borderwidth=0, highlightthickness=0, width=20)
        self.add_event_btn.place(x=570, y=240)


        self.lblf_start = LabelFrame(self.fen2, text=" Pays d'origine de la pandémie ", padx=10, pady=10)
        self.lblf_start.configure(bg=HEXBG, fg=HEXFG)
        self.lblf_start.place(x=520, y=280)

        self.list_start_box = Listbox(self.lblf_start, width=38, height=10)
        self.list_start_box.configure(bg=HEXBG, fg=HEXFG, borderwidth=0, highlightthickness=0)
        self.list_start_box.pack(side="left", fill="y")

        self.scroll_start = Scrollbar(self.lblf_start, orient="vertical")
        self.scroll_start.config(command=self.list_start_box.yview)
        self.scroll_start.configure(bg="#202225", activebackground="#40444B", borderwidth=0, highlightthickness=0)
        self.scroll_start.pack()
        self.scroll_start.pack_forget()


        self.list_start_box.config(yscrollcommand=self.scroll_start.set)

        for x in range(len(countries)):
            self.list_start_box.insert(END, countries[x].name)
        self.list_start_box.select_set(0)


        self.ok_btn = Button(self.fen2, text="OK", command=self.on_close)
        self.ok_btn.configure(bg="#202225", fg=HEXFG, activebackground="#40444B", activeforeground=HEXFG,  borderwidth=0, highlightthickness=0, width=10)
        self.ok_btn.place(x=380, y=450)

        self.fen2.focus_force()
        self.fen2.mainloop()


countries = from_json(json.load(open("Country.json")))
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


global zoomed, on_world, num_country
changed = False
zoomed = False
on_world = True

# Liste des tag des pays
c_tag = [c.tag for c in countries]

# Le Thread principale
graph = MainThread(screen, countries)

# Les fenêtres de menu
menu = Menu()
menu.ask_use_db()
graph.use_db = menu.use_db
num_country = menu.start_c
try:
    if menu.use_db == None:
        quit()
    elif menu.use_db:
            graph.tbm.connect()
            graph.tbm.extract_model_from_db()
    else:
            graph.tbm.create_db(menu.param)
            graph.tbm.init_model()
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
                if not zoomed:
                    if in_rect((40, 650, 1550, 0), x, y):
                        for c in countries:
                            for cb in c.bound:
                                if in_rect(cb, x, y):
                                    for b in c.border:
                                        if in_poly((x, y), b):
                                            n = c_tag.index(c.tag)
                                            if num_country != n:
                                                num_country = n
                                                graph.change_countries(num_country)
                                            changed = zoomed = True
                                            on_world = False
                                            break

                        else:
                            if not on_world:
                                graph.update_world()
                                on_world = True

                else:
                    if in_rect(BTN_BOUND, x, y):
                        zoomed = on_world = False
                        create_mask(30, 10, 1540, 620, BG)
                        for c in countries:
                            c.show()

    if changed:
        changed = False
        graph.update()

    pygame.display.update()


# TODO:
#       - fen param
#       - modèle comp
#       - event
#       - estimation tps sim
#       - countries.json -> sql
#       - facteur évo°
#       - Alexis pls help
#       - opti zoom
