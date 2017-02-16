# Run the current pattern for a given number of steps (using current
# step size) and create a plot of population vs time in separate layer.
# Author: Andrew Trevorrow (andrew@trevorrow.com), May 2007.

import golly as g
from glife import getminbox, rect, rccw
from glife.text import make_text
from time import time
import math

# --------------------------------------------------------------------

# size of plot
# xlen = 500        # length of x axis
ylen = 500        # length of y axis

# --------------------------------------------------------------------

# draw a line of cells from x1,y1 to x2,y2 using Bresenham's algorithm

def draw_line(x1, y1, x2, y2):
    g.setcell(x1, y1, 1)
    if x1 == x2 and y1 == y2: return

    dx = x2 - x1
    ax = abs(dx) * 2
    sx = 1
    if dx < 0: sx = -1
    dy = y2 - y1
    ay = abs(dy) * 2
    sy = 1
    if dy < 0: sy = -1

    if ax > ay:
        d = ay - (ax / 2)
        while x1 != x2:
            g.setcell(x1, y1, 1)
            if d >= 0:
                y1 += sy
                d -= ax
            x1 += sx
            d += ay
    else:
        d = ax - (ay / 2)
        while y1 != y2:
            g.setcell(x1, y1, 1)
            if d >= 0:
                x1 += sx
                d -= ay
            y1 += sy
            d += ax

    g.setcell(x2, y2, 1)

# --------------------------------------------------------------------

# fit pattern in viewport if not empty and not completely visible
def fit_if_not_visible():
    try:
        r = rect(g.getrect())
        if (not r.empty) and (not r.visible()): g.fit()
    except:
        # getrect failed because pattern is too big
        g.fit()

# --------------------------------------------------------------------

if g.empty(): g.exit("There is no pattern.")

# check that a layer is available for population plot
layername = "population plot"
poplayer = -1
for i in xrange(g.numlayers()):
    if g.getname(i) == layername:
        poplayer = i
        break
if poplayer == -1 and g.numlayers() == g.maxlayers():
    g.exit("You need to delete a layer.")

# prompt user for number of steps
numsteps=500
s = g.getstring("Enter the number of steps:",
                str(numsteps), "Population plotter")
if len(s) > 0: numsteps = int(s)
if numsteps <= 0: g.exit()

def boxdm(orientation):
	if not g.empty():
		shrink()
		return g.getselrect()[orientation]
	else:
		return 0
def area():
	if not g.empty():
		shrink()
		return g.getselrect()[2]*g.getselrect()[3]
	else:
		return 0
	
def density():
	if not g.empty():
		shrink()
		return d
	else:
		return 0

def shrink():
	global d
	if g.empty():
		return
	g.select(g.getrect())
	d=int(10000*float(g.getpop())/(int(g.getselrect()[2])*int(g.getselrect()[3])))
	while d<100:
		bbox=g.getselrect()
		bbox[0]=bbox[0]+1
		bbox[1]=bbox[1]+1
		bbox[2]=bbox[2]-2
		bbox[3]=bbox[3]-2
		g.select(bbox)
		g.shrink()
		d=int(10000*float(g.getpop())/(int(g.getselrect()[2])*int(g.getselrect()[3])))
# generate pattern for given number of steps


def popcount():
	clist=g.getcells(g.getrect())
	return sum(clist[2::3].count(x) for x in live_cells)
vars=g.getstring("yVar/yxVar, \n pop=population,\n gen=generation,\n boxy=width of bounding box,\n boxx=height of bounding box,\n density=population/area of bindingbox ,\n area=area of bounding box","pop/gen")

dict_lc={'BDRainbow':[2,4],'BGRainbowR2':[2,4]}
try:
    live_cells=dict_lc[g.getrule().split(':')[0]]
except:
    live_cells=range(1,g.numstates  ())        
dict_f = {'popc':popcount,'pop': g.getpop, 'gen': g.getgen,'boxx':lambda:boxdm(2) ,'boxy': lambda: boxdm(3),'area':area,'density':density, \
		'logpop':lambda:float(math.log(float(g.getpop()))/math.log(2)),'popi':lambda:int(1000000000/float(g.getpop())), 'areai':lambda:int(1000000000/float(int(boxdm(2))*int(boxdm(3))))}
dict_t={'popc':'Population','pop':'Population','gen':'Generation','boxx':'Box width','boxy':'Box height','area':'Box area','density':'Cell density (0.001)',\
		'logpop':'log(pop)','popi':'inverse of pop','areai':'inverse of area'}
yfunc=dict_f[vars.split("/")[0]]
xfunc=dict_f[vars.split("/")[1]]
ytitle=dict_t[vars.split("/")[0]]
xtitle=dict_t[vars.split("/")[1]]



poplist = [ int(yfunc()) ]
genlist = [ int(xfunc()) ]
xlimlist= [int(g.getrect()[1])]
oldsecs = time()
for i in xrange(numsteps):
    g.step()
    poplist.append( float(yfunc()) )
    genlist.append( float(xfunc()) )
    newsecs = time()
    if newsecs - oldsecs >= 1.0:     # show pattern every second
        oldsecs = newsecs
        fit_if_not_visible()
        g.update()
        g.show("Step %i of %i" % (i+1, numsteps))
	
	event=g.getevent()
	if event.startswith("key"):
		evt, ch, mods = event.split()
		if ch == "q":
			out=1
			numsteps=i
			break

fit_if_not_visible()

# poplist.sort(key=dict(zip(poplist, genlist)).get)

# save some info before we switch layers
stepsize = "%i^%i" % (g.getbase(), g.getstep())
pattname = g.getname()

# create population plot in separate layer
g.setoption("stacklayers", 0)
g.setoption("tilelayers", 0)
g.setoption("showlayerbar", 1)
if poplayer == -1:
    poplayer = g.addlayer()
else:
    g.setlayer(poplayer)
g.new(layername)
g.setrule('Life')
# use same rule but without any suffix (we don't want a bounded grid)
# g.setrule(g.getrule().split(":")[0])



deadr, deadg, deadb = g.getcolor("deadcells")
if (deadr + deadg + deadb) / 3 > 128:
    # use black if light background
    g.setcolors([1,0,0,0])
else:
    # use white if dark background
    g.setcolors([1,255,255,255])

minpop = min(poplist)
maxpop = max(poplist)
if minpop == maxpop:
    # avoid division by zero
    minpop -= 1

popscale=g.getstring('what scale to use for pop/y?','%i'%int((maxpop-minpop)/100))
popscale=float(popscale)
mingen = min(genlist)
maxgen = max(genlist)	
xlen=int(maxgen-mingen)
ylen=int(min(xlen,(maxpop-minpop)/popscale))
# popscale = float(maxpop - minpop) / float(ylen)




genscale=1
# genscale = float(maxgen - mingen) / float(xlen)

# draw axes with origin at 0,0
draw_line(0, 0, xlen, 0)
draw_line(0, 0, 0, -ylen)

# add annotation using mono-spaced ASCII font
t = make_text(pattname.upper(), "mono")
bbox = getminbox(t)
t.put((xlen - bbox.wd) / 2, -ylen - 10 - bbox.ht)

t = make_text(ytitle, "mono")
bbox = getminbox(t)
t.put(-10 - bbox.ht, -(ylen - bbox.wd) / 2, rccw)

t = make_text(str(minpop), "mono")
bbox = getminbox(t)
t.put(-bbox.wd - 10, -bbox.ht / 2)

t = make_text(str(maxpop), "mono")
bbox = getminbox(t)
t.put(-bbox.wd - 10, -ylen - bbox.ht / 2)

t = make_text("%s (step=%s)" % (xtitle,stepsize), "mono")
bbox = getminbox(t)
t.put((xlen - bbox.wd) / 2, 10)

t = make_text(str(mingen), "mono")
bbox = getminbox(t)
t.put(-bbox.wd / 2, 10)

t = make_text(str(maxgen), "mono")
bbox = getminbox(t)
t.put(xlen - bbox.wd / 2, 10)

# display result at scale 1:1
g.fit()
g.setmag(0)
g.show("")

# plot the data (do last because it could take a while if numsteps is huge)
x = int(float(genlist[0] - mingen) / genscale)
y = int(float(poplist[0] - minpop) / popscale)
oldsecs = time()
for i in xrange(numsteps):
    newx = int(float(genlist[i+1] - mingen) / genscale)
    newy = int(float(poplist[i+1] - minpop) / popscale)
    draw_line(x, -y, newx, -newy)
    x = newx
    y = newy
    newsecs = time()
    if newsecs - oldsecs >= 1.0:     # update plot every second
        oldsecs = newsecs
        g.update()
