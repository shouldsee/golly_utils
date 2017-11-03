# Invert all cell states in the current selection.
# Author: Andrew Trevorrow (andrew@trevorrow.com), Jun 2006.
# Updated to use exit command, Nov 2006.
# Updated to use numstates command, Jun 2008.

from glife import rect
from time import time
import golly as g

r = rect( g.getselrect() )
if r.empty: g.exit("There is no selection.")

oldsecs = time()
maxstate = g.numstates() - 1

for row in xrange(r.top, r.top + r.height):
    # if large selection then give some indication of progress
    newsecs = time()
    if newsecs - oldsecs >= 1.0:
        oldsecs = newsecs
        g.update()
    for col in xrange(r.left, r.left + r.width):
	if row%2==0:
		a=g.getcell(col, row)
		b=g.getcell(col, row+1)
		if a+b==2:
			anew=0
			bnew=1
		elif a+b==0:
			anew=1
			bnew=0
		elif a+b==1:
			if a==1:
				anew=0
				bnew=0
			else:
				anew=1
				bnew=1
		
		g.setcell(col, row, anew)
		g.setcell(col, row+1, bnew)
	

if not r.visible(): g.fitsel()
