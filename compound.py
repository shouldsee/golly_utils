import golly
s=golly.getstring('rules split by ";"',golly.getclipstr());
rs = [x for x in s.split(';') if x]
# golly.setrule(rs[0]);
L = len(rs)
for i in range(100):
	# golly.run(1)
	golly.step()
	golly.setrule(rs[i%L])
