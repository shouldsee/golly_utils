## Written by Feng (shouldsee.gem@gmail.com) Feb 2017.
import golly
import KBs
# rulestr=golly.getstring('NTCA number',golly.getclipstr()).split('_')[-1];
alias = golly.getrule()
rulestr = KBs.kb_2dntca().alias2rulestr(alias)
bitstr = KBs.hex2bin(rulestr,102)
# .lstrip('0b')

# golly.note('%s'%len(bitstr))

import random
idx =  random.randint(0,102)
bitlst = list(bitstr)
dct = {'0':'1','1':'0'}
bitlst[idx] = dct[bitlst[idx]]
# golly.note(''.join(bitlst))

bitstr = ''.join(bitlst)
rulestr = hex(int(bitstr,2)).lstrip('0x').rstrip('L').zfill(26)
alias = KBs.kb_2dntca().rulestr2alias(rulestr)
# alias = KBs.kb_2dntca().rulestr2alias(rulestr)
golly.note(alias)
curr=golly.getrule().split(':');
if len(curr)>1:
	curr=':'+curr[1];
else:
	curr='';
golly.setalgo("QuickLife")
golly.setrule(alias+curr);
golly.setclipstr('\n'+alias);

