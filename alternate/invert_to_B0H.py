# This script calculate and emulate a B0 composite from the current emulated rule. (Try B024/S0123 or B678/S1278)
# Author: Feng Geng(shouldsee.gem@gmail.com), Sep 2016.

import golly as g
from glife import *

rule=g.getrule()
rule=rule.split(':')[0]
rule=g.getstring('rule to alternate',rule)
ruleB=rule.split('/')[0][1:]
ruleS=rule.split('/')[1][1:]
S=['S']
B=['B']
for i in range(7):
	if str(i) in ruleB:
		S.append(str(6-int(i)))
	if str(i) in ruleS:
		B.append(str(6-int(i)))

B=''.join(B)
S=''.join(S)
rule='/'.join([B,S])
rule=''.join([rule,'H'])
# g.note(rule)
g.setrule(rule)
