# Output an adjacency matrix for current selection to clipborad in a "Mathematica" list fomart 
# Use AdjacencyGraph[] in Mathematica for downstream processing.
# Author: Feng Geng(shouldsee.gem@gmail.com), May 2016.

import golly as g
from glife import *

from collections import Counter
from glife.text import make_text
from time import time
import random
import math as m
import csv
import os
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

	
def parse_list(clist):
	newlist=[]
	for i in range(len(clist[0::3])):
		if 3*i+3 <= len(clist):
			temp=clist[3*i:3*i+3]
			newlist.append(temp)
		else:
			break
	return(newlist)

def adjacencymatrix(parsed_clist,pbox,torus=0,n=2):
	adjacencymatrix=[]
	if torus:
		adjacency_x=[0,1,pbox[2]*n-1]
		adjacency_y=[0,1,pbox[3]*n-1]
	else:
		adjacency_x=[0,1]
		adjacency_y=[0,1]
	# fclist=full_clist(parsed_clist,pbox)
	for i in parsed_clist:
		row=[]
		for j in parsed_clist:
			if 	i!=j and \
			(abs(i[0]-j[0]) in adjacency_x) and \
			(abs(i[1]-j[1]) in adjacency_y) and \
			[i[2],j[2]]==[state,state]:
				row.append(1)
			else:
				row.append(0)
				
		adjacencymatrix.append(row)
	return adjacencymatrix

def full_clist(parsed_clist,pbox):
	# if parsed_clist[0][0:2]!=pbox[0:2]:
		# parsed_clist.insert(0,[pbox[0],pbox[1],0])
	
	# left=pbox[0]
	# top=pbox[1]
	# right=left+pbox[2]-1
	# bottom=top+pbox[1]-1
	
	
	output=[]
	
	for i in [[x,y] for x in range(pbox[2]) for y in range(pbox[3])]:
		i[0]+=pbox[0]
		i[1]+=pbox[1]
		match=i[:]
		match.append(state)
		if match in parsed_clist:
			output.append(match)
		else:
			i.append(0)
			output.append(i)
	return output
	
	
	# for i in range(len(parsed_clist)):
		# c1=parsed_clist[i]
		# c2=parsed_clist[i+1]
		
		
		# if c1[:2]==[right,bottom]:
		
		# c1p=c1[:]
		
		
		# if c1[0]==pbox[0]+pbox[2]-1
		# c1p[0]=c1[0]

		# if y[0]==x[0]+1 or (y[0]==x[0]-pbox[2]+1 and y[1]==x[1]+1):
			# continue
		# else:
			# parsed_clist.insert(i+1,[x[0])
			

def mathematica(s):
	s=s.replace('[','{')
	s=s.replace(']','}')
	return s
def getquad(clist=[],pbox=[],n=2):
	newlist=[]
	# if not clist==[]:
	if not pbox==[]:
		clist=g.getcells(pbox)
	for i in range(len(clist[0::3])):
		if 3*i+3 <= len(clist):
			temp=clist[3*i:3*i+3]
			for x in [pbox[2]*i for i in range(n)]:
				for y in [pbox[3]*i for i in range(n)]:
					newlist.append(temp[0]+x)
					newlist.append(temp[1]+y)
					newlist.append(temp[2])

	newlist.append(0)
	return newlist

def makebox(boxwidth):
	box=[]
	for x in range(boxwidth):
		for y in range(boxwidth):
			if x in [0,boxwidth-1] or  y in [0,boxwidth-1] :
				for i in [x,y,1]:
					box.append(i)
		if len(box)%2 ==0: box.append(0)
	return pattern()

def loadtopo(maxnum,step,boxwidth):
	global pboxlist
	tile=[]
	for i in range(step,maxnum+step,step):
		make_text(str(i)).put(boxwidth*(i-1),0)
		box.put(boxwidth*(i-1),0)
		
		boxsel=[boxwidth*(i-1)+1,1,38,38]
		g.select(boxsel)
		g.shrink()
		if g.getselrect()==boxsel:
			continue
		else:
			sel=g.getselrect()
			pbox=g.getselrect()
			clist=g.getcells(pbox)
			
			
			for i in range(int(len(clist)/3)):
				clist[3*i]   = clist[3*i]-sel[0]
				clist[3*i+1] = clist[3*i+1]-sel[1]
			clist.insert(0,sel[2])
			clist.insert(1,sel[3])
			tile.append(clist)
			pboxlist.append(pbox)
	return tile

input=g.getstring('maxnum/step/boxwidth','100/1/40')
maxnum=int(input.split('/')[0])
step=int(input.split('/')[1])
boxwidth=int(input.split('/')[2])

input=g.getstring('what cell state to screen for/ \n \
			treat selection as torus?/ \n \
			how many repeating units?','%s/%s/%s'%(g.getoption("drawingstate"),'1','2'))
state=int(input.split('/')[0])
torus=int(input.split('/')[1])
n=int(input.split('/')[2])

# box=makebox(boxwidth)	
box=makebox(boxwidth)
pboxlist=[]
tile=loadtopo(maxnum,step,boxwidth)


adjmatlist=[]

for i in range(len(tile)):
	pbox=pboxlist[i]
	clist=getquad(pbox=pbox,n=n)
	g.setclipstr(str(clist))

	parsed_clist=parse_list(clist)
	g.show('clist %i %s,  parsed_clist %i %s'%(len(clist),str(clist),len(parsed_clist),str(parsed_clist))	)

	# fclist=full_clist(parsed_clist,pbox)		
	adjmat=adjacencymatrix(parsed_clist,pbox,torus,2)
	adjmatlist.append(adjmat)
s=mathematica(str(adjmatlist))
g.setclipstr(s)


