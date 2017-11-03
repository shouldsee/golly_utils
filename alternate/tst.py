# Output an adjacency matrix for current selection to clipborad in a "Mathematica" list fomart 
# Use AdjacencyGraph[] in Mathematica for downstream processing.
# Author: Feng Geng(shouldsee.gem@gmail.com), May 2016.

# import golly as g
# # from glife import *
# import numpy as np
# import hashlib

rule='b3s23';
r=rule.lstrip('b');
ruleB,ruleS=r.split('s');
ruleS=ruleS.lstrip('s');

B='';
S='';
for i in range(9):
	if not str(i) in ruleB:
		S+=(str(8-int(i)))
	if not str(i) in ruleS:
		B+=(str(8-int(i)))
# B=B[::-1];
# S=S[::-1];
irule='b{}s{}'.format(B,S);
# g.note(rule)
print(B)
print(irule)