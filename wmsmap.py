# *************************************
# create a printable map with a grid
# based on a WMS request to Omniscale
# *************************************

# A. vue d'ensemble
# telecharger wms depuis omniscale png (spécifier la résolution)
# créer un carroyage sur fond transparent
#
# B. faire indes des rues
#
# C. faire des planches d'atlas
# -> wms 'normal', des A3, ...

import  dateutil
from    owslib.wms import WebMapService
from    PIL import Image, ImageDraw, ImageFont
import  io, datetime, time, re, random, math, os
import  configparser
Config = configparser.ConfigParser()
Config.read("config.poppy")

im_path         = Config.get('config', 'im_path')
omniscale_api   = Config.get('config', 'omniscale_api')
size_real_x_mm  = int(Config.get('config', 'size_real_x_mm'))
size_real_y_mm  = int(Config.get('config', 'size_real_y_mm'))
dx_frame        = int(Config.get('config', 'dx_frame'))
dy_frame        = int(Config.get('config', 'dy_frame'))
dpi             = int(Config.get('config', 'dpi'))
fmt             = Config.get('config', 'fmt')
x0              = int(Config.get('config', 'x0'))
x1              = int(Config.get('config', 'x1'))
y0              = int(Config.get('config', 'y0'))
y1              = int(Config.get('config', 'y1'))
x0_real         = int(Config.get('config', 'x0_real'))
y0_real         = int(Config.get('config', 'y0_real'))
x1_real         = int(Config.get('config', 'x1_real'))
y1_real         = int(Config.get('config', 'y1_real'))
scr             = Config.get('config', 'scr')
delta1          = int(Config.get('config', 'delta1'))
coord_sub       = Config.get('config', 'coord_sub')
a               = Config.get('config', 'a').split(',')
b               = Config.get('config', 'b').split(',')

fontpath        = 'FreeSans.ttf'

#computed
bb             = [[x0, x1],[y1, y0]]                     # REQUESTED bounding box in Lambert 72 coordinates
cc             = [[x0_real, x1_real],[y1_real, y0_real]] # real bounding box (may be different, espacially in y)

out_fname    = 'test' + str(dpi) + '.' + fmt
now          = datetime.datetime.now()

sx_frame     = math.floor(size_real_x_mm / 25.4 * dpi) #pixels
sy_frame     = math.floor(size_real_y_mm / 25.4 * dpi) #pixels

sx           = sx_frame - dx_frame
sy           = sy_frame - dy_frame

#get the image
wms          = WebMapService('http://maps.omniscale.net/v2/'+omniscale_api+'/style.default/dpi.'+str(dpi)+'/map')
img          = wms.getmap(   layers=['osm'],styles=None,srs=scr,bbox=(bb[0][0], bb[1][0], bb[0][1], bb[1][1]),size=(sx, sy),format='image/'+fmt,transparent=True);out = open(out_fname, 'wb'); out.write(img.read()); out.close()

#modify the image (add a grid & a cartouche)
resultImage  = Image.open(out_fname)
cartouche    = Image.open('cartouche.png')
cx           = 2701
cy           = 1113

newImage    = Image.new("RGB", (sx_frame,sy_frame), "white")
newImage.paste(resultImage, (dx_frame,dy_frame,dx_frame+sx,dy_frame+sy))
newImage.paste(cartouche,   (dx_frame,sy_frame-math.floor(dy_frame/2)-cy,dx_frame+cx,sy_frame-math.floor(dy_frame/2)))

draw   = ImageDraw.Draw(newImage)

fnt    = ImageFont.truetype(fontpath, 140)
fnt2   = ImageFont.truetype(fontpath, 30)

dx     = cc[0][1]-cc[0][0]
dy     = cc[1][1]-cc[1][0]


delta2 = delta1/2

nx     = math.floor(dx/delta1);     etax = sx/dx*delta1
ny     = math.floor(dy/delta1);     etay = sy/dy*delta1

nx2    = math.floor(dx/delta2);     etax2 = sx/dx*delta2
ny2    = math.floor(dy/delta2);     etay2 = sy/dy*delta2

for m in range (0, nx+1):
        draw.line((dx_frame+m*etax, dy_frame/2, dx_frame+m*etax, dy_frame+resultImage.size[1]), fill='#000000', width=4)
for m in range (0, ny+1):
        draw.line((dx_frame/2, dy_frame+m*etay, dx_frame+resultImage.size[0], dy_frame+m*etay), fill='#000000', width=4)

for m in range (0, nx2):
        draw.line((dx_frame+m*etax2, dy_frame, dx_frame+m*etax2, dy_frame+resultImage.size[1]), fill='#000000', width=1)
for m in range (0, ny2):
        draw.line((dx_frame, dy_frame+m*etay2, dx_frame+resultImage.size[0], dy_frame+m*etay2), fill='#000000', width=1)
        
for m in range (0, nx):
        w, h = draw.textsize(a[m], font=fnt)
        draw.text((m*etax+etax/2-w/2+dx_frame,30), a[m], fill='#000000', font=fnt)

for m in range (0, ny+1):
        w, h = draw.textsize(str(m), font=fnt)
        draw.text((30,m*sy/dy*delta1+etay/2-h/2+dy_frame), str(m+1), fill='#000000', font=fnt)

if coord_sub == True:
        for m in range (0, nx):
                for n in range (0, ny+1):
                        draw.text((m*sx/dx*delta1+.1*etax,n*sy/dy*delta1+.1*etay), a[m]+' ' + str(n), fill='#000000', font=fnt2)        
 
del draw

outputFileName     = "map%s-%02d%02d%02d-%02d%02d.%s" % (str(dpi), now.year % 100, now.month, now.day, now.hour, now.minute, fmt)
outputFileName_pdf = "map%s-%02d%02d%02d-%02d%02d.pdf" % (str(dpi), now.year % 100, now.month, now.day, now.hour, now.minute)

newImage.save(outputFileName)

os.system("%s %s %s" % (im_path, outputFileName, outputFileName_pdf))

# pour un secteur de 32x32 km,
# l'idéal, pour afficher les rues, est une carte murale de 2000 x 2000 mm, en 100 dpi en png

# en sortie :

# pour créer PDF
#   OPTION 1. using ImageMagick (notamment pour tirer un pdf en A0 à partir d'un png en A0)
#              
#             C:\Program Files\ImageMagick-7.0.2-Q16\convert.exe mapWMS-160917-1159.png mapWMS-160917-1159_IM.pdf
#   OPTION B. à partir de paint > primo pdf + dimensions "personnalisée", puis preflight

# pour créer un EPS : à partir de PIL
# outputFileName = "map%s-%02d%02d%02d-%02d%02d.eps" % (dpi, now.year % 100, now.month, now.day, now.hour, now.minute)
# newImage.save(outputFileName)
# résolution pas géniale

# bad alternatives
# Adobe Acrobat : bad resolution, PDFCreator : bad size
# exporteurs intégrés de PIL (vers PDF, ou EPS puis Acrobat) : compriment en jpeg
# zoomlevel dans Gimp, correspondant à A0 : 33 %

# jpeg : not clean enough for printing
