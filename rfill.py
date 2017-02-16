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

def randfill(rectcoords, amt):
   newstate = g.getoption("drawingstate")
   for i in range(rectcoords[0],rectcoords[0]+rectcoords[2]):
      for j in range(rectcoords[1],rectcoords[1]+rectcoords[3]):
         if(100*random.random()<amt):
            g.setcell(i, j, newstate)
         else:
            # g.setcell(i, j, 0)
			continue

# --------------------------------------------------------------------

if len(g.getselrect()) == 0: g.exit("No selection.")
s = g.getstring("Enter the fill percentage (0.0 - 100.0):","", "Random filler")
try:
   amt = float(s)
   if amt < 0 or amt > 100:
      g.exit('Bad number: %s' % s)
except ValueError:
   g.exit('Bad number: %s' % s)
 
randfill(g.getselrect(),amt)
