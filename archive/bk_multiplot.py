# Run the current pattern for a given number of steps (using current
# step size) and create a plot of population vs time in separate layer.
# Author: Andrew Trevorrow (andrew@trevorrow.com), May 2007.

import golly as g
from time import time
import math
from collections import Counter
from glife import *
from glife.text import make_text
from time import time
import random
import math as m
import csv
import os

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
# --------------------------------------------------------------------
def show_spaceship_speed(period, deltax, deltay):
    # we found a moving oscillator
    if period == 1:
        g.show("Spaceship detected (speed = c)")
    elif (deltax == deltay) or (deltax == 0) or (deltay == 0):
        speed = ""
        if (deltax == 0) or (deltay == 0):
            # orthogonal spaceship
            if (deltax > 1) or (deltay > 1):
                speed += str(deltax + deltay)
        else:
            # diagonal spaceship (deltax == deltay)
            if deltax > 1:
                speed += str(deltax)
        g.show("Spaceship detected (speed = " + speed + "c/" +str(period) + ")")
    else:
        # deltax != deltay and both > 0
        speed = str(deltay) + "," + str(deltax)
        g.show("Knightship detected (speed = " + speed + "c/" + str(period) + ")")

def oscillating():
	# return True if the pattern is empty, stable or oscillating

	# first get current pattern's bounding box

	# tubebox=[-int(wd/2),-int(ht/2)+3,wd,tht]
	prect = g.getrect()
	pbox = rect(prect)
	
	pop=int(g.getpop())
	if pop==0:
		g.show("The pattern is empty.")
		return True

	# get current pattern and create hash of "normalized" version -- ie. shift
	# its top left corner to 0,0 -- so we can detect spaceships and knightships
	## currpatt = pattern( g.getcells(prect) )
	## h = hash( tuple( currpatt(-pbox.left, -pbox.top) ) )

	# use Golly's hash command (3 times faster than above code)
	h = g.hash(prect)

	# check if outer-totalistic rule has B0 but not S8
	rule = g.getrule().split(":")[0]
	hasB0notS8 = rule.startswith("B0") and (rule.find("/") > 1) and not rule.endswith("8")

	# determine where to insert h into hashlist
	pos = 0
	listlen = len(hashlist)
	while pos < listlen:
		if h > hashlist[pos]:
			pos += 1
		elif h < hashlist[pos]:
			# shorten lists and append info below
			del hashlist[pos : listlen]
			del genlist[pos : listlen]
			del poplist[pos : listlen]
			del boxlist[pos : listlen]
			break
		else:
		# h == hashlist[pos] so pattern is probably oscillating, but just in
		# case this is a hash collision we also compare pop count and box size
			if (int(g.getpop()) == poplist[pos]) and \
			   (pbox.wd == boxlist[pos].wd) and \
			   (pbox.ht == boxlist[pos].ht):
				period = int(g.getgen()) - genlist[pos]

				if hasB0notS8 and (period % 2 > 0) and (pbox == boxlist[pos]):
					# ignore this hash value because B0-and-not-S8 rules are
					# emulated by using different rules for odd and even gens,
					# so it's possible to have identical patterns at gen G and
					# gen G+p if p is odd
					return False

				if period == 1:
					if pbox == boxlist[pos]:
						g.show("The pattern is stable.")
					else:
						show_spaceship_speed(1, 0, 0)
				elif pbox == boxlist[pos]:
					g.show("Oscillator detected (period = " + str(period) + ")")
				else:
					deltax = abs(boxlist[pos].x - pbox.x)
					deltay = abs(boxlist[pos].y - pbox.y)
					show_spaceship_speed(period, deltax, deltay)
				return True
			else:
				# look at next matching hash value or insert if no more
				pos += 1

	# store hash/gen/pop/box info at same position in various lists
	hashlist.insert(pos, h)
	genlist.insert(pos, int(g.getgen()))
	poplist.insert(pos, int(g.getpop()))
	boxlist.insert(pos, pbox)

	return False

def fit_if_not_visible():
    # fit pattern in viewport if not empty and not completely visible
    r = rect(g.getrect())
    if (not r.empty) and (not r.visible()): g.fit()

# --------------------------------------------------------------------
dict_fill={'BGRainbowR2':[0,2,2,4,4,5,6],'WireWorld':[0,1,2,1]}
def randfill_mash(rectcoords, amt):
   newstate = g.getoption("drawingstate")
   for i in range(rectcoords[0],rectcoords[0]+rectcoords[2]):
      for j in range(rectcoords[1],rectcoords[1]+rectcoords[3]):
         if(100*random.random()<amt):
            g.setcell(i, j, dict_fill[rule][g.getcell(i,j)])
         else:
            # g.setcell(i, j, 0)
			continue

dict_lc={'BDRainbow':[2,4],'BGRainbowR2':[2,4]}
live_cells=dict_lc[g.getrule().split(':')[0]]
def popcount():
	clist=g.getcells(g.getrect())
	return sum(clist[2::3].count(x) for x in live_cells)

def list_reset():
	global hashlist,poplist,genlist,boxlist,densilist,longlist,timelist
	hashlist=[]
	poplist=[]
	genlist=[]
	boxlist=[]
	densilist=[]
	longlist=[]
	timelist=[]

def clip_rb (patt, right, bottom):
    # remove any cells outside given right and bottom edges
    clist = list(patt)

    #  remove padding int if present
    if (inc == 3) and (len(clist) % 3 == 1): clist.pop()

    x = 0
    y = 1
    while x < len(clist):
        if (clist[x] > right) or (clist[y] > bottom):
            # remove cell from list
            clist[x : x+inc] = []
        else:
            x += inc
            y += inc

    # append padding int if necessary
    if (inc == 3) and (len(clist) & 1 == 0): clist.append(0)

    return pattern(clist)

def tileit(clist,tilewd):
	global inc,pbox
	cliplist=clist

	# g.select([boxsel[0]-20,boxsel[1]-20,20,20])
	# g.clear(0)	
	# make_text(str(posi)).put(boxsel[0]-20,boxsel[1])
	
	pbox = rect( [0, 0] + cliplist[0 : 2] )
	
	wd=tilewd*pbox.wd
	ht=tilewd*pbox.ht
	boxsel=[-int(wd/2),-int(wd/2),wd,ht]
	g.select(boxsel)
	selrect = rect( g.getselrect() )
	inc=2
	cliplist[0 : 2] = []                      # remove wd,ht
	p = pattern( cliplist )

	if len(cliplist) & 1 == 1: inc = 3        # multi-state?
	g.clear(inside)

	
	if len(cliplist) > 0:
		# tile selrect with p, clipping right & bottom edges if necessary
		y = selrect.top
		while y <= selrect.bottom:
			bottom = y + pbox.height - 1
			x = selrect.left
			while x <= selrect.right:
				right = x + pbox.width - 1
				if (right <= selrect.right) and (bottom <= selrect.bottom):
					p.put(x, y)
				else:
					clip_rb( p(x, y), selrect.right, selrect.bottom ).put()
				x += pbox.width
			y += pbox.height

	if not selrect.visible(): g.fitsel()				

def loadtopo(maxnum,step):
	for i in range(step,maxnum+step,step):
		make_text(str(i)).put(boxwidth*(i-1),0)
		box.put(boxwidth*(i-1),0)
		
		boxsel=[boxwidth*(i-1)+1,1,38,38]
		g.select(boxsel)
		g.shrink()
		if g.getselrect()==boxsel:
			continue
		else:
			clist=g.getcells(g.getselrect())
			sel=g.getselrect()
			for i in range(int(len(clist)/3)):
				clist[3*i]   = clist[3*i]-sel[0]
				clist[3*i+1] = clist[3*i+1]-sel[1]
			clist.insert(0,sel[2])
			clist.insert(1,sel[3])
			tile.append(clist)
	return tile


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

	


input=g.getstring('maxnum/step/boxwidth','100/1/40')
maxnum=int(input.split('/')[0])
step=int(input.split('/')[1])
boxwidth=int(input.split('/')[2])

tile=[]

box=g.parse("40o$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$\
o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38b\
o$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o\
38bo$o38bo$o38bo$o38bo$40o!")
box=pattern(box)
help1='tilewd/soupnum/soupwd/density/gen_thres'
input=g.getstring(help1,'10/100/50/35/500')
tilewd=int(input.split('/')[0])
soupnum=int(input.split('/')[1])
soupwd=int(input.split('/')[2])
density=int(input.split('/')[3])
gen_thres=int(input.split('/')[4])

if 	g.getrule().split(':')[0] in dict_lc:
	yfunc='popc'
else:
	yfunc='pop'
vars=g.getstring("yVar/yxVar, \n pop=population,\n gen=generation,\n boxy=width of bounding box,\n boxx=height of bounding box,\n density=population/area of bindingbox ,\n area=area of bounding box","%s/gen"%yfunc)
dict_lc={'BDRainbow':[2,4],'BGRainbowR2':[2,4]}
live_cells=dict_lc[g.getrule().split(':')[0]]
dict_f = {'popc':popcount,'pop': g.getpop, 'gen': g.getgen,'boxx':lambda:boxdm(2) ,'boxy': lambda: boxdm(3),'area':area,'density':density, \
		'logpop':lambda:int(int(g.getpop())*math.log(float(g.getpop()))/math.log(2)),'popi':lambda:int(1000000000/float(g.getpop())), 'areai':lambda:int(1000000000/float(int(boxdm(2))*int(boxdm(3))))}
dict_t={'popc':'Population','pop':'Population','gen':'Generation','boxx':'Box width','boxy':'Box height','area':'Box area','density':'Cell density (0.001)',\
		'logpop':'log(pop)','popi':'inverse of pop','areai':'inverse of area'}
yfunc=dict_f[vars.split("/")[0]]
xfunc=dict_f[vars.split("/")[1]]
ytitle=dict_t[vars.split("/")[0]]
xtitle=dict_t[vars.split("/")[1]]
htlist=[]
plotlist=[]
	
	
tile=loadtopo(maxnum,step)	
# g.note(str(tile[0]))

if not tile==[]:
	# add a layer
	layername = "Topology_Search"
	poplayer = -1
	for i in xrange(g.numlayers()):
		if g.getname(i) == layername:
			poplayer = i
			break
	if poplayer == -1 and g.numlayers() == g.maxlayers():
		g.exit("You need to delete a layer.")
	if poplayer == -1:
		poplayer = g.addlayer()
	else:
		g.setlayer(poplayer)
	tilelayer=g.getlayer()
	g.new(layername)	
	if not g.empty():
		g.select(g.getrect())
		g.clear(0)

	
	rule=g.getrule().split(':')[0]
	rule0=rule
	rule=rule.replace('/','-')
	out=0
	next=0
	posi=0

	
	input=g.getstring('subset?','')
	poslist=input.split(',')
	if len(poslist)==1:
		poslist=range(len(tile))
	else:
		for i in range(len(poslist)):
			poslist[i]=int(poslist[i])
	

	for j in range(len(poslist)):
		posi=poslist[j]
		i=tile[posi]

		g.setlayer(tilelayer)
		if out: break
		if not g.empty():
			g.new('')
		# posi=posi+1	
		
		# start a evaluation loop
		left=-int(tilewd/2)
		top=-int(tilewd/2)
		boxsel=[-int(tilewd/2),-int(tilewd/2),tilewd,tilewd]
		tileit(i,tilewd)
		wd=tilewd*pbox.wd
		ht=tilewd*pbox.ht
		boxsel=[-int(wd/2),-int(wd/2),wd,ht]
		randfill_mash(boxsel,density)		
	
		poplist	= [ int(yfunc()) ]
		genlist = [ int(xfunc()) ]
		xlimlist= [int(g.getrect()[1])]
		oldsecs = time()
		for i in xrange(numsteps):

			g.step()
			poplist.append( int(yfunc()) )
			genlist.append( int(xfunc()) )
			newsecs = time()
			if newsecs - oldsecs >= 1.0:     # show pattern every second
				oldsecs = newsecs
				fit_if_not_visible()
				g.update()
			g.show("Step %i of %i, Topo %i" % (i+1, numsteps,posi))
			
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
		
		
		layername = "population plot"
		poplayer = -1
		for i in xrange(g.numlayers()):
			if g.getname(i) == layername:
				poplayer = i
				break
		if poplayer == -1 and g.numlayers() == g.maxlayers():
			g.exit("You need to delete a layer.")
		if poplayer == -1:
			poplayer = g.addlayer()
		else:
			g.setlayer(poplayer)

		if poplayer == -1:
			poplayer = g.addlayer()
		else:
			g.setlayer(poplayer)
		plotlayer=g.getlayer()
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

		# popscale=g.getstring('what scale to use for pop/y?','%i'%int((maxpop-minpop)/100))
		popscale=1
		popscale=int(popscale)
		mingen = min(genlist)
		maxgen = max(genlist)	
		xlen=maxgen-mingen
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
		htlist.append(g.getrect()[3])
		plotlist.append(g.getcells(g.getrect()))

g.setlayer(plotlayer)
g.new('')
ht=0
for i in range(len(plotlist)):
	ht=ht+htlist[i]+20
	make_text(str(i)).put(-500,ht)		
	g.putcells(plotlist[i],	0,ht)
	
g.setclipstr(str(htlist))
g.setname('bk_plot')
