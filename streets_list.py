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

import  configparser
Config = configparser.ConfigParser()
Config.read("config.poppy")

x0_real         = int(Config.get('config', 'x0_real'))
y0_real         = int(Config.get('config', 'y0_real'))
x1_real         = int(Config.get('config', 'x1_real'))
y1_real         = int(Config.get('config', 'y1_real'))
scr             = Config.get('config', 'scr')
delta1          = int(Config.get('config', 'delta1'))
nx              = int(Config.get('config', 'nx'))
ny              = int(Config.get('config', 'ny'))
a               = Config.get('config', 'a').split(',')
b               = Config.get('config', 'b').split(',')

x1_delta        = x0_real + nx * delta1
y1_delta        = y0_real + ny * delta1

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
    if has_overlap(x0_real, x1_delta, commune['xMin'], commune['xMax']) | has_overlap(y0_real, y1_delta, commune['yMin'], commune['yMax']):
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

        eta = (xMin-x0_real)/delta1; gridX0 = math.floor(eta); sX0 = math.floor((eta-math.floor(eta))*2);
        eta = (y0_real-yMin)/delta1; gridY0 = 1+math.floor(eta); sY0 = math.floor((eta-math.floor(eta))*2);
    
        eta = (xMax-x0_real)/delta1; gridX1 = math.floor(eta); sX1 = math.floor((eta-math.floor(eta))*2);
        eta = (y0_real-yMax)/delta1; gridY1 = 1+math.floor(eta); sY1 = math.floor((eta-math.floor(eta))*2);

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
        na = street['nom'].title().replace(' De ', ' de ').replace(" D' ", " d'").replace(' Du ',' du ').replace(' Des ', ' des ').replace(' La ', ' la ').replace(' Aux ', ' aux ')
        nb = na
        for pre in ['Allée', 'Chemin', 'Rue', 'Avenue', 'Chaussée', 'Carrefour', 'Cour', 'Cité', 'Camp', 'Espace', 'Tienne', 'Tour', 'Boulevard', 'Route', 'Ruelle', 'Place', 'Sentier', 'Square', 'Voie', 'Thier', 'Pré', 'Plateau', 'Fond', 'Clos', 'Tige', 'Quai', 'Porte', 'Bois', 'Impasse', 'Drève', 'Fond', 'Voisinage', 'Venelle']:
            nb = nb.replace(pre + ' de la ', '') 
            nb = nb.replace(pre + " de l'", '')
            nb = nb.replace(pre + ' de ', '').replace(pre + ' des ', '').replace(pre + ' aux ', '').replace(pre + ' du ', '').replace(pre + ' aux ', '').replace(pre + " d' ", '')
            nb = nb.replace(pre + ' ', '')
            
        tab.append([na, nb, u])             # array by municipality
        gentab.append([name, na, nb, u])    # global array

    if len(tab) > 0:
        tab = sorted(tab,key=lambda x: x[1])
        print(name)
        print('-------------------------')
        print(tabulate.tabulate(tab))

#with open("streets.csv", "w") as f:
#    writer = csv.writer(f)
#    writer.writerows(gentab)
