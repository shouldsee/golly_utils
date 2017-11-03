# A randomized rectangle filler for use with Golly.
# Author: Nathaniel Johnston (nathaniel@nathanieljohnston.com), June 2009.
#
# Even though Golly comes built-in with the golly.randfill() function, there
# does not seem to be a way to seed that function, so you get the same sequence
# of random rectangles every time you reload Golly. This script eliminates that
# problem.


import golly as g
import random
random.seed()

# --------------------------------------------------------------------

def randfill_mash(rectcoords, amt,statemap):
	newstate = g.getoption("drawingstate")
#	g.note('%s'%statemap)
	for i in range(rectcoords[0],rectcoords[0]+rectcoords[2]):
		for j in range(rectcoords[1],rectcoords[1]+rectcoords[3]):
			if(100*random.random()<amt):
				try:
					g.show('processing %i,%i'%(i,j))
					g.setcell(i, j, statemap[g.getcell(i,j)])
				except:
					dict_lc=[1]*g.numstates()
					dict_lc[0]=0
					dict_lc[1:3]=[2,2]
					g.setcell(i, j, dict_lc[g.getcell(i,j)])
			else:
			# g.setcell(i, j, 0)
				continue

# --------------------------------------------------------------------

if len(g.getselrect()) == 0: g.exit("No selection.")
s = g.getstring("Enter the fill percentage (0.0 - 100.0):","35", "Random filler")
rule=g.getrule().split(':')[0]

dict_lc={'BGRainbowR2':[0,2,2,4,4,5,6],'WireWorld':[0,1,2,1],'v3k4_202200222012210':{0,3,2,3}}

if rule in dict_lc:
	statemap=dict_lc[rule]
else:
	statemap=g.getstring('statemap?','0/1/2/3').split('/')
	statemap=[int(i) for i in statemap] 

try:
   amt = float(s)
   if amt < 0 or amt > 100:
      g.exit('Bad number: %s' % s)
except ValueError:
   g.exit('Bad number: %s' % s)
 
randfill_mash(g.getselrect(),amt,statemap)
