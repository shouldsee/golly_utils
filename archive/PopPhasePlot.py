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
def rp_plot(a,b,fill=fill):
	ma=max(a)
	mb=max(b)
	
	l=range(min(len(a),min(b)))
#	g.note('%i'%min(8,8))
	for i in range(min(len(a),len(b))):
#	for i in range(ma+1):
#		for j in range(mb+1):
#			if i==a[i] and j==b[j]:
		
		g.setcell(a[i],-b[i],fill)
#			d=norm(input[i],input[j])
#			if d<=dmax:		
	#		clist.append(i)
	#		clist.append(j)
	#		clist.append(input[i]==input[j])
	

def norm(a,b):
	return abs(a-b)


def popcount(sel=0):
	dict_lc={'BDRainbow':[2,4],'BGRainbowR2':[2,4]}
	live_cells=dict_lc[g.getrule().split(':')[0]]	
	if sel:
		clist=g.getcells(g.getselrect())		
	else:
		clist=g.getcells(g.getrect())

	return sum(clist[2::3].count(x) for x in live_cells)
	

dict_lc={'BDRainbow':[2,4],'BGRainbowR2':[2,4]}

input=(g.getstring('How many steps?/similarity distance?','2000/1'))
numsteps=int(input.split('/')[0])
dmax=int(input.split('/')[1])
sel=(g.getselrect()!=[])

rule=g.getrule().split(':')[0]
if rule in dict_lc:
	popfunc=lambda:popcount(sel)
else:
	popfunc=lambda:int(g.getpop())



poplist=[]
dpoplist=[]
hashlist=[int(g.hash(g.getrect()))]
popold=int(popfunc())

poplist.append(popold)
dpoplist.append(0)
for i in range(numsteps):
	g.step()	
	if g.empty():
		break	
	pop=int(popfunc())
	poplist.append(pop)
	dpoplist.append(pop-popold)
	
	h=int(g.hash(g.getrect()))
	if h in hashlist:
		break
	hashlist.append(h)
	popold=pop
	

	event=g.getevent()
	if event.startswith("key"):
		evt, ch, mods = event.split()
		if ch == "q":
			out=1
			break
		if ch == "n":
			next=1
			break	
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
g.setrule(rule)

rp_plot(poplist,dpoplist)
