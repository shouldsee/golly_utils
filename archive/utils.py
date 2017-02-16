import random
import golly as g

def popcount(sel=0):
	dict_lc={'BDRainbow':[2,4],'BGRainbowR2':[2,4]}
	rule=g.getrule().split(':')[0]
	try:
		live_cells=dict_lc[rule]
	except:
		live_cells=range(1,g.numstates())
	if not sel:
		clist=g.getcells(g.getrect())
	else:
		clist=g.getcells(g.getselrect())		
		return sum(clist[2::3].count(x) for x in live_cells)
	


def randfill(rectcoords, amt,amt2=100,secondary_state=1):
   statelist=[ g.getoption("drawingstate"),secondary_state]
   for i in range(rectcoords[0],rectcoords[0]+rectcoords[2]):
      for j in range(rectcoords[1],rectcoords[1]+rectcoords[3]):
         if(100*random.random()<amt):
     		newstate=(100*random.random()>amt2)
        	g.setcell(i, j, statelist[newstate])
         else:
            # g.setcell(i, j, 0)
			continue


def randtopo( num , low , high ):
	hashlist=[]
	topolist=[]
	arealist=[]
	i=0
	while i<num:
		size=random.choice(range(low,high+1))
		area=size*size
		sel=[size,size,size,size]
		g.new('')
		randfill(sel,(1+random.randrange(area))*int(100/area))
		if g.empty():
			continue
		h=g.hash(g.getrect())
		if h in hashlist:
			continue
		else:
			hashlist.append(h)
			pbox=g.getrect()
			actarea=pbox[2]*pbox[3]
			clist=g.getcells(g.getrect())
			g.store(clist,dir+'topo_area%i_hash%i'%(actarea,h))

			clist.insert(0,pbox[2])			#prepare for tiling
			clist.insert(1,pbox[3])
			topolist.append(clist)
			arealist.append(actarea)
			i=i+1
			continue
			return [topolist,hashlist,arealist]

def parse_list(clist):
	newlist=[]
	for i in range(len(clist[0::3])):
		if 3*i+3 <= len(clist):
			temp=clist[3*i:3*i+3]
			newlist.append(temp)
		else:
			break
	return(newlist)

	
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
