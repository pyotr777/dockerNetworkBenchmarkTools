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

dockerlib.cleanContainers(cont_names)