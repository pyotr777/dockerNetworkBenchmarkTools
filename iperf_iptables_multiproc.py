#!/usr/bin/python

# Tests connection performance between containers with iperf.
# First parameter (S) - number of servers.
# Second parameter (N) - number of containers.
# Third parameter (L) - number of processes per client container.
# Start containers: S with iperf server, N with iperf clients.
# Assign IPs with iptables: 10.0.0.3/24,... first to servers, then to clients.

# 1st clent connects to 1 server, 
# S-th client connects to S-th server, (S+1)-th client connects to 1st server, etc.

import sys,dockerlib,time,math

S = 2
N = 2
L = 1
IPbase = "10.0.0." 
start_iplow = 3  # lower number in IP address of the server
image_name = "peter/iperf"  # This image with iperf installed must exist
server_image="peter/iserv"  # These two images will be created
client_image="peter/iclient"
measure_time = 7
client_startup_delay = 8  # Delay for assigning IP addresses to client container 
clinet_PIDs=[]

if (len(sys.argv) > 1):
    S = int(sys.argv[1])
	   
if (len(sys.argv) > 2):
    N = int(sys.argv[2])

if (len(sys.argv) > 3):
    L = int(sys.argv[3])

if (S + N > 250):
    print "Can create max 250 containers.\n"
    sys.exit(1)

#client_options=" -P "+str(L)+" -i 1 -p 5001 -f g -t "+str(measure_time)
client_options=" -P 1 -i 1 -p 5001 -f g -t "+str(measure_time)

client_startup_delay = client_startup_delay + (S/4)


# These scripts with be called on containers start

# Server startup script: start ssh server and iperf server
print "Writing startup scripts"
fservstp = open("server_startup.sh",'w')
fservstp.write("""#!/bin/bash
echo Starting up SSH server and iperf server with options: $1
/usr/sbin/sshd &
iperf -s &> /log.txt""")
fservstp.close()

# Client startup script: start ssh server and iperf client
fclntstp = open("client_startup.sh",'w')
fclntstp.write("""#!/bin/bash
#  echo Starting up SSH server and iperf client with options $@
/usr/sbin/sshd &
sleep %(client_startup_delay)s
# sleep is to wait for iptables to assign IP address to the contianer, otherwise iperf will fail (no connection to server)
touch /logs.txt\n""" % locals())
for i in range (L):
    fclntstp.write("iperf \"$@\" &>>/logs.txt &\n")
# $@ - commandline parameters from "docker run ..." command
# console output records inside of a stopped contaier can be viewed using "docker logs" command
fclntstp.write("sleep "+str(measure_time+1)+"\n")
fclntstp.write("python /getiperfresults.py /logs.txt")
fclntstp.close()


# server_image and client_image will be built with Dockerfiles

# Server dockerfile
fserv = open("Dockerfile",'w')
fserv.write("""
FROM %(image_name)s
MAINTAINER Bryzgalov Peter @ AICS RIKEN
ADD server_startup.sh /server_startup.sh
RUN chmod +x /server_startup.sh
EXPOSE 22 5001
ENTRYPOINT ["/server_startup.sh"]\n""" % locals())
fserv.close()

# Server image build
print "Building server image"
dockerlib.run("docker build --rm=true -t "+server_image+" .")


# Client Dockerfile 
print "Writing client Dockerfile"
fclnt = open("Dockerfile",'w')
fclnt.write("""
FROM %(image_name)s
MAINTAINER Bryzgalov Peter @ AICS RIKEN
ADD client_startup.sh /client_startup.sh
ADD getiperfresults.py /getiperfresults.py
RUN chmod +x /client_startup.sh
EXPOSE 22 5001
ENTRYPOINT [\"/client_startup.sh\"]\n""" % locals())
# CMD is for default options to ENTRYPOINT command
#fclnt.write("CMD\n")
fclnt.close()

# Client image build
print "Building client image"
dockerlib.run("docker build --rm=true -t "+client_image+" .")




# Running containers
print "Running server containers"
for i in range(S): 
    name="iserv"+str(i)
    (exitcode,contID,err)=dockerlib.run("docker run -d -p 22 -p 5001 --name "+name+" "+server_image+" runoptions")
    print "Started server container "+str(i)+ "("+contID[:8]+")"

# Assign IP to server
print "Assigning IP address"

for i in range(S): 
    IP=IPbase+str(start_iplow+i)+"/24"
    name="iserv"+str(i)
    dockerlib.assignIPiptables(name,IP)


print "Running client containers with client_options: "+client_options
for i in range(N):    
    name="client"+str(i)
    serverIP = IPbase + str(i%(S)+start_iplow) 
    print name + " -> " + serverIP 
    dockerlib.run("docker run -d -p 22 -p 5001 --name "+name+" "+client_image+" -c "+serverIP+client_options)
    PID=dockerlib.getContPID(name) 
    clinet_PIDs.append(PID)

# Assign IP to client
print "Assigning IPs to clients"
for i in range(N):
    name="client"+str(i)
    IP=IPbase+str(i+start_iplow+S)+"/24"
    dockerlib.assignIPiptables(name,IP)
print "Mesurements started"

# Wait till client containers stop

while True:
    (exitcode,n,err) = dockerlib.run("docker ps | grep "+client_image,False)
    if len(n) == 0:
        break

# Collect logs from client containers

print "Collecting logs"
for i in range(N):
    name="client"+str(i)
    # print name
    dockerlib.run("docker logs "+name)


ifremove=raw_input('Remove containers and images? (y/n) : ')

# Clean containers and images

if ifremove != 'n':
    for i in range(S):
        name="iserv"+str(i)
        dockerlib.cleanContainers([name])

    for i in range(N):
        name="client"+str(i)
        dockerlib.cleanContainers([name])

    dockerlib.run("docker rmi "+server_image)
    dockerlib.run("docker rmi "+client_image)