Creates a street list using the webservices of the Walloon Region

# Build a street list using the ICAR webservice from the Walloon Region #
#                                                                       #
# Author:  Christophe Cloquet, Poppy, Brussels (2016)                   #
#          christophe@my-poppy.eu                                       #
#          www.my-poppy.eu                                              #
#                                                                       #
# Licence: MIT                                                          #

# This code assumes that you have a rectangular map, with a Lambert 72 coordinates system
# and a grid superimposed on it
# The top left coordinate is (x0, y0)
# A square of the grid has a size in meters of (dx, dy)
# There are nx (resp ny) squares along the x (resp y) coordinates, labeled A, B, C ... (resp 01, 02, 03, ...)
