# A randomized rectangle filler for use with Golly.
# Author: Nathaniel Johnston (nathaniel@nathanieljohnston.com), June 2009.
#
# Even though Golly comes built-in with the golly.randfill() function, there
# does not seem to be a way to seed that function, so you get the same sequence
# of random rectangles every time you reload Golly. This script eliminates that
# problem.


import golly as g
import random
g.note(str(g.getcells(g.getselrect())))
