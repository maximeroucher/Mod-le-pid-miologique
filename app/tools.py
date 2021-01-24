import json
import os

# Mute l'import de pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'True'
# Postionne la fenêtre de l'application
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

import pygame
from shapely.geometry import Point, Polygon

from Pays import Pays

FG = (182, 185, 190)
# Couleur de fond
BG = (32, 34, 37)

# Vérification position point

def in_rect(points, x, y):
    """ Vérifie si un point est dans un rectangle
    ---
    param :

        - points (list) liste des points (l, b, r, t)
        - x (int) position x de la souris
        - y (int) position y de la souris

    result :

        - bool
    """
    return points[0] <= x and points[3] <= y and points[1] >= y and points[2] >= x


def in_poly(point, poly_points):
    """ Vérifie si un point est dans un polygone
    ---
    param :

        - point (tuple(x, y)) point à verifier
        - polypoint (list(tuple)) liste des points d'un polygone

    result :

        - bool
    """
    return Polygon(poly_points).contains(Point(point))


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

        - list(str) le texte séparer sur plusieurs lignes pour améliorer l'affichage
        - pygame.font.SysFont la font qui maximise l'espace occupé
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

def create_mask(t, l, w, h, color, screen):
    """ Créer un masque pour réécrire du texte
    ---
    param :

        - t (int) top
        - l (int) left
        - w (int) largeur
        - h (int) hauteur
        - color ((r, g, b)) la couleur du masque
        - screen (pygame.Surface) la surface sur laquelle afficher le pays
    """
    country_name_mask = pygame.Surface((w, h), pygame.SRCALPHA)
    country_name_mask.fill(color)
    screen.blit(country_name_mask, (l, t))


def update_mask(n, screen):
    """ Met des masques sur les textes qui doivent être changés
    ---
    param :

        - n (int) le nombre de masque a créer
        - screen (pygame.Surface) la surface sur laquelle afficher le pays
    """
    w = 750 / n
    create_mask(170, 1695, 110, 50, BG, screen)
    for x in range(1, n + 1):
        create_mask(177 + w * x, 1695, 110, 50, BG, screen)


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


def get_scale_value(m, M, nb_pt):
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


# Runge Kutta 4

def RK4(h, T, y0, f):
    # f verifie : y' = f(y, t)
    t = 0
    y = y0
    res_t = [0]
    res_y = [y0]
    while t < T:
        k1 = f(t, y)
        k2 = f(t + 1 / 2 * h, y + 1 / 2 * h * k1)
        k3 = f(t + 1 / 2 * h, y + 1 / 2 * h * k2)
        k4 = f(t + h, y + h * k3)
        y = y + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        t = t + h
        res_t.append(t)
        res_y.append(y)
    return res_t, res_y



import numpy as np
from matplotlib import pyplot as plt


def plotdf(xran, yran, grid):
    x = np.linspace(xran[0], xran[1], grid[0])
    y = np.linspace(yran[0], yran[1], grid[1])

    X, Y = np.meshgrid(x, y)
    # Equa diff du modèle SIR
    DX, DY = - X * Y, X * Y - Y
    M = np.hypot(DX, DY)
    M[M == 0] = 1.
    DX = DX / M
    DY = DY / M

    plt.xlabel("Sains")
    plt.ylabel("Infectés")
    plt.quiver(X, Y, DX, DY, np.arctan2(DX, DY), cmap='rainbow', pivot='mid', scale=grid[0])
    plt.xlim(xran)
    plt.ylim(yran)
    plt.grid('on')


## Example
if __name__ == "__main__":
    plotdf(xran=[-1, 3], yran=[-1, 3], grid=[50, 50])
    plt.show()


# https://gist.github.com/nicoguaro/6767643
