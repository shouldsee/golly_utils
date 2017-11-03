## This script generate an ECA rule and emulate it on a torus of width 200. 
## Written by Feng (shouldsee.gem@gmail.com) Feb 2017.
import golly
rnum=golly.getstring('TCA number','6152');




r=bin(int(rnum));
r=r[:1:-1];
r+='0'*(18-len(r));

rule=[i for x,i in zip(r,range(len(r))) if x=='1'];

alias='b';

ps=1;
for a in rule:
	if a>8 and ps:
		alias+='s';
		ps=0;
	alias+=str((a)%9)
if ps==1:
	alias+='s';


golly.setalgo("QuickLife")
# golly.note(alias)
golly.setrule(alias);
golly.setclipstr('\n'+rnum);