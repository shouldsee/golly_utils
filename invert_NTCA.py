## This script generate an ECA rule and emulate it on a torus of width 200. 
## Written by Feng (shouldsee.gem@gmail.com) Feb 2017.
import golly
import copy
alias=golly.getstring('NTCA alias',golly.getrule().split(':')[0]);
try:
	post=golly.getrule().split(':')[1];
except:
	post='';
	
ali=alias;
# rule='0'*102;

henseldict=['b0_','b1c','b1e','b2a','b2c','b3i','b2e','b3a','b2k','b3n','b3j','b4a','s0_','s1c','s1e','s2a','s2c','s3i','s2e','s3a','s2k','s3n','s3j','s4a','b2i','b3r','b3e','b4r','b4i','b5i','s2i','s3r','s3e','s4r','s4i','s5i','b2n','b3c','b3q','b4n','b4w','b5a','s2n','s3c','s3q','s4n','s4w','s5a','b3y','b3k','b4k','b4y','b4q','b5j','b4t','b4j','b5n','b4z','b5r','b5q','b6a','s3y','s3k','s4k','s4y','s4q','s5j','s4t','s4j','s5n','s4z','s5r','s5q','s6a','b4e','b5c','b5y','b6c','s4e','s5c','s5y','s6c','b5k','b6k','b6n','b7c','s5k','s6k','s6n','s7c','b4c','b5e','b6e','s4c','s5e','s6e','b6i','b7e','s6i','s7e','b8_','s8_',];
   # henseldict=['b0_','b1c','b1e','b2a','b2c','b3i','b2e','b3a','b2k','b3n','b3j','b4a','s0_','s1c','s1e','s2a','s2c','s3i','s2e','s3a','s2k','s3n','s3j','s4a','b2i','b3r','b3e','b4r','b4i','b5i','s2i','s3r','s3e','s4r','s4i','s5i','b2n','b3c','b3q','b4n','b4w','b5a','s2n','s3c','s3q','s4n','s4w','s5a','b3y','b3k','b4k','b4y','b4q','b5j','b4t','b4j','b5n','b4z','b5r','b5q','b6a','s3y','s3k','s4k','s4y','s4q','s5j','s4t','s4j','s5n','s4z','s5r','s5q','s6a','b4e','b5c','b5y','b6c','s4e','s5c','s5y','s6c','b5k','b6k','b6n','b7c','s5k','s6k','s6n','s7c','b4c','b5e','b6e','s4c','s5e','s6e','b6i','b7e','s6i','s7e','b8_','s8_',];
# henseldict=['s8_','s7c','s7e','s6a','s6c','s5i','s6e','s5a','s6k','s5n','s5j','s4a','b8_','b7c','b7e','b6a','b6c','b5i','b6e','b5a','b6k','b5n','b5j','b4a','s6i','s5r','s5e','s4r','s4i','s3i','b6i','b5r','b5e','b4r','b4i','b3i','s6n','s5c','s5q','s4n','s4w','s3a','b6n','b5c','b5q','b4n','b4w','b3a','s5y','s5k','s4k','s4y','s4q','s3j','s4t','s4j','s3n','s4z','s3r','s3q','s2a','b5y','b5k','b4k','b4y','b4q','b3j','b4t','b4j','b3n','b4z','b3r','b3q','b2a','s4e','s3c','s3y','s2c','b4e','b3c','b3y','b2c','s3k','s2k','s2n','s1c','b3k','b2k','b2n','b1c','s4c','s3e','s2e','b4c','b3e','b2e','s2i','s1e','b2i','b1e','s0_','b0_']
invhenseldict=['s8_','s7c','s7e','s6a','s6c','s5i','s6e','s5a','s6k','s5n','s5j','s4a','b8_','b7c','b7e','b6a','b6c','b5i','b6e','b5a','b6k','b5n','b5j','b4a','s6i','s5r','s5e','s4n','s4t','s3i','b6i','b5r','b5e','b4n','b4t','b3i','s6n','s5c','s5q','s4r','s4q','s3a','b6n','b5c','b5q','b4r','b4q','b3a','s5y','s5k','s4k','s4j','s4w','s3j','s4i','s4y','s3n','s4z','s3r','s3q','s2a','b5y','b5k','b4k','b4j','b4w','b3j','b4i','b4y','b3n','b4z','b3r','b3q','b2a','s4c','s3c','s3y','s2c','b4c','b3c','b3y','b2c','s3k','s2k','s2n','s1c','b3k','b2k','b2n','b1c','s4e','s3e','s2e','b4e','b3e','b2e','s2i','s1e','b2i','b1e','s0_','b0_']
#henselproj=[101,89,99,73,81,35,95,47,87,69,66,23,100,85,97,60,77,29,92,41,83,56,53,11,98,71,94,33,34,17,96, 58, 91, 27, 28, 5, 88, 79, 72, 45, 46, 19, 84, 75, 59, 39, 40, 7, 80, 86, 63, 64, 65, 22, 67, 68, 21, 70, 31, 44, 15, 76, 82, 50, 51, 52, 10, 54, 55, 9, 57, 25, 38, 3, 78, 43, 61, 16, 74, 37, 48, 4, 62, 20, 42, 13, 49, 8, 36, 1, 93, 32, 18, 90, 26, 6, 30, 14, 24, 2, 12, 0];
# henselproj=list(henseldict.index(x) for x in invhenseldict)
henselproj=[101, 89, 99, 73, 81, 35, 95, 47, 87, 69, 66, 23, 100, 85, 97, 60, 77, 29, 92, 41, 83, 56, 53, 11, 98, 71, 94, 45, 67, 17, 96, 58, 91, 39, 54, 5, 88, 79, 72, 33, 65, 19, 84, 75, 59, 27, 52, 7, 80, 86, 63, 68, 46, 22, 34, 64, 21, 70, 31, 44, 15, 76, 82, 50, 55, 40, 10, 28, 51, 9, 57, 25, 38, 3, 93, 43, 61, 16, 90, 37, 48, 4, 62, 20, 42, 13, 49, 8, 36, 1, 78, 32, 18, 74, 26, 6, 30, 14, 24, 2, 12, 0]


# invhenseldict=[];
# inv={'b':'s','s':'b'};
# invsub={'c':'e','e':'c','k':'k','a':'a','i':'t','t':'i','n':'r','r':'n','y':'j','j':'y','q':'w','w':'q','z':'z'};
# for v in henseldict:
# 	if v[1]=='4':
# 		end=invsub[v[2]];
# 	else:
# 		end=v[2]
# 		pass
# 	k=inv[v[0]]+str(8-int(v[1]))+end;
# 	invhenseldict.append(k);


henselidx={k: v for v, k in enumerate(henseldict)};
subconf='_cekainyqjrtwz';

def add_all(s,prime,sold,neg=0):
	for c in subconf:
		conf=prime+sold+c;
		try:
			s[henselidx[conf]]=str(1-neg);
		except KeyError:
			pass	
class rule():
	def __init__(self,dgt):
		self.s=list('0'*dgt);
	def add(self,ali):
		ali=ali.replace('/','').lower();
		if len(self.s)==102:
			while True:
				prime=ali[0];

				ali=ali[1:];
				sold=[];
				# sold=ali[0];
				# nold=
				neg=0;
				for i,s in enumerate(ali):
					if s.isdigit():	
						neg=0;		
						if sold==[]:
							pass
						elif sold.isdigit():
							add_all(self.s,prime,sold);
							# golly.note('added all of '+prime+sold)
						nold=s;
						
					elif s in ['b','s']:
						ali=ali[i:];
						break
					elif s=='-':
						neg=1;
						add_all(self.s,prime,nold);
						# golly.note('added all of '+prime+sold)
					else:
						conf=prime+nold+s;
						self.s[henselidx[conf]]=str(1-neg);
						# golly.note('added '+conf)
					alii=ali[i+1:];
					sold=s;
					# golly.note(alii)	
				if sold.isdigit():
					add_all(self.s,prime,sold);
					# golly.note('added all of '+prime+s)
				if i+1==len(ali):
					break
			self.rstr=''.join(self.s[::-1]);
			self.rnum=hex(int(self.rstr,2)).lstrip('0x').rstrip('L').zfill(26);
			self.alias=rule2alias(self.s);
	def inverse(self):
		# s=[0]*102;
		# for i,k in enumerate(self.s):
		# 	val=str(1-int(k));
		# 	s[henseldict.index(invhenseldict[i])]=val;	
		# 	# s[henselproj[i]]=str(1-int(k))
		# 	# val=str(int(self.s[henselproj[i]]));
		# 	# s.append(val);
		self.s=list(str(1-int(self.s[henselproj[i]])) for i,k in enumerate(self.s));
		# self.s=s;
		self.rstr=''.join(self.s[::-1]);
		self.rnum=hex(int(self.rstr,2)).lstrip('0x').rstrip('L').zfill(26);
		self.alias=rule2alias(self.s);
def rule2alias(rlst):
	alias='';
	rlst=[i for i,x in enumerate(rlst) if x=='1'];
	others=[];
	# ps=1;
	primed=0;
	for i in rlst:
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
	# golly.note(str(alias))
	
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
	return alias

		

r1=rule(102);
r1.add(alias);
r1.inverse();
rstr=r1.alias+':'+post;
# golly.note(rstr);
golly.setrule(rstr);
# s=''.join(rule.s[::-1]);
# r=hex(int(s,2)).rstrip('L');
# r2=copy.deepcopy(r1);
# r2.inverse();
# golly.note(str(r1.rnum)+' \n'+r1.rstr+'\n'+r1.alias+'\n'+r2.alias+'\n'+r2.rnum)
# golly.note(str(r1.alias))
# print(r)

# B2ei3eikqry4ceknty5aciknq6aein7c/S2cen3-iqr4aqwz5-inr6cikn7c
# B2ei3-acjn4ceknty5-ejry6-ck7c8/S01c2cen3-iqr4aqwz5-inr6-ae78
# B2ae3inr4-aqwz5iqr6aik7e/S1e2ck3ejry4aijqrwz5acjn6ackn78
# s876-ae5-inr4aqwz3-iqr2-aik7-e8/b87-e6-ck5-ejry4-aijqrwz3-acjn2-ackn

# B2ei3eikqry4ceknty5aciknq6aein7c8/S2cen3-iqr4aqwz5-inr6cikn7c8

# b3s23
# s87643210
# # asc=ord(rnum)
# lst=list([x=='-' for x in  rnum]);
# # golly.note(str(lst))
# # golly.note(rnum)
# # golly.note(str(~sum(lst)));
# if sum(lst)==0:
# 	pass
# else:
# 	rnum=rnum.split('/')[-1].split('-')[1]
# 	# golly.note(str(lst2))
# r0=bin(int(rnum,16))[2:].zfill(102);
# # golly.note(str(len(r0)));
# # golly.setclipstr((r0));
# # golly.note('copied')
# r=r0[::-1];


# rule=[i for x,i in zip(r,range(len(r))) if x=='1'];

# rs=[];

# alias='';

# others=[];
# # ps=1;
# primed=0;
# for i in rule:
# 	s=henseldict[i];
# 	alias=alias.rstrip('_');

# 	if primed:
# 		if s[0]==sold[0]:
# 			if s[1]==sold[1]:
# 				alias+=s[2]
# 			else:
# 				alias+=s[1:];
# 				primed=1;
# 		else:
# 			others.append(s);
# 			# pass
# 			# break
# 			continue
# 	else:
# 		alias+=s;
# 		primed=1;
# 	sold=s;
# alias=alias.rstrip('_');

# primed=0;
# for s in others:
# 	alias=alias.rstrip('_');
# 	if primed:
# 		if s[0]==sold[0]:
# 			if s[1]==sold[1]:
# 				alias+=s[2]
# 			else:
# 				alias+=s[1:];
# 				primed=1;
# 		else:
# 			others.append(s);
# 			# pass
# 			# break
# 			continue
# 	else:
# 		alias+=s;
# 		primed=1;
# 	sold=s;
# alias=alias.rstrip('_');
	
# 	# alias+=str((a)%9)
# # if ps==1:
# # 	alias+='s';


# golly.setalgo("QuickLife")
# # golly.note(alias)
# golly.setrule(alias);
# golly.setclipstr('\n'+alias);