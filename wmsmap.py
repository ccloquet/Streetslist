 ####################################################################### 
#                                                                       #
# Create a high definition large printable map                          #
# (eg : 2000 x 2000, 300 dpi) with a grid                               #
# based on WMS requests to Omniscale                                    #
#                                                                       #
# Author:  Christophe Cloquet, Poppy, Brussels (2016)                   #
#          christophe@my-poppy.eu                                       #
#          www.my-poppy.eu                                              #
#                                                                       #
# Licence: MIT                                                          #
#                                                                       #
 ####################################################################### 

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
white_border_x_mm       = int(Config.get('config', 'white_border_x_mm'))
white_border_y_mm       = int(Config.get('config', 'white_border_y_mm'))
margin_x_charac_mm      = int(Config.get('config', 'margin_x_charac_mm'))
margin_y_charac_mm      = int(Config.get('config', 'margin_y_charac_mm'))

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

npartsw                 = int(Config.get('config', 'npartsw'))
npartsh                 = int(Config.get('config', 'npartsh'))

border_half_width       = int(Config.get('config', 'border_half_width'))
enforce_overlap         = Config.get('config', 'enforce_overlap'); 
add_grid                = Config.get('config', 'add_grid'); 
add_cartouche           = Config.get('config', 'add_cartouche');
fontpath                = Config.get('config', 'fontpath'); 

if coord_sub == 'False':
        coord_sub = False
else:
        coord_sub = True
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
        coeff_bcz_omniscale_bug = 1.11 # 2016.09.01: bug in omniscale that does not display the right level of detail. Support has been notified. Will be solved in the next release of Omniscale
else:
        coeff_bcz_omniscale_bug = 1
        
cc              = [[x0_real, x1_real],[y1_real, y0_real]] # REAL bounding box (may be different, espacially in y)
now             = datetime.datetime.now()

dx_frame        = math.floor(border_frame_x_mm / 25.4 * dpi)
dy_frame        = math.floor(border_frame_y_mm / 25.4 * dpi)

margin_x_charac = math.floor(margin_x_charac_mm / 25.4 * dpi)
margin_y_charac = math.floor(margin_y_charac_mm / 25.4 * dpi)

wb_x            = math.floor(white_border_x_mm / 25.4 * dpi)
wb_y            = math.floor(white_border_y_mm / 25.4 * dpi)

sx_request      = math.floor( (size_real_x_mm - border_frame_x_mm - 2.0 * white_border_x_mm) / nsub / 25.4 * dpi * coeff_bcz_omniscale_bug) #pixels
sy_request      = math.floor( (size_real_y_mm - border_frame_y_mm - 2.0 * white_border_y_mm) / nsub / 25.4 * dpi * coeff_bcz_omniscale_bug) #pixels

dx_frame = math.floor(dx_frame*coeff_bcz_omniscale_bug)
dy_frame = math.floor(dy_frame*coeff_bcz_omniscale_bug)
wb_x     = math.floor(wb_x*coeff_bcz_omniscale_bug)
wb_y     = math.floor(wb_y*coeff_bcz_omniscale_bug)

sx_frame        = math.floor( nsub * sx_request+ (dx_frame+2*wb_x)  )
sy_frame        = math.floor( nsub * sy_request+ (dy_frame+2*wb_y)  )

# the following computation so that the cut of the plate is correct at the pixel level     
if sx_frame%npartsw>0:
        DX              = (npartsw-sx_frame%npartsw); dx_frame += DX; sx_frame += DX

if sy_frame%npartsh>0:
        DY              = (npartsh-sy_frame%npartsh); dy_frame += DY; sy_frame += DY

sx              = sx_frame - dx_frame - 2*wb_x
sy              = sy_frame - dy_frame - 2*wb_y

deltax          = (x1-x0)/nsub
deltay          = (y0-y1)/nsub

# (comment steps 1 and 2 (up to ********************* ) to use an already downloaded map)

get the image, possibly by parts

print('1. getting the images', dpi, sx_frame, sy_frame)

wms             = WebMapService('http://maps.omniscale.net/v2/'+omniscale_api+'/style.default/dpi.'+str(dpi)+'/map')

for i in range (0, nsub):
        for j in range (0, nsub):
                print('   ', i, j, x0+i*deltax, y1+j*deltay, x0+(i+1)*deltax, y1+(j+1)*deltay)
                out_fname    = 'test' + str(dpi) + '_' + str(i) + str(j) + '.' + fmt
                img          = wms.getmap(   layers=['osm'],styles=None,srs=scr,bbox=(x0+i*deltax, y1+j*deltay, x0+(i+1)*deltax, y1+(j+1)*deltay),size=(sx_request, sy_request),format='image/'+fmt,transparent=True);out = open(out_fname, 'wb'); out.write(img.read()); out.close()

# get overlap images between the images, to mask the differences at the joins
if (nsub > 1) & (enforce_overlap):
        print('2. getting the overlap images')
        for i in range (1, nsub):
                for j in range (0, nsub):
                        print('   ', i, j, x0+i*deltax, y1+j*deltay, x0+(i+1)*deltax, y1+(j+1)*deltay)
                        i_prime      = i-.5
                        out_fname    = 'test' + str(dpi) + '_joinx_' + str(i) + str(j) + '.' + fmt
                        img          = wms.getmap(   layers=['osm'],styles=None,srs=scr,bbox=(x0+i_prime*deltax, y1+j*deltay, x0+(i_prime+1)*deltax, y1+(j+1)*deltay),size=(sx_request, sy_request),format='image/'+fmt,transparent=True);out = open(out_fname, 'wb');
                        out.write(img.read());
                        out.close()
                        
        for i in range (0, nsub):
                for j in range (1, nsub):
                        print('   ', i, j, x0+i*deltax, y1+j*deltay, x0+(i+1)*deltax, y1+(j+1)*deltay)
                        j_prime = j-.5
                        out_fname    = 'test' + str(dpi) + '_joiny_' + str(i) + str(j) + '.' + fmt
                        img          = wms.getmap(   layers=['osm'],styles=None,srs=scr,bbox=(x0+i*deltax, y1+j_prime*deltay, x0+(i+1)*deltax, y1+(j_prime+1)*deltay),size=(sx_request, sy_request),format='image/'+fmt,transparent=True);out = open(out_fname, 'wb');
                        out.write(img.read());
                        out.close()

# ********************* end for comment


#merge the images, add a grid & a cartouche
print('3. merging the images')
newImage    = Image.new("RGB", (sx_frame,sy_frame), "white")

for i in range (0, nsub):
        for j in range (0, nsub):
                out_fname    = 'test' + str(dpi) + '_' + str(i) + str(nsub-1-j) + '.' + fmt
                resultImage  = Image.open(out_fname)
                newImage.paste(resultImage, (dx_frame+wb_x+i*sx_request,dy_frame+wb_y+j*sy_request,dx_frame+wb_x+(i+1)*sx_request,dy_frame+wb_y+(j+1)*sy_request))

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
                        newImage.paste(resultImage, (dx_frame+wb_x+i*sx_request-border_half_width,dy_frame+wb_y+j*sy_request,dx_frame+wb_x+i*sx_request-border_half_width+w,dy_frame+wb_y+(j+1)*sy_request))

        for i in range (0, nsub):
                for j in range (1, nsub):
                       
                        out_fname   = 'test' + str(dpi) + '_joiny_' + str(i) + str(j) + '.' + fmt
                        resultImage = Image.open(out_fname)
                        w, h        = resultImage.size
                        to_crop     = math.floor(h/2-border_half_width)
                        resultImage = resultImage.crop((0, to_crop, w, h-to_crop))
                        w, h        = resultImage.size
                        newImage.paste(resultImage, (dx_frame+wb_x+i*sx_request,dy_frame+wb_y+j*sy_request-border_half_width,dx_frame+wb_x+(i+1)*sx_request,dy_frame+wb_y+j*sy_request-border_half_width+h))

# add the grid

print('4. adding the grid')
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
                draw.line((wb_x+dx_frame+m*etax, wb_y+dy_frame/2, wb_x+dx_frame+m*etax, newImage.size[1]-wb_y), fill='#000000', width=4)
        for m in range (0, ny+1):
                draw.line((wb_x+dx_frame/2, wb_y+dy_frame+m*etay, newImage.size[0]-wb_x, wb_y+dy_frame+m*etay), fill='#000000', width=4)

        for m in range (0, nx2):
                draw.line((wb_x+dx_frame+m*etax2, wb_y+dy_frame, wb_x+dx_frame+m*etax2, newImage.size[1]-wb_y), fill='#000000', width=1)
        for m in range (0, ny2):
                draw.line((wb_x+dx_frame, wb_y+dy_frame+m*etay2, newImage.size[0]-wb_x, wb_y+dy_frame+m*etay2), fill='#000000', width=1)
                
        for m in range (0, nx):
                w, h = draw.textsize(a[m], font=fnt)
                draw.text((wb_x+m*etax+etax/2-w/2+dx_frame,wb_y+margin_y_charac), a[m], fill='#000000', font=fnt)

        for m in range (0, ny):
                w, h = draw.textsize(str(m), font=fnt)
                draw.text((wb_x+margin_y_charac,wb_y+m*sy/dy*delta1+etay/2-h/2+dy_frame), str(m+1), fill='#000000', font=fnt)

        m = ny; draw.line((wb_x+dx_frame/2, wb_y+dy_frame+m*etay+2+15, newImage.size[0]-wb_x, wb_y+dy_frame+m*etay+2+15), fill='#ffffff', width=30)
        m = nx; draw.line((wb_x+dx_frame+m*etax+2+15, wb_y+dy_frame/2, wb_x+dx_frame+m*etax+2+15, newImage.size[1]-wb_y), fill='#ffffff', width=30)
        
        if coord_sub == True:
                for m in range (0, nx):
                        for n in range (0, ny+1):
                                draw.text((wb_x+dx_frame+m*sx/dx*delta1+.1*etax,wb_y+dy_frame+n*sy/dy*delta1+.1*etay), a[m]+' ' + str(n+1), fill='#000000', font=fnt2)        
        del draw

# add the cartouche
if add_cartouche:
        print('5. adding the cartouche')
        
        cartouche    = Image.open('cartouche.png')
        s            = .4945/140 # scale of the cartouche. Modify this to enlarge or reduce it
        c            = 'black'   # color of the border

#        cartouche    = Image.open('cartouche2.png')
#        s            = 0.4802535355/140
#        c            = 'white'

        w,h          = cartouche.size
        cx           = math.floor(coeff_bcz_omniscale_bug*w*dpi*s)
        cy           = math.floor(coeff_bcz_omniscale_bug*h*dpi*s)
        cartouche    = cartouche.resize((cx,cy), Image.ANTIALIAS)
        Add_Padd     = 10
        new_im       = Image.new('RGB', (cx+2*Add_Padd,cy+2*Add_Padd), c) 
        new_im.paste(cartouche, (Add_Padd,Add_Padd))

        # cartouche on the map
        newImage.paste(new_im,   (wb_x+math.floor(dx_frame*1.15),sy_frame-math.floor(dy_frame/4)-cy-2*Add_Padd-wb_y,wb_x+math.floor(dx_frame*1.15+cx+2*Add_Padd),sy_frame-math.floor(dy_frame/4)-wb_y))

        # cartouche outside of the map
#        newImage.paste(new_im,   (sx_frame-wb_x-math.floor(cx+2*Add_Padd),sy_frame-math.floor(dy_frame/4)-cy-2*Add_Padd,sx_frame-wb_x,sy_frame-math.floor(dy_frame/4)))
        
outputFileName_base = "map%s-%02d%02d%02d-%02d%02d" % (str(dpi), now.year % 100, now.month, now.day, now.hour, now.minute)
outputFileName      = "%s.%s" % (outputFileName_base, fmt)
outputFileName_pdf  = "%s.pdf" % (outputFileName_base)
outputFileName_jpg  = "%s.jpg" % (outputFileName_base)

newImage.save(outputFileName)

print('6. converting')
os.system("%s %s %s" % (im_path, outputFileName, outputFileName_pdf))
newImage.save(outputFileName_jpg, quality=95)

w, h    = newImage.size

print('7. splitting')
for i in range(0,npartsw):
        for j in range(0,npartsh):
                print('    ' + str(i) + str(j))
                outputFileNameij = "%s_%02d%02d.%s" % (outputFileName_base, i, j, fmt)
                outputFileNameij_tif = "%s_%02d%02d.tif" % (outputFileName_base, i, j)
                outputFileNameij_pdf = "%s_%02d%02d.pdf" % (outputFileName_base, i, j)
                outputFileNameij_jpg = "%s_%02d%02d.jpg" % (outputFileName_base, i, j)
                
                newImagecrop = newImage.crop((math.floor(w/npartsw*i), math.floor(h/npartsh*j), math.floor(w/npartsw*(i+1)), math.floor(h/npartsh*(j+1))))

                newImagecrop.save(outputFileNameij)
                newImagecrop.save(outputFileNameij_tif) #no compression
                newImagecrop.save(outputFileNameij_jpg, quality=95)  
                os.system("%s %s %s" % (im_path, outputFileNameij, outputFileNameij_pdf))

A4_nx = sx_frame/size_real_x_mm*210
A4_ny = sy_frame/size_real_y_mm*297

print ('A4_extract', A4_nx, A4_ny) # number of pixels in x & y if you want to extract smth to be printed on an A4
