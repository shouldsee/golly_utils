# Output an adjacency matrix for current selection to clipborad in a "Mathematica" list fomart 
# Use AdjacencyGraph[] in Mathematica for downstream processing.
# Author: Feng Geng(shouldsee.gem@gmail.com), May 2016.

import golly as g
from glife import *
import numpy as np
import hashlib

rule=g.getrule()
g.setrule(rule.split(':')[0])

