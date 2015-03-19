#!/usr/bin/python

# Start containers
# and create external IP addresses with iptables and DHCP.
# Parameters:
# 1st - number of containers to create


import sys,subprocess,dockerlib


N = 10
create_cont = True
make_br = True
add_routing = True
image_name="peter/iperf"

if (len(sys.argv) > 1):
    N = int(sys.argv[1])

cont_longIDs=[]

if (create_cont):
    print "Creating " + str(N) + " containers."
    command = "-p 22 -p 5001 "+image_name+" /usr/sbin/sshd -D"
    cont_longIDs=dockerlib.runContainers(N,command)

if (create_cont and len(cont_longIDs) < 1):
    sys.exit("No containers created. Exiting")

cont_names = []
if (cont_longIDs is None):
    cont_names = dockerlib.getContNames()
else:
    for cont_longID in cont_longIDs:
        cont_name=dockerlib.getContName(str(cont_longID))
        print cont_name+" \t: \t" + cont_longID
        cont_names.append(cont_name)

if (make_br):    
    print "Assigning IP addresses"
    
    for cont_ID in cont_names:
        if (cont_ID is None):
            continue
        print "Bridge for " + str(cont_ID)
        br_name=dockerlib.getBridgeName(cont_ID)
        print br_name
        subprocess.call(["./ip.sh",br_name])
        
for cont_ID in cont_names:
    br_name = dockerlib.getBridgeName(cont_ID)
    c = subprocess.Popen(["./getip.sh",br_name],stdout=subprocess.PIPE)
    CIDR, err = c.communicate()
    extip = CIDR.split("/")[0]
    intip = dockerlib.getInternalIP(cont_name)
    print cont_ID+ " : "+ extip + " - " + intip
    
    if (add_routing):
        if (extip is None):
            print "No ext IP for "+ cont_ID
        elif (intip is None):
            print "No int IP for " + cont_ID
        else :    
            subprocess.call(["./iptables.sh",cont_ID,extip,intip])
