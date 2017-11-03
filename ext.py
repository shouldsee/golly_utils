f=open('lst.txt','r');
outf=open('lst_out','w');
for line in f.readlines():
	outf.write('\'{}\''.format(line.split('.')[-2])+'\n');