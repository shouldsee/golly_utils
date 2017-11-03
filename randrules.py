import random
import golly;

numlst=[102,193,165,110,145,118,108,90,30,20,147,195,54];

namelst=['W'+str(rnum) for rnum in numlst];

stepnum=int(golly.getstring('how many steps?','500'))
for i in range(stepnum):
	name=namelst[random.randrange(len(namelst))];
	# name=namelst[i%len(numlst)];
	# golly.setalgo("RuleLoader")
	golly.setrule(name+':T200,0');
	golly.run(1)
	golly.update()