from collections import Counter
import golly as g
from glife import *
from glife.text import make_text
from time import time
import random
import math as m
import csv
import os

input=g.getstring('max/step/boxwidth','100/1/40')
maxnum=int(input.split('/')[0])
step=int(input.split('/')[1])
boxwidth=int(input.split('/')[2])

tile=[]


#make a box
box=[]
for x in range(boxwidth):
	for y in range(boxwidth):
		if x in [0,boxwidth-1] or  y in [0,boxwidth-1] :
			for i in [x,y,1]:
				box.append(i)
if len(box)%2 ==0: box.append(0)
# box=g.parse("40o$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$\
# o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38b\
# o$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o38bo$o\
# 38bo$o38bo$o38bo$o38bo$40o!")
g.putcells(box,0,0)
# box=pattern(box)


def clip_rb (patt, right, bottom):
    # remove any cells outside given right and bottom edges
    clist = list(patt)

    #  remove padding int if present
    if (inc == 3) and (len(clist) % 3 == 1): clist.pop()

    x = 0
    y = 1
    while x < len(clist):
        if (clist[x] > right) or (clist[y] > bottom):
            # remove cell from list
            clist[x : x+inc] = []
        else:
            x += inc
            y += inc

    # append padding int if necessary
    if (inc == 3) and (len(clist) & 1 == 0): clist.append(0)

    return pattern(clist)


for i in range(step,maxnum+step,step):
	make_text(str(i)).put(boxwidth*(i-1),0)
	g.putcells(box,boxwidth*(i-1),0)
	
	boxsel=[boxwidth*(i-1)+1,1,boxwidth-2,boxwidth-2]
	g.select(boxsel)
	g.shrink()
	if g.getselrect()==boxsel:
		continue
	else:
		clist=g.getcells(g.getselrect())
		sel=g.getselrect()
		for i in range(int(len(clist)/3)):
			clist[3*i]   = clist[3*i]-sel[0]
			clist[3*i+1] = clist[3*i+1]-sel[1]
		clist.insert(0,sel[2])
		clist.insert(1,sel[3])
		tile.append(clist)
		
		# tile.append(g.getcells(g.getselrect()))

if not tile==[]:
	if int(g.getstring("make new layer?","1")):
		try:
			newindex = g.addlayer()
			g.setlayer(newindex)
		except:
			g.show('too many layers')
		
	input=g.getstring('tilewidth','100')
	wd=int(input)
	
	input=g.getstring('tile to take e.g.: 1,5,7,8,.....','all')
	poslist=input.split(',')
	if len(poslist)==1:
		poslist=range(len(tile))
	else:
		for i in range(len(poslist)):
			poslist[i]=int(poslist[i])
	
	for j in range(len(poslist)):
		pos=poslist[j]
		i=tile[pos]
		make_text(str(pos+1)).put(wd*(j),0)
		boxsel =[wd * (j),boxwidth,wd,wd]
		g.select(boxsel)
		selrect = rect( g.getselrect() )
		# if selrect.empty: g.exit("There is no selection.")
		inc=2
		cliplist = i                    # 1st 2 items are wd,ht
		pbox = rect( [0, 0] + cliplist[0 : 2] )
		cliplist[0 : 2] = []                      # remove wd,ht
		p = pattern( cliplist )

		if len(cliplist) & 1 == 1: inc = 3        # multi-state?
		g.clear(inside)
		
		if len(cliplist) > 0:
			# tile selrect with p, clipping right & bottom edges if necessary
			y = selrect.top
			while y <= selrect.bottom:
				bottom = y + pbox.height - 1
				x = selrect.left
				while x <= selrect.right:
					right = x + pbox.width - 1
					if (right <= selrect.right) and (bottom <= selrect.bottom):
						p.put(x, y)
					else:
						clip_rb( p(x, y), selrect.right, selrect.bottom ).put()
					x += pbox.width
				y += pbox.height

		if not selrect.visible(): g.fitsel()		