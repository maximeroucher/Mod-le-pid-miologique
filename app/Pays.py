import os
import random

# Mute l'import de pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'True'

import pygame

# Couleur du texte, des axes des graphiques et des bords des pays
FG = (182, 185, 190)


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


    def show(self, screen):
        """ Affiche le pays
        ---
        param :

            - screen (pygame.Surface) la surface sur laquelle afficher le pays
        """
        for point in self.border:
            pygame.draw.polygon(screen, (self.r, self.g, self.b), point)
            pygame.draw.lines(screen, FG, True, point, 1)


    def show_border(self, screen):
        """ Affiche le carré autour du pays
        ---
        param :

            - screen (pygame.Surface) la surface sur laquelle afficher le pays
        """
        for rect in self.bound:
            pygame.draw.lines(screen, (255, 0, 0), True, [(rect[0], rect[1]),
                                                          (rect[2], rect[1]), (rect[2], rect[3]), (rect[0], rect[3])], 1)


    def to_json(self):
        """ Renvoie la classe sous forme Json
        ---
        result:

            - json
        """
        return {self.tag: {"NAME_FR": self.name, "POP_EST": self.pop, "GDP_MD_EST": self.pib, "geometry": self.border, "bounds": self.bound}}


    def toggle_close(self):
        self.r, self.b = self.b, self.r
        self.show()


    def __lt__(self, value):
        """ Opérateur de comparaison
        ---
        result :

            - bool
        """
        return self.name < value.name
