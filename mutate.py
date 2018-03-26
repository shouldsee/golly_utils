## Written by Feng (shouldsee.gem@gmail.com) March 2018.
import golly
import KBs
import random


# rulestr=golly.getstring('NTCA number',golly.getclipstr()).split('_')[-1];
kb = KBs.kb_2dntca()
# alias = golly.getrule()
curr=golly.getrule().split(':')
if len(curr)==1:
	curr+=['']
alias,suffix = curr

rulestr = kb.alias2rulestr(alias)
bitstr = KBs.hex2bin(rulestr,102)
# assert KBs.bin2hex(bitstr)==rulestr
bitlst = list(bitstr)

idx =  random.randint(0,102)
flip = {'0':'1','1':'0'}
bitlst[idx] = flip[bitlst[idx]]
rulestr = KBs.bin2hex(''.join(bitlst))
alias = kb.rulestr2alias(rulestr)


golly.note(alias)
golly.setclipstr(alias)

golly.setrule('%s:%s'%(alias,suffix))
