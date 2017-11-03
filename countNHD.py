import os
import golly as g
#g.select(g.getrect())
oldrule=g.getrule()
i=0
g.autoupdate(0)
while i==0:
	g.run(1)
	g.save('temp','rle')
	g.setrule('S_input')
	g.run(1)
	cellindex=g.getlayer()
	execfile("histogram_2002_r75.py")
	histindex=g.getlayer()
	g.setlayer(cellindex)
	g.open('temp')
	g.setlayer(histindex)
	g.fit()
	g.update()
	g.setlayer(cellindex)
	i=+1
