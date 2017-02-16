# Creates a histogram plot showing the frequencies of all cell states
# in the current selection (if one exists) or the entire pattern.
# Author: Andrew Trevorrow (andrew@trevorrow.com), September 2009.

import golly as g
import math
from glife import getminbox, rect, rccw, pattern
from glife.text import make_text
from time import time



# --------------------------------------------------------------------

barwd = 40     # width of each bar

# length of axes
xlen = g.numstates() * barwd
ylen = 500

totalcells = 0

# --------------------------------------------------------------------

def draw_line(x1, y1, x2, y2, state = 1):
   # draw a line of cells in given state from x1,y1 to x2,y2
   # using Bresenham's algorithm
   g.setcell(x1, y1, state)
   if x1 == x2 and y1 == y2: return
   
   dx = x2 - x1
   ax = abs(dx) * 2
   sx = 1
   if dx < 0: sx = -1
   dy = y2 - y1
   ay = abs(dy) * 2
   sy = 1
   if dy < 0: sy = -1
   
   if ax > ay:
      d = ay - (ax / 2)
      while x1 != x2:
         g.setcell(x1, y1, state)
         if d >= 0:
            y1 += sy
            d -= ax
         x1 += sx
         d += ay
   else:
      d = ax - (ay / 2)
      while y1 != y2:
         g.setcell(x1, y1, state)
         if d >= 0:
            x1 += sx
            d -= ay
         y1 += sy
         d += ax
   
   g.setcell(x2, y2, state)

# --------------------------------------------------------------------

def color_text(string, extrastate):
   t = make_text(string, "mono")
   bbox = getminbox(t)
   # convert two-state pattern to multi-state and set state to extrastate
   mlist = []
   tlist = list(t)
   for i in xrange(0, len(tlist), 2):
      mlist.append(tlist[i])
      mlist.append(tlist[i+1])
      mlist.append(extrastate)
   if len(mlist) % 2 == 0: mlist.append(0)
   p = pattern(mlist)
   return p, bbox.wd, bbox.ht

# --------------------------------------------------------------------

def draw_bar(state, extrastate):
   barht = int( float(ylen) * float(statecount[state]) / float(totalcells) )
   x = barwd * state
   draw_line(x, 0, x, -barht, extrastate)
   draw_line(x, -barht, x+barwd, -barht, extrastate)
   draw_line(x+barwd, 0, x+barwd, -barht, extrastate)
   if barht > 1:
      # fill bar with corresponding color
      x1 = x + 1
      x2 = x + barwd - 1
      for y in xrange(barht - 1):
         draw_line(x1, -(y+1), x2, -(y+1), state)
   if statecount[state] > 0:
      # show count on top of bar
      t, twd, tht = color_text(str(statecount[state]), extrastate)
      t.put(barwd * (state+1) - barwd/2 - twd/2, -barht - tht - 3)

# --------------------------------------------------------------------

if g.empty(): g.exit("There is no pattern.")
if g.numstates() == 256: g.exit("No room for extra state.")

# check that a layer is available for the histogram
histname = "histogram"
histlayer = -1
for i in xrange(g.numlayers()):
   if g.getname(i) == histname:
      histlayer = i
      break
if histlayer == -1 and g.numlayers() == g.maxlayers():
   g.exit("You need to delete a layer.")

# use selection rect if it exists, otherwise use pattern bounds
label = "Selection"
r = rect( g.getselrect() )
if r.empty:
   label = "Pattern"
   r = rect( g.getrect() )

# count all cell states in r
g.show("Counting cell states...")
counted = 0
totalcells = r.wd * r.ht
statecount = [0] * g.numstates()
oldsecs = time()
for row in xrange(r.top, r.top + r.height):
   for col in xrange(r.left, r.left + r.width):
      counted += 1
      statecount[g.getcell(col,row)] += 1
      newsecs = time()
      if newsecs - oldsecs >= 1.0:     # show % done every sec
         oldsecs = newsecs
         done = 100.0 * float(counted) / float(totalcells)
         g.show("Counting cell states... %.2f%%" % done)
         g.dokey( g.getkey() )

statecount=[int(10*math.log((x+1),2)) for x in statecount]
totalcells=sum(statecount)
if statecount[0] == counted: g.exit("Selection is empty.")

# save current layer's info before we switch layers
currname = g.getname()
currcursor = g.getcursor()
currcolors = g.getcolors()
currstates = g.numstates()
deads, deadr, deadg, deadb = g.getcolors(0)

# create histogram in separate layer
g.setoption("stacklayers", 0)
g.setoption("tilelayers", 0)
g.setoption("showlayerbar", 1)
if histlayer == -1:
   histlayer = g.addlayer()
else:
   g.setlayer(histlayer)

g.new(histname)
g.setcursor(currcursor)

# use a Generations rule so we can append extra state for drawing text & lines
g.setrule("//" + str(currstates+1))
extrastate = currstates
currcolors.append(extrastate)
if (deadr + deadg + deadb) / 3 > 128:
   # use black if light background
   currcolors.append(0)
   currcolors.append(0)
   currcolors.append(0)
else:
   # use white if dark background
   currcolors.append(255)
   currcolors.append(255)
   currcolors.append(255)
g.setcolors(currcolors)

# draw axes with origin at 0,0
draw_line(0, 0, xlen, 0, extrastate)
draw_line(0, 0, 0, -ylen, extrastate)

# add annotation using mono-spaced ASCII font
t, twd, tht = color_text("Pattern name: "+currname, extrastate)
t.put(0, -ylen - 30 - tht)

t, twd, tht = color_text("%s size: %d x %d (%d cells)" %
                           (label, r.wd, r.ht, totalcells), extrastate)
t.put(0, -ylen - 15 - tht)

t, twd, tht = color_text("% FREQUENCY", extrastate)
t.put(-35 - tht, -(ylen - twd)/2, rccw)

for perc in xrange(0, 101, 10):
   t, twd, tht = color_text(str(perc), extrastate)
   y = -perc * (ylen/100)
   t.put(-twd - 10, y - tht/2)
   ### draw_line(-3, y, 0, y, extrastate)
   # draw dotted horizontal line from 0 to xlen
   for x in xrange(0, xlen, 2): g.setcell(x, y, extrastate)

t, twd, tht = color_text("STATE", extrastate)
t.put((xlen - twd)/2, 30)

for state in xrange(extrastate):
   t, twd, tht = color_text(str(state), extrastate)
   t.put(barwd * (state+1) - barwd/2 - twd/2, 10)
   draw_bar(state, extrastate)

# display result at scale 1:1
g.fit()
g.setmag(0)
g.show("")
