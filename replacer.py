import random
import golly as g




def replace(rectcoords,map):
   for i in range(rectcoords[0],rectcoords[0]+rectcoords[2]):
      for j in range(rectcoords[1],rectcoords[1]+rectcoords[3]):
       		g.setcell(i, j, map[g.getcell(i,j)])



# rule=g.getrule().split(':')[0]
# map_dc={'BGRainbowR2':'0/1/2/3/4/5/6'}
# if rule in map_dc:
# 	default=map_dc[rule]
# else:
# 	default='0/1'

	
def replace_sel(IN,):
	od=IN.split('/')
	od = [int(x) for x in od]
	sel=(g.getselrect()!=[])

	if g.empty():
		g.show('universe is empty')
	else:
		if sel:
			replace(g.getselrect(),od)
		else:
			replace(g.getrect(),od)
if __name__=='__builtin__':
	default='0/1'
	IN=g.getstring('map?',default)
	replace_sel(IN)