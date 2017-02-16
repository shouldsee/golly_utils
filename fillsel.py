# Fill clicked region with current drawing state.
# Author: Andrew Trevorrow (andrew@trevorrow.com), Jan 2011.

import golly as g
from time import time

def fill(rectcoords):
   newstate = g.getoption("drawingstate")
   for i in range(rectcoords[0],rectcoords[0]+rectcoords[2]):
      for j in range(rectcoords[1],rectcoords[1]+rectcoords[3]):
            g.setcell(i, j, newstate)

			
try:
	sel=g.getselrect()
	fill(sel)
except:
	g.show('no selection')
	
