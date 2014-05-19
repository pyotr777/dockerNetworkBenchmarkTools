# Clear docker ip settings
# Remove interfaces (br_...)
# Kill containers
# Remove stopped containers

# Can be used as:
# clean_containers.py cont_name1 ... cont_name2
# or as:
# clean_containers.py cont_name externalIP internalIP


import subprocess, re, sys, dockerlib


# Container names
cont_names=[]

if (len(sys.argv) > 1):
    cont_names = sys.argv[1:]
    print cont_names
else:
    # Get names of running containers
    cont_names = dockerlib.getContNames()
    print "Running containers: ", cont_names

def cleanContainers(cont_names):
    clean_routing = True
    remove_devices = True
    stop_containers = True
    remove_containers = True

    for cont_name in cont_names:
        m = re.match("\d+\.\d+\.\d+\.\d+",cont_name)
        if (m is not None):
            # Have IP address, not container name
            continue
        cont_ID=dockerlib.getContID(str(cont_name))
        if (cont_ID is None):
            # Probably we have container ID in command line parameters
            cont_ID = cont_name
        print "ID: "+ str(cont_ID)
        extip = dockerlib.getExternalIP(cont_ID)
        intip = dockerlib.getInternalIP(cont_ID)
        print cont_ID+ " - "+ str(extip) + " - " + str(intip)
            
        if (clean_routing):
            if (extip is None):
                print "No ext IP for "+ cont_name
                if (len(sys.argv) > 2):
                    ip = sys.argv[2]
                    m = re.match("\d+\.\d+\.\d+\.\d+",ip)
                    if (m is not None):
                        print "Use external IP "+ ip
                        extip = ip
            if (intip is None):
                print "No int IP for " + cont_name
                if (len(sys.argv) > 3):
                    ip = sys.argv[3]
                    m = re.match("\d+\.\d+\.\d+\.\d+",ip)
                    if (m is not None):
                        print "Use internal IP "+ ip
                        intip = ip
            if (extip is not None and intip is not None) :
                print "Clean iptables"
                subprocess.call(["./iptablesclean.sh",cont_ID,extip,intip])
            
    if (remove_devices):
        dockerlib.removeInterfaces([cont_ID])

        
    if (stop_containers):
        for cont_name in cont_names:
            print "Kill "+ cont_name
            subprocess.call(dockerlib.docker_api+["kill",cont_name])
    if (remove_containers):
        for cont_name in cont_names:
            print "Remove "+ cont_name
            subprocess.call(dockerlib.docker_api+["rm",cont_name])


cleanContainers(cont_names)