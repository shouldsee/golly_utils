## This script generate an ECA rule and emulate it on a torus of width 200. 
## Written by Feng (shouldsee.gem@gmail.com) Feb 2017.
import sys
import golly 

# 193,62,120
head='''@RULE %s
@TABLE
n_states:3
neighborhood:Moore
symmetries:none
var m=0
var p=2
var a={m,1}
var b={m,1}
var c={m,1}
var d={m,1}
var e={m,1}
var f={m,1}
var g={m,1}
var h={m,1}



m,p,p,m,m,m,f,g,p,%s
m,p,1,m,m,m,f,g,p,%s
m,1,p,m,m,m,f,g,p,%s
m,1,1,m,m,m,f,g,p,%s
m,p,p,m,m,m,f,g,1,%s
m,p,1,m,m,m,f,g,1,%s
m,1,p,m,m,m,f,g,1,%s
m,1,1,m,m,m,f,g,1,%s
1,a,b,d,e,f,g,h,c,1
p,a,b,d,e,f,g,h,c,p

''';
rnum=golly.getstring('ECA number','110');
name='W'+rnum;
file=golly.getdir("rules")+name+".rule"

r=bin(int(rnum));
r=r[:1:-1];
r+='0'*(8-len(r));
rule=r;
# rule=[0, 1, 1, 1, 1, 1, 0, 0];

dct=['p','1'];
with open(file,'w') as f:
	f.write(head%((name,)+tuple([dct[int(x)] for x in rule])));
golly.setalgo("RuleLoader")
golly.setrule(name+':T1000,0');
