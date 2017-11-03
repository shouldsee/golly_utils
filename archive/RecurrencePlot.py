# Run the current pattern for a given number of steps (using current
# step size) and create a plot of population vs time in separate layer.
# Author: Andrew Trevorrow (andrew@trevorrow.com), May 2007.

import golly as g
from glife import *
from glife.text import make_text
from time import time
from random import random
import math

clist=[]
fill = int(g.getoption("drawingstate"))
def rp_plot(input,fill=fill):
	m=len(input);
	for i in range(m):
		for j in range(m):
			d=norm(input[i],input[j])
			if d<=dmax:
				g.setcell(i,-j,fill)
			
	#		clist.append(i)
	#		clist.append(j)
	#		clist.append(input[i]==input[j])
	#g.putcells(clist,0,0)

def norm(a,b):
	return abs(a-b)


def popcount(sel=0):
	dict_lc={'BDRainbow':[2,4],'BGRainbowR2':[2,4]}
	live_cells=dict_lc[g.getrule().split(':')[0]]	
	if not sel:
		clist=g.getcells(g.getrect())
	else:
		clist=g.getcells(g.getselrect())		
	return sum(clist[2::3].count(x) for x in live_cells)
	

dict_lc={'BDRainbow':[2,4],'BGRainbowR2':[2,4]}

input=(g.getstring('How many steps?/similarity distance?','2000/1'))
numsteps=int(input.split('/')[0])
dmax=int(input.split('/')[1])


if g.getrule().split(':')[0] in dict_lc:
	popfunc=lambda:popcount(sel)

else:
	popfunc=lambda:g.getpop()



poplist=[]
dpoplist=[]
hashlist=[int(g.hash(g.getrect()))]
popold=int(g.getpop())
dead=0
sel=(g.getrect()!=[])

popold=int(popfunc())

poplist.append(popold)
dpoplist.append(0)
for i in range(numsteps):
	g.run(1)	
	if g.empty():
		break	
	pop=int(popfunc())
	poplist.append(pop)
	dpoplist.append(pop-popold)
	
	h=int(g.hash(g.getrect()))
	if h in hashlist:
		break
	hashlist.append(h)

layername = "recurrent plot"
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

rp_plot(poplist)
