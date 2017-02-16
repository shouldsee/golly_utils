import random


def randfill(rectcoords, amt):
   newstate = g.getoption("drawingstate")
   for i in range(rectcoords[0],rectcoords[0]+rectcoords[2]):
      for j in range(rectcoords[1],rectcoords[1]+rectcoords[3]):
         if(100*random.random()<amt):
            g.setcell(i, j, newstate)
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

def popcount(sel=0):
	dict_lc={'BDRainbow':[2,4],'BGRainbowR2':[2,4]}
	live_cells=dict_lc[g.getrule().split(':')[0]]	
	if not sel:
		clist=g.getcells(g.getrect())
	else:
		clist=g.getcells(g.getselrect())		
		return sum(clist[2::3].count(x) for x in live_cells)
	

