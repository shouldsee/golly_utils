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
import numpy as np
import hashlib
import math as m
import csv
import os
# from utils import *
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

def randfill(rectcoords, amt,amt2=50,secondary_state=1):
   statelist=[ g.getoption("drawingstate"),secondary_state]
   g.note(str(statelist))
   for i in range(rectcoords[0],rectcoords[0]+rectcoords[2]):
      for j in range(rectcoords[1],rectcoords[1]+rectcoords[3]):
         if(100*random.random()<amt):
     		newstate=(100*random.random()>amt2)
        	g.setcell(i, j, statelist[newstate])
         else:
            # g.setcell(i, j, 0)
			continue

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

def adj_hash(pbox):
	def parse_list(clist):
		newlist=[]
		for i in range(len(clist[0::3])):
			if 3*i+3 <= len(clist):
				temp=clist[3*i:3*i+3]
				newlist.append(temp)
			else:
				break
		return(newlist)

	def adjacencymatrix(parsed_clist,pbox=pbox,torus=0):
		adjacencymatrix=[]
		if torus:
			adjacency_x=[0,1,pbox[2]-1]
			adjacency_y=[0,1,pbox[3]-1]
		else:
			adjacency_x=[0,1]
			adjacency_y=[0,1]
		# fclist=full_clist(parsed_clist,pbox)
		for i in parsed_clist:
			row=[]
			for j in parsed_clist:
				if 	i!=j and \
				(abs(i[0]-j[0]) in adjacency_x) and \
				(abs(i[1]-j[1]) in adjacency_y) and \
				[i[2],j[2]]==[state,state]:
					row.append(1)
				else:
					row.append(0)
					
			adjacencymatrix.append(row)
		return adjacencymatrix


	clist=getquad(pbox)
	pbox[2]=2*pbox[2]
	pbox[3]=2*pbox[3]
	parsed_clist=parse_list(clist)
	state = g.getoption("drawingstate")
	adjmat=adjacencymatrix(parsed_clist,pbox,torus=1)
	eigval=np.linalg.eigvalsh(adjmat)
	eigval =np.round( eigval,decimals=5)
	h=hash(tuple(eigval))	
	return h
	
	# a =np.around( eigval,decimals=5)
	# b=a.view(np.uint8)
	# h=hashlib.sha1(b).hexdigest()

def getquad(pbox):
	newlist=[]
	clist=g.getcells(pbox)
	for i in range(len(clist[0::3])):
		if 3*i+3 <= len(clist):
			temp=clist[3*i:3*i+3]
			for x in [0,pbox[2]]:
				for y in [0,pbox[3]]:
					newlist.append(temp[0]+x)
					newlist.append(temp[1]+y)
					newlist.append(temp[2])

	newlist.append(0)
	return newlist

dir=g.getdir('rules')+'BGRainbow\\TopoSearch\\'
try:
	os.makedirs(dir)
except:
	pass

	
# #test
# pbox=g.getselrect()
# clist=g.getcells(pbox)
# clist_new=quad(pbox)
# g.exit()

hashlist=[]
topolist=[]



input=g.getstring('toponum/sizerange/bool_randoms','1000/3,4/0')
toponum=int(input.split('/')[0])

low=int(input.split('/')[1].split(',')[0])
high=int(input.split('/')[1].split(',')[1])
sizelist=range(low,high+1)
bool_random=int(input.split('/')[2])
# def randtopo(topnum,low,high):
i=0
wd=low
ht=low
while (bool_random==1 and i != toponum) or (not bool_random and not([wd,ht]==[sizelist[1]]*2)) :
	g.show('topo %i of %i'%(i,toponum))
	
	size=random.choice(sizelist)
	area=size*size
	sel=[size,size,size,size]
	g.new('')
	if bool_random:
		randfill(sel,(1+random.randrange(area))*int(100/area))
	# else:
	# generate a 2 
		
	if g.empty():
		continue
		
	raw_line(x1, y1, x2, y2):
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
   
	pbox=g.getrect()
	h=adj_hash(pbox)
	
	# h=g.hash(g.getrect())
	
	
	event=g.getevent()
	if event.startswith("key"):
		evt, ch, mods = event.split()
		if ch == "q":
			out=1
			break
		if ch == "n":
			next=1
			break	
	if h in hashlist:
		continue
	else:
		hashlist.append(h)
		pbox=g.getrect()
		actarea=pbox[2]*pbox[3]
		clist=g.getcells(g.getrect())
		g.store(clist,dir+'topo_area%i_hash%s'%(actarea,h))

		clist.insert(0,pbox[2])			#prepare for tiling
		clist.insert(1,pbox[3])
		topolist.append(clist)
		i=i+1
		continue


		# return topolist

wd=0
for i in topolist:
	i=i[2:]
	p=pattern(i)
	# wd=wd+getminbox(p)+20
	wd=wd+40
	p.put(wd,0)
