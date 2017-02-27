## This script generate an ECA rule and emulate it on a torus of width 200. 
## Written by Feng (shouldsee.gem@gmail.com) Feb 2017.
import golly

rnum=golly.getstring('NTCA number',golly.getclipstr());
# asc=ord(rnum)
lst=list([x=='-' for x in  rnum]);
# golly.note(str(lst))
# golly.note(rnum)
# golly.note(str(~sum(lst)));
if sum(lst)==0:
	pass
else:
	rnum=rnum.split('/')[-1].split('-')[1]
	# golly.note(str(lst2))
r0=bin(int(rnum,16))[2:].zfill(102);
# golly.note(str(len(r0)));
# golly.setclipstr((r0));
# golly.note('copied')
r=r0[::-1];

henseldict=['b0_','b1c','b1e','b2a','b2c','b3i','b2e','b3a','b2k','b3n','b3j','b4a','s0_','s1c','s1e','s2a','s2c','s3i','s2e','s3a','s2k','s3n','s3j','s4a','b2i','b3r','b3e','b4r','b4i','b5i','s2i','s3r','s3e','s4r','s4i','s5i','b2n','b3c','b3q','b4n','b4w','b5a','s2n','s3c','s3q','s4n','s4w','s5a','b3y','b3k','b4k','b4y','b4q','b5j','b4t','b4j','b5n','b4z','b5r','b5q','b6a','s3y','s3k','s4k','s4y','s4q','s5j','s4t','s4j','s5n','s4z','s5r','s5q','s6a','b4e','b5c','b5y','b6c','s4e','s5c','s5y','s6c','b5k','b6k','b6n','b7c','s5k','s6k','s6n','s7c','b4c','b5e','b6e','s4c','s5e','s6e','b6i','b7e','s6i','s7e','b8_','s8_',];

rule=[i for x,i in zip(r,range(len(r))) if x=='1'];

rs=[];

alias='';

others=[];
# ps=1;
primed=0;
for i in rule:
	s=henseldict[i];
	alias=alias.rstrip('_');

	if primed:
		if s[0]==sold[0]:
			if s[1]==sold[1]:
				alias+=s[2]
			else:
				alias+=s[1:];
				primed=1;
		else:
			others.append(s);
			# pass
			# break
			continue
	else:
		alias+=s;
		primed=1;
	sold=s;
alias=alias.rstrip('_');

primed=0;
for s in others:
	alias=alias.rstrip('_');
	if primed:
		if s[0]==sold[0]:
			if s[1]==sold[1]:
				alias+=s[2]
			else:
				alias+=s[1:];
				primed=1;
		else:
			others.append(s);
			# pass
			# break
			continue
	else:
		alias+=s;
		primed=1;
	sold=s;
alias=alias.rstrip('_');
	
	# alias+=str((a)%9)
# if ps==1:
# 	alias+='s';


golly.setalgo("QuickLife")
# golly.note(alias)
curr=golly.getrule().split(':');
if len(curr)>1:
	curr=':'+curr[1];
else:
	curr='';

golly.setrule(alias+curr);
golly.setclipstr('\n'+alias);