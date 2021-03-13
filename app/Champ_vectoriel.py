import numpy as np
from matplotlib import pyplot as plt


def afficher_champ_vecteur(xran, yran, grid, b, l):
    """ Affiche le champ vectoriel associé à l'équation différentielle du modèle SIR
    ---
    param :

        - xran (list(int)) la liste contenant la valeur minimale et maximale de x
        - xran (list(int)) la liste contenant la valeur minimale et maximale de y
        - grid (list(int)) le nombre de vecteur selon x et y
    """
    x = np.linspace(xran[0], xran[1], grid[0])
    y = np.linspace(yran[0], yran[1], grid[1])

    X, Y = np.meshgrid(x, y)
    # Equa diff du modèle SIR
    DX, DY = - b * X * Y, b * X * Y - l * Y

    # On normalise chaque vecteur

    # La longueur de chaque vecteur
    M = np.hypot(DX, DY)  # M est une matrice de valeur
    # Si les longueurs sont nuls on les met à 1
    M[M == 0] = 1.
    # on normalise
    DX = DX / M
    DY = DY / M

    # Le nom des axes
    plt.xlabel("Sains")
    plt.ylabel("Infectés")
    # affichage du champs (pivot est la position selon laquelle le vecteur pivote, scale redimensionne les vecteurs)
    plt.quiver(X, Y, DX, DY, np.arctan2(DX, DY), cmap='rainbow', pivot='mid', scale=grid[0])
    # Recentre selon les valeurs données
    plt.xlim(xran)
    plt.ylim(yran)
    # Affiche la grille
    plt.grid('on')


## Example
if __name__ == "__main__":
    afficher_champ_vecteur([-.5, 1], [-.5, 1], [40, 40], 0.5, 0.1)
    plt.show()

# Le lien d'ou je tire ça :
# https://gist.github.com/nicoguaro/6767643
