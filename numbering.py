from collections import Counter
import golly as g
from glife import *
from glife.text import make_text
from time import time
import random
import math as m
import csv
import os

input=g.getstring('max/step/boxwidth','36/2/20')
max=int(input.split('/')[0])
step=int(input.split('/')[1])
boxwidth=int(input.split('/')[2])


box=g.parse("40o$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$\
o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38b\
o$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o\
38bo$o38bo$o38bo$o38bo$40o!")



box=pattern(box)

# box=pattern()
for i in range(step,max+step,step):
	make_text(str(i)).put(boxwidth*(i-1),0)
	box.put(boxwidth*(i-1),0)
	