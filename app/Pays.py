import os
import random

# Empêche l'import de pygame d'afficher du texte
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'True'

import pygame

# Couleur du texte, des axes des graphiques et des bords des pays
FG = (182, 185, 190)


class Pays:

    def __init__(self, tag, nom, pop, frontiere, carre):
        """ Initialisation d'un pays
        ---
        paramètres :

            - tag (str) le format du nom de pays
            - name (str) le nom français du pays
            - pop (int) la population estimée du pays
            - frontiere (list(tuple)) le contour du pays
            - carre (list(tuple)) le carré dans lequel le pays est inscrit
        """
        self.tag = tag
        self.nom = nom
        self.pop = pop
        self.frontiere = frontiere
        self.carre = carre
        self.r = random.randint(0, 50)
        self.g = random.randint(120, 180)
        self.b = random.randint(200, 235)


    def afficher(self, surf):
        """ Affiche le pays
        ---
        paramètre :

            - surf (pygame.Surface) la surface sur laquelle afficher le pays
        """
        for point in self.frontiere:
            pygame.draw.polygon(surf, (self.r, self.g, self.b), point)
            pygame.draw.lines(surf, FG, True, point, 1)


    def afficher_frontiere(self, screen):
        """ Affiche le carré autour du pays
        ---
        paramètre :

            - screen (pygame.Surface) la surface sur laquelle afficher le pays
        """
        for rect in self.carre:
            pygame.draw.lines(screen, (255, 0, 0), True, [(rect[0], rect[1]),
                                                          (rect[2], rect[1]), (rect[2], rect[3]), (rect[0], rect[3])], 1)


    def vers_json(self):
        """ Renvoie la classe sous forme Json
        ---
        résultat:

            - json
        """
        return {self.tag: {"NAME_FR": self.name, "POP_EST": self.pop, "geometry": self.frontiere, "bounds": self.carre}}


    def __lt__(self, value):
        """ Opérateur de comparaison
        ---
        résultat :

            - bool
        """
        return self.nom < value.nom
