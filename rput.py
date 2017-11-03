# A randomized rectangle filler for use with Golly.
# Author: Nathaniel Johnston (nathaniel@nathanieljohnston.com), June 2009.
#
# Even though Golly comes built-in with the golly.randfill() function, there
# does not seem to be a way to seed that function, so you get the same sequence
# of random rectangles every time you reload Golly. This script eliminates that
# problem.


import golly as g
import random
from glife import *
from utils import *
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

def randput(rectcoords,clist,symlist,amt=50):
   xlist=range(rectcoords[0],rectcoords[0]+rectcoords[2])
   ylist=range(rectcoords[1],rectcoords[1]+rectcoords[3])

   size=int(len(clist)/3)
   base=pattern(clist)
   box=getminbox(base)
   num=int(len(xlist)*len(ylist)/size)
#   num=10
   for i in range(num):
      if (100*random.random())<amt:
         n=0
         while True:
            x=random.choice(xlist)
            y=random.choice(ylist)
            sym=random.choice(symlist)
            tpbox=multiply(sym,[box.wd,0,box.ht,0])
            wd=tpbox[0]
            ht=tpbox[2]


            tpbox=[min(x-1,x+wd),min(y-1,y+ht),abs(wd)+2,abs(ht)+2]
            g.select(tpbox)
            pop=popcount(sel=1)
            
            if pop==0:
               base.put(x,y,sym)
            #   g.note('pop=%i \n wd=%i \n ht=%i'%(pop,wd,ht) )
               break
            else:
               n=n+1
               if n>1000:
                  g.note('Too many attemps'+str(tpbox))
                  g.exit()

      else:
         continue



def multiply(a,b):
   b1=[b[i] for i in [0,2]]
   b2=[b[i] for i in [1,3]]
   a1=[a[0],a[1]]
   a2=[a[2],a[3]]
   return [vmt(a,b)  for a in [a1,a2] for b in [b1,b2] ]
def vmt(a,b):
   ma=len(a)
   mb=len(b)
   if ma==mb:
      return sum([a[i]*b[i] for i in range(ma)])
   else:
      g.show('Vector not of same length')
      return NaN

# --------------------------------------------------------------------

if len(g.getselrect()) == 0: g.exit("No selection.")
s = g.getstring("Enter the fill percentage (0.0 - 100.0):","50", "Random filler")
try:
   amt = float(s)
   if amt < 0 or amt > 100:
      g.exit('Bad number: %s' % s)
except ValueError:
   g.exit('Bad number: %s' % s)
 

base=g.parse(g.getstring("RLE string for your seed","CBA$CBA!"))
symlist=[identity,rcw,rccw,flip_x]

# base=pattern(base)

# for sym in symlist:
#    base.put(1,1,sym)

l1=[5,6,7,8]
l2=[4,3,2,1]
#g.note(str(multiply(l1,l2)))
randput(g.getselrect(),base,symlist,amt)
