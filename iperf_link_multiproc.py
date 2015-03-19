#!/usr/bin/python

# Tests connection performance between containers with iperf.
# First parameter (M) - number of servers.
# Second parameter (N) - number of containers.
# Third parameter (L) - number of processes per client container.
# Start containers: M with iperf server, N with iperf clients.
# Connect containers docker linking.

# 1st clent connects to 1 server, 
# M-th client connects to M-th server, (M+1)-th client connects to 1st server, etc.

import sys,subprocess,dockerlib,time,math

N = 2
M = 2
L = 1
image_name = "peter/iperf"  # This image with iperf installed must exist
server_image="peter/iserv"  # These two images will be created
client_image="peter/iclient"
measure_time = 7
client_startup_delay = 2

clinet_PIDs=[]

if (len(sys.argv) > 1):
    M = int(sys.argv[1])
	   
if (len(sys.argv) > 2):
    N = int(sys.argv[2])

if (len(sys.argv) > 3):
    L = int(sys.argv[3])

if (M + N > 250):
    print "Can create max 250 containers.\n"
    sys.exit(1)

client_options=" -P 1 -i 1 -p 5001 -f g -t "+str(measure_time)
client_startup_delay = client_startup_delay + (M/4)


# These scripts with be called on containers start

# Server startup script: start ssh server and iperf server
print "Writing startup scripts"
fservstp = open("server_startup.sh",'w')
fservstp.write("#!/bin/bash\n")
fservstp.write("echo Starting up SSH server and iperf server with options: $@\n")
fservstp.write("/usr/sbin/sshd &\n")
fservstp.write("iperf -s &> /log.txt\n")
fservstp.close()

# Client startup script: start ssh server and iperf client
fclntstp = open("client_startup.sh",'w')
fclntstp.write("""#!/bin/bash
# echo Starting up SSH server and iperf client with options $@
/usr/sbin/sshd &
sleep %(client_startup_delay)s
# sleep is to wait for all clients to startup
IP=$ISERV_PORT_5001_TCP_ADDR
""" % locals())
fclntstp.write("touch /logs.txt\n")
for i in range (L):
	fclntstp.write("iperf -c $IP \"$@\" &>>/logs.txt &\n")
# $@ - commandline parameters from "docker run ..." command
# console output records inside of a stopped contaier can be viewed using "docker logs" command
fclntstp.write("sleep "+str(measure_time+1)+"\n")
fclntstp.write("python /getiperfresults.py /logs.txt")
fclntstp.close()


# server_image and client_image will be built with Dockerfiles

# Server dockerfile
fserv = open("Dockerfile",'w')
fserv.write("FROM "+image_name+"\n")
fserv.write("MAINTAINER Bryzgalov Peter @ AICS RIKEN\n")
fserv.write("ADD server_startup.sh /server_startup.sh\n")
fserv.write("RUN chmod +x /server_startup.sh\n")
fserv.write("EXPOSE 22 5001\n")
fserv.write("ENTRYPOINT [\"/server_startup.sh\"]\n")
fserv.close()

# Server image build
print "Building server image"
dockerlib.run("docker build --rm=true -t "+server_image+" .",False)


# Client Dockerfile 
print "Writing client Dockerfile"
fclnt = open("Dockerfile",'w')
fclnt.write("FROM "+image_name+"\n")
fclnt.write("MAINTAINER Bryzgalov Peter @ AICS RIKEN\n")
fclnt.write("ADD client_startup.sh /client_startup.sh\n")
fclnt.write("ADD getiperfresults.py /getiperfresults.py\n")
fclnt.write("RUN chmod +x /client_startup.sh\n")
fclnt.write("EXPOSE 22 5001\n")
fclnt.write("ENTRYPOINT [\"/client_startup.sh\"]\n")
# CMD is for default options to ENTRYPOINT command
#fclnt.write("CMD\n")
fclnt.close()

# Client image build
print "Building client image"
dockerlib.run("docker build --rm=true -t "+client_image+" .",False)




# Start containers
print "Running server containers"
for i in range(M): 
    name="iserv"+str(i)
    runcommand="docker run -d -p 22 --name "+name+" "+server_image
    print(runcommand)
    (exitcode,contID,err)=dockerlib.run(runcommand,False)
    

print "Running client containers with client_options: "+client_options
for i in range(N):    
    name="client"+str(i)
    server_name = "iserv" + str(i%M)     
    print name + " -> " + server_name
    runcommand="docker run -d -p 22 --name "+name+" --link "+server_name+":iserv "+client_image+" "+client_options
    # runcommand="docker run -d -p 22 -p 5001 --name "+name+" "+client_image
    # print runcommand
    dockerlib.run(runcommand,False)
    PID=dockerlib.getContPID(name) 
    clinet_PIDs.append(PID)


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


# Ask if user wants to clean out 

ifremove=raw_input('Remove containers and images? (y/n) : ')


def removeCont(name):    
    PID=dockerlib.getContPID(name)    
    contID=dockerlib.getContID(name)
    print "Remove "+contID
    dockerlib.run("docker kill "+contID,False)
    dockerlib.run("docker rm "+contID,False)    
    

if ifremove != 'n':
    for i in range(M):
        name="iserv"+str(i)
        removeCont(name)
        
    for i in range(N):
        name="client"+str(i)
        removeCont(name)

    dockerlib.run("docker rmi "+server_image)
    dockerlib.run("docker rmi "+client_image)
