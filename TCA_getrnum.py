## This script generate an ECA rule and emulate it on a torus of width 200. 
## Written by Feng (shouldsee.gem@gmail.com) Feb 2017.
import golly

ali=golly.getstring('TCA rulestring',golly.getrule().split(':')[0])




def alias2rnum(ali):
	rule=['0']*18;
	ali=ali.replace('/','').lower().lstrip('b');
	(b,s)=ali.split('s');
	lst=list(str(int(i)+9) for i in s);
	golly.note(str(lst))
	bs=list(b)+(lst)
	for i in bs:
		rule[int(i)]='1';
	# golly.note(bs)
	# golly.note(''.join(rule[::-1]))
	rnum=int(''.join(rule[::-1]),2);
	return(rnum);
# golly.setalgo("QuickLife")
# # golly.note(alias)
# golly.setrule(alias);
rnum=str(alias2rnum(ali));
golly.setclipstr(rnum);
golly.note(rnum)