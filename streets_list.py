 ####################################################################### 
#                                                                       #
# Build a street list using the ICAR webservice from the Walloon Region #
#                                                                       #
# Author:  Christophe Cloquet, Poppy, Brussels (2016)                   #
#          christophe@my-poppy.eu                                       #
#          www.my-poppy.eu                                              #
#                                                                       #
# Licence: MIT                                                          #
#                                                                       #
 ####################################################################### 

import csv
import requests
import json
import math
import tabulate

#######################
# PARAMETERS
# #####################

# This code assumes that you have a rectangular map, with a Lambert 72 coordinates system
# and a grid superimposed on it
# The top left coordinate is (x0, y0)
# A square of the grid has a size in meters of (dx, dy)
# There are nx (resp ny) squares along the x (resp y) coordinates, labeled A, B, C ... (resp 01, 02, 03, ...)

x0  = 115000 # coord MIN (gauche de la carte) - doivent être les coordonnées réelles (la carte n'est pas exactement ce qui a été demandé)
y0  = 104108 # coord MAX (haut de la carte)   - doivent être les coordonnées réelles (la carte n'est pas exactement ce qui a été demandé)
dx  = 1250   # width in meters of a main grid square 
dy  = 1250   #
nx  = 26     # number of grid squares in x
ny  = 33     # number of grid squares in y

#main grid labels (X)
a   = ['A', 'B', 'B', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

#subgrid (4 subsquares)
b   = ['a', 'b', 'c', 'd']

#     0 1            0 1
#0    a b         0  0 1
#1    c d         1  2 3

x1 = x0 + nx * dx
y1 = y0 + ny * dy


# 1. gets the list of the municipalities in the rectangle
# -------------------------------------------------------
names     = []
gentab    = []
r         = requests.get('http://geoservices.wallonie.be/geolocalisation/rest/getListeCommunes/')
localites = r.json()
communes  = localites['communes']

def has_overlap(x0, x1, xmin, xmax):
    # is there an overlap between the two segments ?
    # x0, x1 : limit of the grid
    # xmin, xmax : limits of the commune

    if ((x0 <= xmin) & (xmin <= x1)) | ((x0 <= xmax) & (xmax <= x1)) | ((x0 <= xmin) & (xmax <= x1)):
        return True
    else:
        return False
    
for commune in communes:
    if has_overlap(x0, x1, commune['xMin'], commune['xMax']) | has_overlap(y0, y1, commune['yMin'], commune['yMax']):
        names.append(commune['nom'])

print(names)
gentab = []


# 2. for each municipality, get the streets, and compute the coordinates on the grid
# ----------------------------------------------------------------------------------

for name in names:
    tab     = []
    r       = requests.get('http://geoservices.wallonie.be/geolocalisation/rest/getListeRuesByCommune/'+name+'/')

    streets=r.json()
    
    if (r.status_code != 200):          print('************' +str(r.status_code))
    if (streets['errorMsg'] != None):   print('*************' + streets['errorMsg'])
    
    for street in streets['rues']:
        
        xMin = street['xMin'];  xMax = street['xMax']
        yMin = street['yMin'];  yMax = street['yMax']

        eta = (xMin-x0)/dx; gridX0 = math.floor(eta); sX0 = math.floor((eta-math.floor(eta))*2);
        eta = (y0-yMin)/dy; gridY0 = math.floor(eta); sY0 = math.floor((eta-math.floor(eta))*2);
    
        eta = (xMax-x0)/dx; gridX1 = math.floor(eta); sX1 = math.floor((eta-math.floor(eta))*2);
        eta = (y0-yMax)/dy; gridY1 = math.floor(eta); sY1 = math.floor((eta-math.floor(eta))*2);

        # streets that are out of the rectangle even though if a part of the municipality is in the rectangle
        if gridX0 >= len(a):
            G = '+'
            continue
        elif gridX0 < 0:
            G = '-'
            continue
        else:
            G = a[gridX0]
    
        if gridX1 >= len(a):
            H = '+'
            continue
        elif gridX1 < 0:
            H = '-'
            continue
        else:
            H = a[gridX1]

        if (gridY0 < 0) | (gridY0 >= ny) | (gridY1 < 0) | (gridY1 >= ny):
            continue

        # format the labels
        u = G + '%02d' % (gridY0) + b[sX0+2*sY0]
        v = H + '%02d' % (gridY1) + b[sX1+2*sY1]

        if u != v:
            u+= ' - ' + v

        # extract the relevant part of the name, to sort
        na = street['nom'].title().replace(' De ', ' de ').replace(' Du ',' du ').replace(' Des ', ' des ').replace(' La ', ' la ')
        nb = na
        for pre in ['Allée', 'Chemin', 'Rue', 'Avenue', 'Chaussée', 'Boulevard', 'Route', 'Ruelle', 'Place', 'Sentier', 'Voie', 'Thier', 'Pré', 'Plateau', 'Fond', 'Clos', 'Tige', 'Quai', 'Porte', 'Bois', 'Impasse', 'Drève', 'Fond', 'Voisinage', 'Venelle']:
            nb = nb.replace(pre + ' de la ', '')
            nb = nb.replace(pre + ' de l\' ', '')
            nb = nb.replace(pre + ' de ', '').replace(pre + ' des ', '').replace(pre + ' du ', '').replace(pre + ' aux ', '')
            nb = nb.replace(pre + ' ', '')
            
        tab.append([na, nb, u])       # array by municipality
        gentab.append([name, na, nb, u])    # global array

    if len(tab) > 0:
        tab = sorted(tab,key=lambda x: x[1])
        print(name)
        print('-------------------------')
        print(tabulate.tabulate(tab))

with open("streets.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerows(gentab)
