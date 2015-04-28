#!/usr/bin/python

# Setup OVS connections from containers to ovs-bridge interface on host machine
# and setup tunnel from ovs-bridge to remote host with given IP.
# Takes three parametes: container IP with net mask, remote IP without mask and OVS tunnel type

import sys, os, dockerlib

bridge = "ovs-bridge"
bridge_create = "ovs-vsctl --may-exist add-br "
bridge_remove = "ovs-vsctl --if-exists del-br "+bridge


usage = """Setup OVS connection from a container to ovs-bridge on host machine 
and setup tunnel from ovs-bridge to remote host with given IP. 
Parameters:  
    1. container IP with net mask, 
    2. remote host IP without mask         
    3. OVS tunnel type (gre, vxlan ...). Optional, default is gre."""

if (len(sys.argv) < 3):
    print usage
    sys.exit(1)

def setupOVS(bridge_create, bridge, port, tunnel_t, remoteIP):
    # Check that port not exists
    (exitcode, out, err) = dockerlib.run("ovs-vsctl show | grep -A 3 " +port,False)
    if (out is not None and len(out) > 2):
        print "Tunnel (OVS port) " + port + " already exists."
        print out
        return False

    (exitcode, contID, err) = dockerlib.run(bridge_create + bridge)
    if (exitcode > 0):
        print "Error creating bridge with command:" + bridge_create + bridge \
               + "\nExitcode (" + str(exitcode) + ")"
        if (err is not None and err != ""):
            print "Err: "+err
        sys.exit(1)
    else:
        print "Bridge " + bridge + " created"
        # Add port
        (exitcode, contID, err) = dockerlib.run("ovs-vsctl add-port " + bridge +
                                                " " + port + " -- set interface " +
                                                port + " type="+ tunnel_t + 
                                                " options:remote_ip=" + remoteIP)
        print "Tunnel " + port + " created."
        (exitcode, out, err) = dockerlib.run("ovs-vsctl show | grep -A 3 "+port)
        return True


fname="ovs_connect_container.sh"
if (not os.path.isfile(fname)):
    print "Need executable "+str(fname) +" in the same directory."
    sys.exit(1)
else:
    if (not os.access(fname, os.X_OK)):
        print "File "+str(fname) +" must be executable."
        sys.exit(1)

# Container IP        
contIP = sys.argv[1]
if (contIP.find("/") == -1):
    print "Container IP address must include a netmask. Maybe you meant "+contIP+ "/24 ?"
    sys.exit(1)

# Remote IP
remoteIP = sys.argv[2]

# Tunnel type
tunnel_t = "gre"   
if (len(sys.argv) > 3 and sys.argv[3] is not None) :
    tunnel_t = sys.argv[3]

# MTU
mtu = ""
if (tunnel_t == "gre"):
    mtu = "1462"
elif (tunnel_t == "vxlan"):
    mtu = "1450"

port = "ovs_"+tunnel_t
port_created = False

cont_name = "iperf"
cont_created = False

port_created = setupOVS(bridge_create, bridge, port, tunnel_t, remoteIP)

# Run container
print "Start container " + cont_name 
(exitcode, out, err) = dockerlib.run("docker run --name " + cont_name + " -p 22 -d pyotr777/iperf /usr/sbin/sshd -D")
if (exitcode > 0):
    if (err.find("is already in use by container") > 0):
        # Name is used
        # Delete old container
        dockerlib.run("docker rm $(docker kill " + cont_name + ")") 
        # Try again
        (exitcode, out, err) = dockerlib.run("docker run --name " + cont_name + " -p 22 -d pyotr777/iperf /usr/sbin/sshd -D")
        if (exitcode > 0):
            print "Error running container \nExitcode ("+str(exitcode)+ ")"
            if (err is not None and err != ""):
                print "Err: "+err
        else:
            cont_created = True
else:
    cont_created = True

# Setup OVS
print "Setup OVS for container " + cont_name 
command = "./ovs_connect_container.sh " + cont_name + " " + contIP + " " \
            + bridge + " " + mtu
(exitcode, out, err) = dockerlib.run(command)
if (exitcode > 0):
    print "Error running " + command + "\nExitcode ("+str(exitcode)+ ")"
    if (err is not None and err != ""):
        print "Err: "+err


ifremove=raw_input('Remove setup? (y/n) : ')

if ifremove == 'y':
    # Remove setup 
    if (cont_created):
        dockerlib.removeContOVS(cont_name)
    if (port_created):
        (exitcode, out, err) = dockerlib.run(bridge_remove)
        if (exitcode > 0):
            print "Error removing tunnel " + port + "\nExitcode ("+str(exitcode)+ ")"
        if (err is not None and err != ""):
            print "Err: "+err