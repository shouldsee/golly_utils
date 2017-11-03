# Output an adjacency matrix for current selection to clipborad in a "Mathematica" list fomart 
# Use AdjacencyGraph[] in Mathematica for downstream processing.
# Author: Feng Geng(shouldsee.gem@gmail.com), May 2016.

import golly as g
from glife import *

	
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
def getquad(pbox,n=2):
	newlist=[]
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


input=g.getstring('what cell state to screen for/ \n \
			treat selection as torus?/ \n \
			how many repeating units?','%s/%s/%s'%(g.getoption("drawingstate"),'1','2'))

state=int(input.split('/')[0])
torus=int(input.split('/')[1])
n=int(input.split('/')[2])

pbox=g.getselrect()
clist=getquad(pbox,n=n)
g.setclipstr(str(clist))

parsed_clist=parse_list(clist)
g.show('clist %i %s,  parsed_clist %i %s'%(len(clist),str(clist),len(parsed_clist),str(parsed_clist))	)

fclist=full_clist(parsed_clist,pbox)		
adjmat=adjacencymatrix(parsed_clist,pbox,torus,n=n)
s=mathematica(str(adjmat))
g.setclipstr(s)


