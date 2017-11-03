## This script generate an ECA rule and emulate it on a torus of width 200. 
## Written by Feng (shouldsee.gem@gmail.com) Feb 2017.
import golly
import KBs
rulestr=golly.getstring('NTCA number',golly.getclipstr()).split('_')[-1];
alias = KBs.kb_2dntca().rulestr2alias(rulestr)
golly.note(alias)
curr=golly.getrule().split(':');
if len(curr)>1:
	curr=':'+curr[1];
else:
	curr='';
golly.setalgo("QuickLife")
golly.setrule(alias+curr);
golly.setclipstr('\n'+alias);