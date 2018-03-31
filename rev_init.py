## Written by Feng (shouldsee.gem@gmail.com) March 2018.
import golly
import KBs

import random,re,os


# rulestr=golly.getstring('NTCA number',golly.getclipstr()).split('_')[-1];
kb = KBs.kb_2dntca()
# alias = golly.getrule()
prefix,curr,suffix = KBs.interpret(golly.getrule().split(':'))
prefix = 'rev_'


rulestr = kb.alias2rulestr(curr)
# bitstr = KBs.hex2bin(rulestr,102)
# # assert KBs.bin2hex(bitstr)==rulestr
# bitlst = list(bitstr)
# idx =  random.randrange(102)
# flip = {'0':'1','1':'0'}
# bitlst[idx] = flip[bitlst[idx]]
# rulestr = KBs.bin2hex(''.join(bitlst))
alias = kb.rulestr2alias(rulestr)


if 1:
	DIR=golly.getdir('rules')
	fname = os.path.join(DIR,prefix+alias+'.rule')	
	with open(fname,'w') as f:
		print >>f,kb.rulestr2table(rulestr,reverse=1)
newrule ='%s%s:%s'%(prefix,alias,suffix)
golly.note(newrule)
golly.setclipstr(newrule.split(':')[0])

golly.setrule(newrule)
