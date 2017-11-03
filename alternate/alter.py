import golly as g
stepmax=int(g.getstring('how many steps?','500'))
rule1=g.getstring('first rule',g.getrule());
rule2=g.getstring('2nd rule',g.getrule());

step=1;
while step<=stepmax:
	g.setrule([rule1,rule2,rule2][int(g.getstep())%3])
	g.run(1)
	# execfile('shuffle.py')
	g.update()
	step=step+1;


