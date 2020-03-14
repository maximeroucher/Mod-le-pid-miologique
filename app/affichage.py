import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import shapefile
import numpy as np
import json

from dbfread import DBF, read

""" table = read('110m_cultural/ne_110m_admin_0_countries.dbf', encoding='utf-8')
tags = ["POP_EST", "GDP_MD_EST"]

l = []
for y in range(len(table)):
    d = {table[y]["NAME_FR"]: {x : table[y][x] for x in tags}}
    l.append(d)
json.dump(l, open("Country_data.json", "w"))
"""
""" 
sf = shapefile.Reader("110m_cultural/ne_110m_admin_0_scale_rank.shp")

pts = sf.shapes()[190].points
pts_x, pts_y = [a for a, b in pts], [b for a, b in pts]
plt.plot(pts_x, pts_y)
plt.xlim(-185, 185)
plt.ylim(-95, 95)
 """
""" for x in range(len(sf)):
    pts = sf.shapes()[x].points
    pts_x, pts_y = [a for a, b in pts], [b for a, b in pts]
    plt.plot(pts_x, pts_y)
    plt.xlim(-185, 185)
    plt.ylim(-95, 95) """

def afficher_sim(data):
    """ Afifiche le résultat de la simulation
    ---
    param : data (dict[label : list])
    """
    axe_x = list(range(len(list(data.values())[0])))
    for x in list(data.keys()):
        plt.plot(axe_x, data[x], label=x)
    plt.legend()
    plt.show()
