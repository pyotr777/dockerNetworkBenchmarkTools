# get average from iperf connection tests

import sys, math

if (len(sys.argv) > 1):
    file = sys.argv[1]
else:
    print "Need file name with results"
    sys.exit(1)

f = open(file,'r')
lines = f.readlines()
data=[]
for line in lines:
    str="/sec"
    if line.find(str) >= 0:
        parts=line.split(" ")
        data.append(float(parts[11]))
f.close()
# print data
sum = 0
for v in data:
    sum = sum + v

if len(data) <= 0:
    print "No data"
    sys.exit(1)
avg = sum / len(data)
print math.floor(avg*100)/100