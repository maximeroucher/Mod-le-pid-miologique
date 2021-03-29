from __future__ import print_function
import math

import matplotlib.pyplot as plt
# Barre de progression
from tqdm import tqdm
import time
import numpy as np
from matplotlib import cm
from matplotlib.ticker import LinearLocator
from mpl_toolkits.mplot3d import Axes3D
import datetime


def calcul_logistique(param, x):
    """ Calcul de la courbe de la fonction logistique
    ---
    param :

        - param (list(float))
        - x (float)

    result :

        - float
    """
    assert len(param) == 3
    K, R, A = param
    return K / (1 + A * math.exp(R * x))


def der_log(param, x):
    """ Calcul de la courbe de la dérivée de la fonction logistique
    ---
    param :

        - param (list(float))
        - x (float)

    result :

        - float
    """
    assert len(param) == 3
    K, R, A = param
    H = A * math.exp(R * x)
    return - (K * R * H) / (1 + H)**2


class Regression:

    def __init__(self, pts, min_pts, f):
        """ Régression linéaire de la simulation
        ---
        param :

            - pts (list(str, int)) la liste des points
            - min_pts (int) le nombre minimal de points pour le calcul de la régression
            - f (func(float -> float)) la fonction à utiliser pour la régression
        """
        self.pts = pts
        self.nb_pts = min(min_pts, len(pts))
        self.f = f


    def sq_error(self, pts, param):
        """ Calcul le carré de l'erreur
        ---
        result :

            - pts (list(float)) la liste en entrée
            - param (list(float))

        result :

            - float
        """
        r = 0
        d = int(len(self.pts) / self.nb_pts)
        for x in range(self.nb_pts):
            r += (self.pts[x * d][1] - self.f(param, self.pts[x * d][0]))**2
        return r


    def regression(self, range_param, nb_iteration):
        """ Calcul la régression de le courbe donnée
        ---
        param :

            - param (list(float))
            - nb_iteration (int) le nombre d'itération de calcul

        result :

            - list(float)
        """
        print("Début de la régression")
        t = time.perf_counter()
        lparam = len(range_param)
        params = [0 for _ in range(lparam)]
        minS = -1
        RANGE = 10
        diff = 0
        for k in range(nb_iteration):
            R = RANGE
            dparam = [(range_param[k][1] - range_param[k][0]) / R for k in range(lparam)]
            iterations = [0 for _ in range(lparam)]
            for _ in tqdm(range((R + 1)**lparam), leave=False):
                p = [range_param[i][0] + iterations[i] * dparam[i] for i in range(lparam)]
                err = self.sq_error(pts, p)
                if minS == -1 or minS > err:
                    minS = err
                    params = p
                for i in range(lparam):
                    iterations[i] = iterations[i] + 1
                    if iterations[i] > R:
                        iterations[i] = 0
                    else:
                        break
            for i in range(lparam):
                range_param[i][0] = params[i] - dparam[i]
                range_param[i][1] = params[i] + dparam[i]
            print(f"Itération n° {k + 1}  \t Erreur : {minS} \t Différence : {abs(diff - minS)}")
            diff = minS
        print(
            f"Fin de la régression, durée : {datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.perf_counter() - t), '%H:%M:%S:%f')}")
        return params


    def calcul_r2(self, y, x, f):
        """ Calcul de l'erreur de la regression
        ---
        param :

            - y (list(float)) les données en sortie
            - x (list(float)) les données en entrée
            - f (func(float -> float)) la fonction de regression

        result :

            - float entre 0 et 1
        """
        Y = sum(y) / len(y)
        Stot = sum([(y[k] - Y)**2 for k in range(len(y))])
        Sres = sum([(y[k] - f(x[k]))**2 for k in range(len(y))])
        return 1 - Sres / Stot


# Données tirées de la simulation
data = {'Sains':
    [1998, 1996, 1995, 1994, 1991, 1990, 1989, 1988, 1988, 1987, 1984, 1982, 1978, 1974, 1971, 1970, 1966, 1963, 1961, 1958, 1954, 1952, 1950, 1948, 1946, 1940, 1935, 1933, 1926, 1923, 1919, 1918, 1916, 1911, 1905, 1899, 1896,
    1888, 1887, 1880, 1877, 1871, 1868, 1858, 1853, 1844, 1837, 1832, 1823, 1813, 1800, 1791, 1786, 1780, 1776, 1769, 1763, 1756, 1746, 1739, 1731, 1717, 1711, 1705, 1700, 1689, 1681, 1675, 1669, 1662, 1660, 1659, 1652, 1641,
    1628, 1621, 1612, 1606, 1594, 1587, 1582, 1573, 1568, 1562, 1557, 1550, 1547, 1542, 1538, 1536, 1528, 1523, 1514, 1503, 1496, 1489, 1484, 1478, 1470, 1465, 1462, 1453, 1444, 1442, 1433, 1417, 1402, 1392, 1380, 1369, 1362,
    1354, 1338, 1331, 1319, 1305, 1296, 1284, 1272, 1259, 1251, 1247, 1239, 1233, 1229, 1222, 1214, 1202, 1200, 1194, 1189, 1187, 1183, 1174, 1163, 1154, 1136, 1129, 1125, 1114, 1101, 1087, 1080, 1073, 1067, 1059, 1050, 1039,
    1032, 1025, 1014, 1002, 992, 982, 969, 966, 954, 951, 945, 934, 928, 922, 914, 907, 897, 890, 883, 876, 865, 857, 851, 843, 836, 831, 825, 814, 804, 796, 789, 782, 769, 761, 752, 741, 730, 723, 714, 705, 698, 689, 683, 676,
    672, 665, 661, 653, 645, 639, 631, 622, 614, 612, 610, 603, 599, 594, 589, 587, 585, 579, 570, 566, 554, 547, 543, 541, 538, 533, 522, 514, 509, 504, 499, 492, 486, 476, 467, 464, 460, 453, 450, 447, 443, 437, 431, 426, 422,
    418, 415, 410, 408, 403, 399, 398, 392, 390, 385, 382, 374, 369, 364, 358, 350, 349, 346, 340, 340, 338, 334, 329, 327, 316, 307, 302, 301, 301, 300, 298, 296, 292, 288, 286, 282, 277, 272, 271, 270, 267, 264, 260, 260, 258,
    254, 253, 253, 250, 246, 245, 243, 240, 231, 226, 223, 220, 214, 209, 208, 206, 204, 201, 199, 197, 195, 190, 189, 189, 189, 187, 184, 182, 179, 174, 168, 163, 162, 162, 157, 155, 153, 147, 142, 137, 128, 125, 124, 123, 121,
    119, 117, 116, 115, 114, 114, 114, 114, 114, 113, 111, 106, 105, 105, 104, 104, 104, 104, 104, 104, 102, 100, 99, 97, 93, 89, 86, 83, 76, 75, 75, 74, 74, 74, 73, 72, 72, 70, 69, 67, 67, 66, 65, 65, 65, 65, 65, 65, 65, 65, 63,
    62, 61, 59, 58, 58, 58, 58, 57, 57, 56, 56, 56, 56, 56, 55, 55, 55, 55, 55, 55, 54, 54, 54, 53, 53, 53, 53, 53, 52, 52, 52, 52, 52, 52, 52, 52, 52, 52, 52, 52, 52, 51, 51, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50,
    50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50],
        'Infectés':
    [2, 4, 5, 6, 9, 10, 11, 12, 12, 13, 16, 18, 22, 26, 29, 30, 34, 37, 39, 42, 46, 48, 50, 52, 54, 60, 65, 67, 74, 77, 81, 82, 84, 89, 95, 101, 104, 112, 113, 120, 123, 129, 132, 141, 146, 155, 161, 164, 171, 179, 191, 200, 205,
    211, 213, 219, 222, 229, 236, 240, 247, 258, 263, 267, 271, 282, 288, 293, 294, 298, 295, 295, 300, 307, 317, 321, 323, 326, 334, 335, 337, 341, 337, 342, 342, 344, 346, 344, 342, 338, 340, 341, 346, 347, 353, 352, 355, 350,
    352, 348, 349, 350, 354, 350, 349, 356, 360, 359, 365, 368, 368, 371, 379, 380, 382, 390, 393, 400, 395, 401, 398, 397, 401, 397, 397, 398, 400, 397, 395, 393, 391, 389, 389, 394, 400, 404, 416, 416, 413, 416, 426, 431, 430,
    437, 436, 436, 440, 444, 444, 437, 441, 442, 442, 445, 446, 439, 443, 433, 431, 432, 423, 419, 418, 403, 411, 411, 411, 413, 416, 412, 412, 413, 411, 410, 410, 413, 411, 413, 416, 418, 420, 420, 418, 422, 420, 421, 419, 419,
    418, 424, 418, 421, 417, 413, 406, 407, 406, 406, 404, 397, 391, 385, 378, 377, 373, 371, 370, 366, 364, 361, 363, 351, 353, 350, 347, 346, 342, 336, 341, 341, 341, 339, 340, 343, 336, 331, 333, 329, 326, 319, 320, 317, 306,
    300, 300, 299, 299, 298, 293, 292, 288, 287, 280, 277, 275, 272, 268, 265, 263, 260, 258, 258, 259, 250, 249, 248, 245, 246, 242, 241, 239, 243, 247, 248, 246, 240, 235, 233, 230, 226, 225, 219, 212, 213, 214, 211, 209, 208,
    200, 196, 191, 186, 189, 185, 179, 179, 177, 172, 171, 167, 171, 172, 172, 171, 173, 172, 173, 174, 172, 168, 167, 167, 163, 165, 166, 163, 157, 155, 151, 151, 146, 149, 149, 152, 145, 141, 139, 138, 138, 143, 147, 146, 152,
    152, 152, 150, 148, 145, 144, 143, 142, 137, 136, 132, 132, 131, 129, 128, 132, 129, 127, 125, 122, 120, 118, 112, 108, 107, 107, 103, 102, 104, 106, 104, 106, 111, 109, 106, 107, 102, 99, 97, 97, 93, 90, 89, 88, 86, 79, 77,
    75, 72, 72, 70, 68, 66, 63, 62, 59, 56, 58, 59, 56, 55, 54, 54, 54, 53, 52, 51, 50, 49, 48, 47, 45, 44, 44, 42, 41, 41, 39, 37, 35, 33, 32, 31, 30, 29, 28, 28, 26, 25, 22, 21, 20, 18, 17, 15, 15, 16, 16, 16, 15, 15, 15, 14,
    14, 14, 13, 12, 12, 12, 12, 12, 12, 12, 11, 10, 8, 8, 7, 7, 7, 7, 6, 6, 6, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 3, 3, 2, 2, 2, 1, 1, 1, 1, 0],
        'Rétablis':
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 4, 6, 8, 9, 9, 9, 9, 11, 12, 15, 15, 18, 21, 22, 25, 26, 28, 29, 29, 31, 32, 37, 40,
    45, 46, 48, 52, 55, 58, 65, 68, 72, 78, 81, 86, 95, 96, 101, 106, 107, 114, 120, 126, 132, 136, 140, 150, 151, 159, 161, 172, 178, 187, 189, 197, 202, 208, 218, 227, 238, 249, 255, 263, 270, 275, 283, 289, 299, 305, 311, 316,
    333, 340, 351, 356, 360, 370, 374, 380, 386, 401, 405, 413, 420, 424, 428, 432, 437, 442, 448, 455, 462, 470, 473, 482, 490, 490, 497, 505, 510, 517, 524, 538, 545, 556, 566, 573, 585, 595, 603, 616, 624, 634, 649, 659, 668,
    690, 692, 699, 706, 711, 719, 731, 737, 744, 753, 759, 765, 773, 785, 791, 795, 800, 811, 819, 830, 837, 850, 856, 867, 876, 884, 887, 899, 903, 911, 922, 933, 940, 949, 955, 965, 981, 995, 1003, 1012, 1020, 1028, 1035, 1041,
    1047, 1051, 1060, 1067, 1083, 1093, 1103, 1110, 1113, 1120, 1131, 1137, 1145, 1150, 1157, 1161, 1165, 1178, 1193, 1200, 1207, 1214, 1228, 1230, 1236, 1251, 1263, 1269, 1275, 1279, 1284, 1292, 1298, 1304, 1310, 1321, 1325,
    1333, 1338, 1347, 1353, 1363, 1371, 1378, 1384, 1391, 1401, 1405, 1412, 1415, 1416, 1424, 1430, 1434, 1441, 1446, 1450, 1453, 1459, 1465, 1469, 1474, 1482, 1487, 1495, 1506, 1510, 1514, 1518, 1521, 1525, 1536, 1544, 1549,
    1556, 1557, 1562, 1568, 1571, 1577, 1583, 1586, 1593, 1598, 1602, 1605, 1609, 1613, 1619, 1619, 1620, 1624, 1631, 1634, 1636, 1642, 1645, 1645, 1648, 1654, 1658, 1665, 1667, 1675, 1677, 1683, 1685, 1693, 1697, 1704, 1707,
    1709, 1710, 1711, 1717, 1720, 1723, 1724, 1727, 1731, 1736, 1739, 1741, 1743, 1749, 1750, 1754, 1754, 1755, 1758, 1761, 1762, 1766, 1768, 1771, 1774, 1776, 1778, 1784, 1788, 1791, 1793, 1798, 1801, 1803, 1805, 1810, 1811,
    1813, 1816, 1819, 1819, 1824, 1827, 1830, 1831, 1835, 1840, 1842, 1845, 1847, 1855, 1858, 1860, 1863, 1863, 1865, 1867, 1869, 1872, 1875, 1879, 1883, 1883, 1883, 1886, 1887, 1888, 1889, 1889, 1891, 1892, 1893, 1894, 1895,
    1897, 1898, 1900, 1901, 1901, 1903, 1905, 1905, 1907, 1910, 1912, 1914, 1915, 1916, 1918, 1919, 1920, 1920, 1922, 1923, 1926, 1927, 1928, 1930, 1931, 1933, 1933, 1933, 1933, 1934, 1935, 1935, 1935, 1936, 1936, 1936, 1937,
    1938, 1938, 1938, 1938, 1938, 1938, 1938, 1939, 1940, 1942, 1942, 1943, 1943, 1943, 1943, 1944, 1944, 1944, 1945, 1945, 1945, 1945, 1945, 1945, 1945, 1945, 1945, 1945, 1946, 1947, 1947, 1948, 1948, 1948, 1949, 1949, 1949,
    1949, 1950]}


def calc_I(r, l):
    """ Déduit la courbe de I en fonction de celle de R avec l'équation R' = l * I, l constante
    ---
    param :

        - r (list(float)) les points de la courbe de R
        - l (float) la constante

    result :

        - list(float)
    """
    res = [0]
    for k in range(len(r) - 1):
        res.append(1 / l * (r[k + 1] - r[k]))
    return res


def calc_S(r, i, pop):
    """ Déduit la courbe de S en fonction de R et I car R + I + P est constant par hypothèse
    ---
    param :

        - r (list(float)) les points de la courbe de R
        - i (list(float)) les points de la courbe de I
        - pop (int) la population totale de la simulation

    result :

        - list(float)
    """
    return [pop - r[k] - i[k] for k in range(len(r))]


def calcul_cst_grad(i, b, l, mu):
    a, c, d, e = 0, 0, 0, 0
    for k in range(len(s)):
        if mu + l * math.log(s[k]) - s[k] >= 0:
            lk = math.log(s[k])
            a += lk ** 2
            c += lk
            d -= (i[k] + s[k]) * lk
            e += s[k] - i[k]
    return a, len(s), 2 * c, 2 * d, 2 * e


def calc_grad(l, mu, i, s):
    a, b, c, d, e = calcul_cst_grad(i, s, l, mu)
    return (2 * a * l + c * mu + d, c * l + 2 * b * mu + e)


def remonte_gradient(l1, mu1, i, s, step):
    last = [l1, mu1]
    new = [l1, mu1]
    x = 0
    while last[0] - new[0] + last[1] - new[1] > 0 or x == 0:
        grad = calc_grad(new[0], new[1], i, s)
        last = [new[0], new[1]]
        new[0] = new[0] - step * grad[0]
        new[1] = new[1] - step * grad[1]
        x += 1
    return last


# Nombre de points pris en compte pour la régression (le but est de pouvoir minimiser ce paramètre)
RANGE = 5
# Nombre de point de la régression
NB_PTS = 100

# Extrait chaque courbe des données
s = data["Sains"]
i = data["Infectés"]
r = data["Rétablis"]

print(remonte_gradient(.01, 100, i, s, 1e-4))

"""
calcul_surf = lambda x, y : a * x ** 2 + b * y ** 2 + c * x * y + d * x + e * y

X = np.arange(0, 2500, 100)
Y = np.arange(0, 1000, 100)
X, Y = np.meshgrid(X, Y)
Z = calcul_surf(X, Y)


fig = plt.figure()
ax = fig.gca(projection='3d')
surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.rainbow,
                       linewidth=0, antialiased=False)

plt.show()
"""

""" 
x = list(range(len(r)))

# Exttrait les données à fournir pour la régression
px = x[0:RANGE]
py = r[0:RANGE] # on fait une régression sur la courbe R

# Transforme les deux listes en une seule [[x0, y0], [x1, y1], ...]
pts = list(zip(px, py))

Reg = Regression(pts, NB_PTS, calcul_logistique)
# Calcule la régression
nK, nR, nA = Reg.regression([[0, 2000], [-.1, 0], [0, 100]], 15)
err = Reg.calcul_r2(r, x, lambda x: calcul_logistique([nK, nR, nA], x))
# Calcul les points de la courbe (donc plus que sur le domaine de régression)
rr = [calcul_logistique([nK, nR, nA], z) for z in x]
# En déduit I
ii = calc_I(rr, 2.5e-2)
# En déduit S
ss = calc_S(rr, ii, 2000)

print(f"Régression :\n- K = {nK}\n- R = {nR}\n- A = {nA}\n- r² = {err}")

# Affiche le tout
plt.plot(x, r)
# plt.plot(s)
# plt.plot(i)
plt.plot(px, py)
plt.plot(x, rr)
#plt.plot(x, ii)
#plt.plot(x, ss)
plt.show()
 """
