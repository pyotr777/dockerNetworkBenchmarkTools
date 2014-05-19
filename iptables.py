# Assign external IP (fixed or with DHCP) address with iptables.
# Parameters:
# 1st - container ID
# 1st - IP address with mask or "dhcp"


import sys,subprocess,dockerlib

make_br = True
add_routing = True
use_dhcp = False

IP = "0.0.0.0/24"

if (len(sys.argv) < 3):
    print "Provide container ID and IP address or 'dhcp'"
    sys.exit(1)

if (len(sys.argv) >= 3):
    cont_name = sys.argv[1]
    if (sys.argv[2]=="dhcp"):
        use_dhcp = True
    else:
        IP = sys.argv[2]

if (use_dhcp):
    IPa = "DHCP"
else:
    IPa = IP

cont_ID=dockerlib.getContID(str(cont_name))
# print cont_ID+" \t: \t" + cont_name

if (make_br):    
    print "Assigning " +IPa+ " to container " + cont_name
    
    br_name=dockerlib.getBridgeName(cont_ID)
    # Create virtual network interface for assigning external IP address to Docker container
    subprocess.call(["./create_macvlan.sh",br_name])

    if (use_dhcp):
        subprocess.call(["./dhclient","-v",br_name])        
        c = subprocess.Popen(["./getip.sh",br_name],stdout=subprocess.PIPE)
        CIDR, err = c.communicate()
        extip = CIDR.split("/")[0]
    else:
        command_s = "ip addr add "+IP+" dev "+br_name
        command_l = command_s.split()
        subprocess.call(command_l) 
        extip = IP

    intip = dockerlib.getInternalIP(cont_ID)
    print cont_ID+ " : "+ extip + " - " + intip
    
    if (add_routing):
        if (extip is None):
            print "No ext IP for "+ cont_ID
        elif (intip is None):
            print "No int IP for " + cont_ID
        else :    
            subprocess.call(["./iptables.sh",cont_ID,extip,intip])
