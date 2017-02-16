from collections import Counter
import golly as g
from glife import *
from utils import *

from glife.text import make_text
from time import time
import random
import math as m
import csv
import os

debug=0

workingdir=g.getdir('rules')+'BGRainbow\\TopoSearch\\'
try:
	os.makedirs(workingdir)
except:
	pass

input=g.getstring('max/step/boxwidth','100/1/40')
max=int(input.split('/')[0])
step=int(input.split('/')[1])
boxwidth=int(input.split('/')[2])

help1='tilewd/soupnum/soupwd/density/gen_thres'
input=g.getstring(help1,'10/100/50/35/500')
tilewd=int(input.split('/')[0])
soupnum=int(input.split('/')[1])
soupwd=int(input.split('/')[2])
density=int(input.split('/')[3])
gen_thres=int(input.split('/')[4])

tile=[]
box=g.parse("40o$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$\
o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38b\
o$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o\
38bo$o38bo$o38bo$o38bo$40o!")
box=pattern(box)

def randtopo( num , low , high ):
	# global 	hashlist,topolist,	arealist
	hashlist=[]
	topolist=[]
	arealist=[]
	i=0
	while i<num:
		g.show('searching topo %i of %i '%(i,num))
		size=random.choice(range(low,high+1))
		area=size*size
		sel=[size,size,size,size]
		g.new('')
		randfill(sel,(1+random.randrange(area))*int(100/area))
		if g.empty():
			continue
		h=g.hash(g.getrect())
		if h in hashlist:
			continue
		else:
			hashlist.append(h)
			pbox=g.getrect()
			actarea=pbox[2]*pbox[3]
			clist=g.getcells(g.getrect())
			g.store(clist,workingdir+'topo_area%i_hash%i'%(actarea,h))

			clist.insert(0,pbox[2])			#prepare for tiling
			clist.insert(1,pbox[3])
			topolist.append(clist)
			arealist.append(actarea)
			i=i+1
			continue
	return [topolist,hashlist,arealist]


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

def loadtopo():
	for i in range(step,max+step,step):
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






input=g.getstring('cyclenum/toponum/sizelist/bool_rand1_read0','5/10000/3,4/1')

cyclenum=int(input.split('/')[0])
toponum=int(input.split('/')[1])
low=int(input.split('/')[2].split(',')[0])
high=int(input.split('/')[2].split(',')[1])
rand=int(input.split('/')[3])

for c in range(cyclenum):
	if rand:
		output=randtopo(toponum,low,high)
		tile=output[0]
		topohash=output[1]
		topoarea=output[2]
		
	else:
		tile=loadtopo()

	# tile.append(g.getcells(g.getselrect()))
	# tile now includes cell list for topos




	# Future
	# generate random topology
	# hash the topology

	# compare hash with a library
	# if not repeated 

	# start evaluation

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
		g.new(layername)	
		if not g.empty():
			g.select(g.getrect())
			g.clear(0)


		rule=g.getrule().split(':')[0]
		rule0=rule
		rule=rule.replace('/','-')

		i=0
		while True:
			try:
				filename=g.getdir('rules')+'topoS_%s_%i.csv'%(rule,i)
				myfile = open(filename, 'r')
				i=i+1
				continue
			except:
				break

		myfile=open(filename, 'wb')
		myfile.write('rule\n%s\n %s=%s'%(rule,help1,input))
		out=0
		next=0
		posi=0
		for pos in range(len(tile)):
			i=tile[pos]
			if debug!=0: g.note(str(i))

			if out: break
			posi=posi+1	
			# start a evaluation loop
			left=-int(tilewd/2)
			top=-int(tilewd/2)
			boxsel=[-int(tilewd/2),-int(tilewd/2),tilewd,tilewd]
			# output a buffer line and an index
			if rand:
				myfile.write('\n \n hash%i arealist%i \n'%(topohash[pos],topoarea[pos]))			
			else:
				myfile.write('\n \n index%i \n'%posi)
				
			# tile the universe 100*100
			
			
			tileit(i,tilewd)
			g.select(boxsel)
			tempfile=g.getdir('rules')+'topoS_temptile'
			
			list_reset()
			
			# An I/O race
				# tile_clist=g.getcells(boxsel)
				# g.new('')
				# t1=time()
				# tile_clist=g.putcells(tile_clist,0,0)
				# t2=time()
				
				# tempfile=g.getdir('rules')+'topoS_temptile'
				# g.save(tempfile,'rle')
				# t3=time()
				# g.open(tempfile)
				# t4=time()
			
				# g.note('clist io %ims,temptile io %ims '%(1000*(t2-t1),1000*(t4-t3)))

			for j in range(soupnum):
				if out or next: break
				g.show('processing topo %i, soup %i'%(posi,j))
				g.new('')
				g.open(tempfile)
				g.setname(layername)
				if debug=='load': g.exit()
				t1=time()

				# wd=soupwd*pbox.wd
				# ht=soupwd*pbox.ht
				# soupsel=[-int(wd/2),-int(ht/2),wd,ht]
				
				wd=tilewd*pbox.wd
				ht=tilewd*pbox.ht
				boxsel=[-int(wd/2),-int(wd/2),wd,ht]
				randfill_mash(boxsel,density)
				
				while not oscillating():
					t3=time()
					g.run(1)
					t4=time()
					if t4-t3>1:
						break
					if int(g.getgen())>gen_thres: break
							
					event=g.getevent()
					if event.startswith("key"):
						evt, ch, mods = event.split()
						if ch == "q":
							out=1
							break
						if ch == "n":
							next=1
							break	
				t2=time()
				if not g.getgen()=='0':
					longlist.append(m.log(int(g.getgen()),10))
					poplist.append(popcount())
					timelist.append(t2-t1)
				
			# oscillating()
			
			# if gen > 5000,break, lifespan=g.getgen()
			# count end pop
			# 
			# time each cycle
			# table the result, 
			
				# allow key board exit by 'q'
				
			
			
			myfile.write('\n longev,')
			try:
				longlist.insert(0,sum(longlist)/len(longlist))
				longlist.insert(1,0)
				for i in longlist:
					myfile.write('%s,'%i)		
				
				myfile.write('\n endpop,')
				poplist.insert(0,sum(poplist)/len(poplist))
				poplist.insert(1,0)
				for i in poplist:
					myfile.write('%s,'%i)
					
				myfile.write('\n longev,')
				timelist.insert(0,sum(timelist)/len(timelist))
				timelist.insert(1,0)
				for i in timelist:
					myfile.write('%s,'%i)
			except:
				pass
		myfile.close()

