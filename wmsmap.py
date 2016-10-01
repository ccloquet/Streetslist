# *****************************************************************************************
# create a high definition large printable map (eg : 2000 x 2000, 300 dpi) with a grid    *
# based on WMS requests to Omniscale                                                      *
# *****************************************************************************************
#
# Author:  C. Cloquet, Poppy, 2016
# Licence: MIT

import  dateutil
from    owslib.wms import WebMapService
from    PIL import Image, ImageDraw, ImageFont
import  io, datetime, time, re, random, math, os
import  configparser

Config = configparser.ConfigParser()
Config.read("config.poppy")

im_path                 = Config.get('config', 'im_path')
omniscale_api           = Config.get('config', 'omniscale_api')
size_real_x_mm          = int(Config.get('config', 'size_real_x_mm'))
size_real_y_mm          = int(Config.get('config', 'size_real_y_mm'))
border_frame_x_mm       = int(Config.get('config', 'border_frame_x_mm'))
border_frame_y_mm       = int(Config.get('config', 'border_frame_y_mm'))
dpi                     = int(Config.get('config', 'dpi'))
fmt                     = Config.get('config', 'fmt')
x0                      = int(Config.get('config', 'x0'))
x1                      = int(Config.get('config', 'x1'))
y0                      = int(Config.get('config', 'y0'))
y1                      = int(Config.get('config', 'y1'))
x0_real                 = int(Config.get('config', 'x0_real'))
y0_real                 = int(Config.get('config', 'y0_real'))
x1_real                 = int(Config.get('config', 'x1_real'))
y1_real                 = int(Config.get('config', 'y1_real'))
scr                     = Config.get('config', 'scr')
nsub                    = int(Config.get('config', 'nsub'))
delta1                  = int(Config.get('config', 'delta1'))
coord_sub               = Config.get('config', 'coord_sub'); 
a                       = Config.get('config', 'a').split(',')
b                       = Config.get('config', 'b').split(',')

border_half_width       = int(Config.get('config', 'border_half_width'))
enforce_overlap         = Config.get('config', 'enforce_overlap'); 
add_grid                = Config.get('config', 'add_grid'); 
add_cartouche           = Config.get('config', 'add_cartouche');
fontpath                = Config.get('config', 'fontpath'); 

if coord_sub == 'False': coord_sub = False
if enforce_overlap == 'False':
        enforce_overlap = False
else:
        enforce_overlap = True
if add_grid == 'False':
        add_grid = False;
else:
        add_grid = True
if add_cartouche == 'False':
        add_cartouche = False;
else:
        add_cartouche = True

#computed
if dpi > 100:
        coeff_bcz_omniscale_bug = 1.11 # 2016.09.01: bug in omniscale that does not display the right level of detail. Support has been notified. Will be solved in the next release
else:
        coeff_bcz_omniscale_bug = 1
        
cc             = [[x0_real, x1_real],[y1_real, y0_real]] # REAL bounding box (may be different, espacially in y)
now            = datetime.datetime.now()

dx_frame       = math.floor(border_frame_x_mm / 25.4 * dpi)
dy_frame       = math.floor(border_frame_y_mm / 25.4 * dpi)

sx_request     = math.floor( (size_real_x_mm - border_frame_x_mm) / nsub / 25.4 * dpi * coeff_bcz_omniscale_bug) #pixels
sy_request     = math.floor( (size_real_y_mm - border_frame_y_mm) / nsub / 25.4 * dpi * coeff_bcz_omniscale_bug) #pixels

sx_frame       = nsub * sx_request+dx_frame
sy_frame       = nsub * sy_request+dx_frame
     
sx              = sx_frame - dx_frame
sy              = sy_frame - dy_frame

deltax          = (x1-x0)/nsub
deltay          = (y0-y1)/nsub
wms             = WebMapService('http://maps.omniscale.net/v2/'+omniscale_api+'/style.default/dpi.'+str(dpi)+'/map')

#get the image, possibly by parts
print('1. get the image', dpi, sx_frame, sy_frame)

for i in range (0, nsub):
        for j in range (0, nsub):
                print(i, j, x0+i*deltax, y1+j*deltay, x0+(i+1)*deltax, y1+(j+1)*deltay)
                out_fname    = 'test' + str(dpi) + '_' + str(i) + str(j) + '.' + fmt
                img          = wms.getmap(   layers=['osm'],styles=None,srs=scr,bbox=(x0+i*deltax, y1+j*deltay, x0+(i+1)*deltax, y1+(j+1)*deltay),size=(sx_request, sy_request),format='image/'+fmt,transparent=True);out = open(out_fname, 'wb'); out.write(img.read()); out.close()


# get overlap images between the images, to mask the differences at the joins
if (nsub > 1) & (enforce_overlap):
        print('2. get the overlap images')
        for i in range (1, nsub):
                for j in range (0, nsub):
                        print(i, j, x0+i*deltax, y1+j*deltay, x0+(i+1)*deltax, y1+(j+1)*deltay)
                        i_prime      = i-.5
                        out_fname    = 'test' + str(dpi) + '_joinx_' + str(i) + str(j) + '.' + fmt
                        img          = wms.getmap(   layers=['osm'],styles=None,srs=scr,bbox=(x0+i_prime*deltax, y1+j*deltay, x0+(i_prime+1)*deltax, y1+(j+1)*deltay),size=(sx_request, sy_request),format='image/'+fmt,transparent=True);out = open(out_fname, 'wb');
                        out.write(img.read());
                        out.close()
                        
        for i in range (0, nsub):
                for j in range (1, nsub):
                        print(i, j, x0+i*deltax, y1+j*deltay, x0+(i+1)*deltax, y1+(j+1)*deltay)
                        j_prime = j-.5
                        out_fname    = 'test' + str(dpi) + '_joiny_' + str(i) + str(j) + '.' + fmt
                        img          = wms.getmap(   layers=['osm'],styles=None,srs=scr,bbox=(x0+i*deltax, y1+j_prime*deltay, x0+(i+1)*deltax, y1+(j_prime+1)*deltay),size=(sx_request, sy_request),format='image/'+fmt,transparent=True);out = open(out_fname, 'wb');
                        out.write(img.read());
                        out.close()

#merge the images, add a grid & a cartouche
print('3. merge the images')
newImage    = Image.new("RGB", (sx_frame,sy_frame), "white")

for i in range (0, nsub):
        for j in range (0, nsub):
                out_fname    = 'test' + str(dpi) + '_' + str(i) + str(nsub-1-j) + '.' + fmt
                resultImage  = Image.open(out_fname)
                newImage.paste(resultImage, (dx_frame+i*sx_request,dy_frame+j*sx_request,dx_frame+(i+1)*sx_request,dy_frame+(j+1)*sy_request))

# add the overlap (get the images, crop them, pathe them in the large image)
border_half_width *= dpi
if (nsub > 1) & (enforce_overlap):
        for i in range (1, nsub):
                for j in range (0, nsub):
                       
                        out_fname   = 'test' + str(dpi) + '_joinx_' + str(i) + str(nsub-1-j) + '.' + fmt
                        resultImage = Image.open(out_fname)
                        w, h        = resultImage.size
                        to_crop     = math.floor(w/2-border_half_width)
                        resultImage = resultImage.crop((to_crop, 0, w-to_crop, h))
                        w, h        = resultImage.size
                        newImage.paste(resultImage, (dx_frame+i*sx_request-border_half_width,dy_frame+j*sx_request,dx_frame+i*sx_request-border_half_width+w,dy_frame+(j+1)*sy_request))

        for i in range (0, nsub):
                for j in range (1, nsub):
                       
                        out_fname   = 'test' + str(dpi) + '_joiny_' + str(i) + str(j) + '.' + fmt
                        resultImage = Image.open(out_fname)
                        w, h        = resultImage.size
                        to_crop     = math.floor(h/2-border_half_width)
                        resultImage = resultImage.crop((0, to_crop, w, h-to_crop))
                        w, h        = resultImage.size
                        newImage.paste(resultImage, (dx_frame+i*sx_request,dy_frame+j*sx_request-border_half_width,dx_frame+(i+1)*sx_request,dy_frame+j*sy_request-border_half_width+h))

# add the grid
print('4. add the grid')
if add_grid:
        draw   = ImageDraw.Draw(newImage)

        fnt    = ImageFont.truetype(fontpath, math.floor(30/25.4*dpi))  # 30 mm
        fnt2   = ImageFont.truetype(fontpath, math.floor(6.5/25.4*dpi)) # 6.5 mm

        dx     = cc[0][1]-cc[0][0]
        dy     = cc[1][1]-cc[1][0]

        delta2 = delta1/2

        nx     = math.floor(dx/delta1);     etax = sx/dx*delta1
        ny     = math.floor(dy/delta1);     etay = sy/dy*delta1

        nx2    = math.floor(dx/delta2);     etax2 = sx/dx*delta2
        ny2    = math.floor(dy/delta2);     etay2 = sy/dy*delta2

        for m in range (0, nx+1):
                draw.line((dx_frame+m*etax, dy_frame/2, dx_frame+m*etax, newImage.size[1]), fill='#000000', width=4)
        for m in range (0, ny+1):
                draw.line((dx_frame/2, dy_frame+m*etay, newImage.size[0], dy_frame+m*etay), fill='#000000', width=4)

        for m in range (0, nx2):
                draw.line((dx_frame+m*etax2, dy_frame, dx_frame+m*etax2, newImage.size[1]), fill='#000000', width=1)
        for m in range (0, ny2):
                draw.line((dx_frame, dy_frame+m*etay2, newImage.size[0], dy_frame+m*etay2), fill='#000000', width=1)
                
        for m in range (0, nx):
                w, h = draw.textsize(a[m], font=fnt)
                draw.text((m*etax+etax/2-w/2+dx_frame,50), a[m], fill='#000000', font=fnt)

        for m in range (0, ny+1):
                w, h = draw.textsize(str(m), font=fnt)
                draw.text((50,m*sy/dy*delta1+etay/2-h/2+dy_frame), str(m+1), fill='#000000', font=fnt)

        if coord_sub == True:
                for m in range (0, nx):
                        for n in range (0, ny+1):
                                draw.text((m*sx/dx*delta1+.1*etax,n*sy/dy*delta1+.1*etay), a[m]+' ' + str(n), fill='#000000', font=fnt2)        
        del draw

# add the cartouche
if add_cartouche:
        print('5. add the cartouche')
        cartouche    = Image.open('cartouche.png')
        cx           = math.floor(coeff_bcz_omniscale_bug*2262/2*dpi/140)
        cy           = math.floor(coeff_bcz_omniscale_bug*1034/2*dpi/140)
        cartouche    = cartouche.resize((cx,cy), Image.ANTIALIAS)
        Add_Padd     = 10
        new_im       = Image.new('RGB', (cx+2*Add_Padd,cy+2*Add_Padd)) # black
        new_im.paste(cartouche, (Add_Padd,Add_Padd))
        newImage.paste(new_im,   (math.floor(dx_frame*1.15),sy_frame-math.floor(dy_frame/4)-cy-2*Add_Padd,math.floor(dx_frame*1.15+cx+2*Add_Padd),sy_frame-math.floor(dy_frame/4)))

outputFileName     = "map%s-%02d%02d%02d-%02d%02d.%s" % (str(dpi), now.year % 100, now.month, now.day, now.hour, now.minute, fmt)
outputFileName_pdf = "map%s-%02d%02d%02d-%02d%02d.pdf" % (str(dpi), now.year % 100, now.month, now.day, now.hour, now.minute)

newImage.save(outputFileName)

print('6. converts in pdf')
os.system("%s %s %s" % (im_path, outputFileName, outputFileName_pdf))

A4_nx = sx_frame/size_real_x_mm*210
A4_ny = sy_frame/size_real_y_mm*297

print ('A4_extract', A4_nx, A4_ny) # number of pixels in x & y if you want to extract smth to be printed on an A4
