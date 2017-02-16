# Calculates the density of live cells in the current pattern.
# Author: Andrew Trevorrow (andrew@trevorrow.com), March 2006.
# Updated to use exit command, Nov 2006.

import golly as g
from glife import *
from utils import *

def popcount(sel=0):
	dict_lc={'BDRainbow':[2,4],'BGRainbowR2':[2,4]}
	live_cells=dict_lc[g.getrule().split(':')[0]]	
	if not sel:
		clist=g.getcells(g.getrect())
	else:
		clist=g.getcells(g.getselrect())		
		return sum(clist[2::3].count(x) for x in live_cells)
	
pop=popcount(sel=1)
medium=int(len(g.getcells(g.getselrect()))/3)

density=float(pop)/float(medium)*100

g.setclipstr(str(density))
g.show('density=%i/100,pop=%i,medium=%i'%(density,pop,medium))