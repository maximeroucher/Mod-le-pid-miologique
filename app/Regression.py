import math
import matplotlib.pyplot as plt


def calcul_logisitique(K, R, A, x):
    return K / (1 + A * math.exp(R * x))


class Regression:

    def __init__(self, pts, min_pts):
        """ Régression linéaire de la simulation
        ---
        param :

            - pts (list(str, int)) la liste des points
            - min_pts (int) le nombre minimal de points pour le calcul de la régression
        """
        self.pts = pts
        self.nb_pts = min(min_pts, len(pts))
        self.K = 0
        self.R = 0
        self.A = 0


    def sq_error(self, pts, K, R, A):
        """ Calcul le carré de l'erreur
        ---
        result :

            - int
        """
        r = 0
        d = int(len(self.pts) / self.nb_pts)
        for x in range(self.nb_pts):
            r += (self.pts[x * d][1] - calcul_logisitique(K, R, A, self.pts[x * d][0]))**2
        return r


    def regression(self, minK, maxK, minR, maxR, minA, maxA, nb_iteration):
        """ Calcul la régression de le courbe donnée
        ---
        param :

            - minK (int) la borne inférieure de K
            - maxK (int) la borne supérieure de K
            - minR (int) la borne inférieure de R
            - maxR (int) la borne supérieure de R
            - minA (int) la borne inférieure de A
            - maxA (int) la borne supérieure de A
            - nb_iteration (int) le nombre d'itération de calcul

        result :

            - R, A (int, int)
        """
        minS = -1
        minCouple = (0, 0)
        for _ in range(nb_iteration):
            dK = (maxK - minK) / 10
            dR = (maxR - minR) / 10
            dA = (maxA - minA) / 10
            for k in range(10):
                for n in range(10):
                    m = self.sq_error(pts, minK + k * dK, minR + k * dR, minA + n * dA)
                    if minS == -1 or minS > m:
                        minS = m
                        minCouple = (minK + k * dK, minR + k * dR, minA + n * dA)
            nK, nR, nA = minCouple
            maxK = nK + dK
            minK = nK - dK
            maxR = nR + dR
            minR = nR - dR
            maxA = nA + dA
            minA = nA - dA
        return minCouple



RANGE = 30
K = 1
R = .1
A = .01
x = list(range(100))
y = [calcul_logisitique(K, R, A, z) for z in x]
px = x[0:RANGE]
py = y[0:RANGE]
plt.plot(x, y)
plt.plot(px, py)

pts = list(zip(px, py))
Reg = Regression(pts, 30)
nK, nR, nA = Reg.regression(.5, 1.5, -.5, .5, 0, .05, 1000)
print(nK, nR, nA)
yy = [calcul_logisitique(nK, nR, nA, z) for z in x]
plt.plot(x, yy)
plt.show()
