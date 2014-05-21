# get average from iperf connection tests

import sys, math, string

if (len(sys.argv) > 1):
    file = sys.argv[1]
else:
    print "Need file name with results"
    sys.exit(1)

f = open(file,'r')
text = f.read()
#print text
lines = text.split("\n")
data=[]
for line in lines:
    if line.find("/sec") >= 0 and line.find("[SUM]") < 0 :
        parts=line.split(" ")
        try:
            data.append(float(parts[11]))
        except IndexError:
            pass
f.close()
#print data
sum = 0
for v in data:
    sum = sum + v

if len(data) <= 0:
    print "No data"
    sys.exit(1)
avg = sum / len(data)
print math.floor(avg*100)/100