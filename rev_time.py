

import random
import golly as g


#import replacer


def replace(rectcoords,map):
   for i in range(rectcoords[0],rectcoords[0]+rectcoords[2]):
      for j in range(rectcoords[1],rectcoords[1]+rectcoords[3]):
       		g.setcell(i, j, map[g.getcell(i,j)])



	
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

# if __name__=='__builtin__':
# 	default='0/1'
# 	IN=g.getstring('map?',default)
# 	replace_sel(IN)

replace_sel('0/2/1/3')