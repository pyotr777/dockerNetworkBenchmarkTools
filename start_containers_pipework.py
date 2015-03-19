#!/usr/bin/python

# Start containers
# and assign IPs with pipeworks

# First parameter - number of containers
# Second parameter - Docker image: iperf or ssh

import sys,subprocess,dockerlib

N = 2
IPbase = "10.0.0." 
create_cont = True
assign_IP = True
image_names={
    "ssh":"-p 22 peter/ssh",
    "iperf":"-p 22 -p 5001 peter/iperf"
}
image_key="ssh"

cont_names = []


if (len(sys.argv) > 1):
    N = int(sys.argv[1])
    if (N > 250):
	print "Can create max 250 containers.\n"
	sys.exit(0)

if (len(sys.argv) > 2):
	image_key = sys.argv[2]

image_name = image_names.get(image_key,"-p 22 peter/ssh")

if (create_cont):
    print "Creating " + str(N) + " containers from "+ image_name+ " image."
    command = image_name + " /usr/sbin/sshd -D"
    cont_longIDs=dockerlib.runContainers(N,command)

print cont_longIDs
print "ps"
subprocess.call(["docker","ps"])
    
cont_IDs = []  
if (cont_longIDs is None):
    cont_IDs = dockerlib.getContNames()
else:
    for cont_longID in cont_longIDs:
        cont_IDs.append(dockerlib.getContID(str(cont_longID)))

print "\n-------","\nIDs:",cont_IDs

if (assign_IP):    
    print "Assigning IP addresses"
       
    IPi = 0

    for cont_ID in cont_IDs:
        IP=IPbase+str(IPi+5)+"/24"
        print "./pipework.sh","br1",cont_ID,IP
        c = subprocess.Popen(["./pipework.sh","br1",cont_ID,IP],stdout=subprocess.PIPE)
        out, err = c.communicate()
        print out
        IPi += 1
        if (IPi > 250):
            print "Max 250 IPs limit reached."
            break
    
