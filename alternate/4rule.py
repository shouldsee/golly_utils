# This script calculate and emulate a B0 composite from the current emulated rule. (Try B024/S0123 or B678/S1278)
# Author: Feng Geng(shouldsee.gem@gmail.com), Sep 2016.

import golly as g
from glife import *

rule=g.getrule()
rule=rule.split(':')[0]
rule=g.getstring('rule to alternate',rule)
numstep=int(g.getstring('number of steps to run','1000'))

#def makerule(b,s):
#	return(''.join)

ruleB=rule.split('/')[0][1:]
ruleS=rule.split('/')[1][1:]

S=['S']
B=['B']

beven=['B']
seven=['S']
bodd=['B']
sodd=['S']

for i in range(9):
	if i%2==0:
		if str(i) in ruleB:
			beven.append(str(i))
		if str(i) in ruleS:
			seven.append(str(i))
	if i%2==1:
		if str(i) in ruleB:
			bodd.append(str(i))
		if str(i) in ruleS:
			sodd.append(str(i))


rbeven=''.join(beven)
rseven=''.join(seven)
rbodd=''.join(bodd)
rsodd=''.join(sodd)
r1='/'.join([rbeven,rseven]);
r2='/'.join([rbodd,rseven]);
r3='/'.join([rbodd,rsodd]);
r4='/'.join([rbeven,rsodd]);
r=[r1,r2,r3,r4];
g.note(str(r))
gen=int(g.getgen());
gen0=gen;
while gen<numstep+gen0:
	gen=int(g.getgen());
	g.setrule(r[gen%4]);
	g.run(1)
	if gen%4==0:
		g.update()
	if g.empty():
		break


