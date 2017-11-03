# Output an adjacency matrix for current selection to clipborad in a "Mathematica" list fomart 
# Use AdjacencyGraph[] in Mathematica for downstream processing.
# Author: Feng Geng(shouldsee.gem@gmail.com), May 2016.

import golly as g
from glife import *
import numpy as np
import hashlib

stepmax=int(g.getstring('steps to advance','100'))
sel=g.getselrect()
step=1
while step<=stepmax:
	g.advance(0,1)
#	execfile('invert.py')	
	step=step+1
	g.update()
