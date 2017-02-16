# Output an adjacency matrix for current selection to clipborad in a "Mathematica" list fomart 
# Use AdjacencyGraph[] in Mathematica for downstream processing.
# Author: Feng Geng(shouldsee.gem@gmail.com), May 2016.

import golly as g
from glife import *
import numpy as np
import hashlib

def parse_list(clist):
	newlist=[]
	for i in range(len(clist[0::3])):
		if 3*i+3 <= len(clist):
			temp=clist[3*i:3*i+3]
			newlist.append(temp)
		else:
			break
	return(newlist)

	
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
			
def adjacencymatrix(parsed_clist,pbox,torus=0):
	adjacencymatrix=[]
	if torus:
		adjacency_x=[0,1,pbox[2]-1]
		adjacency_y=[0,1,pbox[3]-1]
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

def mathematica(s):
	s=s.replace('[','{')
	s=s.replace(']','}')
	return s

state=int(g.getstring('what cell state to screen for','%s'%g.getoption("drawingstate")))
torus=int(g.getstring('treat selection as torus? 1 for True','0'))

pbox=g.getselrect()
clist=g.getcells(pbox)

parsed_clist=parse_list(g.getcells(pbox))
adjmat=adjacencymatrix(parsed_clist,pbox,torus)
eigval=np.linalg.eigvalsh(adjmat)
eigval =np.round( eigval,decimals=1)
h=hash(tuple(eigval))
# a=eigval
# b = a.view(np.uint8)
# h=hashlib.sha1(b).hexdigest()
# h=hash(eigval)


s=mathematica(str(adjmat))
s='hash=%s,\n eigvall=%s, \n \n adjmat=%s'%(h,str(eigval),s)
g.show(s)


g.setclipstr(s)


