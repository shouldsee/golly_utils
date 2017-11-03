import golly as g
stepmax=int(g.getstring('how many steps?','500'))
step=1;
while step<=stepmax:
	g.run(1)
	execfile('shuffle.py')
	g.update()
	step=step+1;


