# Tests connection performance between containers with iperf.
# First parameter (M) - number of servers.
# Second parameter (N) - number of containers.
# Third parameter (L) - number of processes per client container.
# Start containers: M with iperf server, N with iperf clients.
# Connect containers through ovs bridge,
# assign then IPs: 10.0.0.3/24,... first to servers, then to clients.

# 1st clent connects to 1 server, 
# M-th client connects to M-th server, (M+1)-th client connects to 1st server, etc.

import sys,subprocess,dockerlib,time,math

N = 2
M = 2
L = 1
IPbase = "10.0.0." 
start_iplow = 3  # lower number in IP address of the server
image_name = "peter/iperf"  # This image with iperf installed must exist
server_image="peter/iserv"  # These two images will be created
client_image="peter/iclient"
measure_time = 4
client_startup_delay = 5
bridge_create="ovs-vsctl --may-exist add-br ovs-bridge"
bridge_remove="ovs-vsctl --if-exists del-br ovs-bridge"

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

# Setup open vSwitch bridge
(exitcode,contID,err)=dockerlib.run(bridge_create)
if (exitcode > 0):
    print "Error creating bridge with command:"+bridge_create+"\nExitcode ("+str(exitcode)+ ")"
    if (err is not None and err != ""):
        print "Err: "+err
    sys.exit(1)



# These scripts with be called on containers start

# Server startup script: start ssh server and iperf server
print "Writing startup scripts"
fservstp = open("server_startup.sh",'w')
fservstp.write("#!/bin/bash\n")
fservstp.write("echo Starting up SSH server and iperf server with options: $1\n")
fservstp.write("/usr/sbin/sshd &\n")
fservstp.write("iperf -s &> /log.txt\n")
fservstp.close()

# Client startup script: start ssh server and iperf client
fclntstp = open("client_startup.sh",'w')
fclntstp.write("#!/bin/bash\n")
# fclntstp.write("echo Starting up SSH server and iperf client with options $@\n")
fclntstp.write("/usr/sbin/sshd &\n")
fclntstp.write("sleep "+str(client_startup_delay)+"\n")
fclntstp.write("touch /logs.txt\n")
# sleep is to wait for pipework to assign IP address to the contianer, otherwise iperf will fail (no connection to server)
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
fserv.write("FROM "+image_name+"\n")
fserv.write("MAINTAINER Bryzgalov Peter @ AICS RIKEN\n")
fserv.write("ADD server_startup.sh /server_startup.sh\n")
fserv.write("RUN chmod +x /server_startup.sh\n")
fserv.write("EXPOSE 22 5001\n")
fserv.write("ENTRYPOINT [\"/server_startup.sh\"]\n")
fserv.close()

# Server image build
print "Building server image"
dockerlib.run("docker build --rm=true -t "+server_image+" .")


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
dockerlib.run("docker build --rm=true -t "+client_image+" .")




# Running containers
print "Running server containers"
for i in range(M): 
    name="iserv"+str(i)
    (exitcode,contID,err)=dockerlib.run("docker run -d -p 22 -p 5001 -name "+name+" "+server_image+" runoptions")
    print "Started server container "+str(i)+ "("+contID[:8]+")"

# Assign IP to server
print "Assigning IP address"

for i in range(M): 
    IP=IPbase+str(start_iplow+i)+"/24"
    name="iserv"+str(i)
    dockerlib.assignIPovs(name,IP)


print "Running client containers with client_options: "+client_options
for i in range(N):    
    name="client"+str(i)
    serverIP = IPbase + str(i%(M)+start_iplow)     
    print name + " -> " + serverIP 
    dockerlib.run("docker run -d -p 22 -p 5001 -name "+name+" "+client_image+" -c "+serverIP+client_options)
    PID=dockerlib.getContPID(name) 
    clinet_PIDs.append(PID)

# Assign IP to client
print "Assigning IPs to clients"
for i in range(N):
    name="client"+str(i)
    IP=IPbase+str(i+start_iplow+M)+"/24"    
    dockerlib.assignIPovs(name,IP)

time.sleep(measure_time  + client_startup_delay+ math.floor((M+N+L)/3))

print "Collecting logs"
for i in range(N):
    name="client"+str(i)
    # print name
    dockerlib.run("docker logs "+name)




ifremove=raw_input('Remove containers and images? (y/n) : ')


def removeCont(name):    
    PID=dockerlib.getContPID(name)    
    contID=dockerlib.getContID(name)
    print "Remove "+contID+" and netns "+str(PID)    
    dockerlib.run("docker kill "+contID)
    dockerlib.run("docker rm "+contID)    
    if (PID !=0 ):
        dockerlib.run("rm /var/run/netns/"+str(PID))

if ifremove != 'n':
    for i in range(M):
        name="iserv"+str(i)
        removeCont(name)
        
    for i in range(N):
        name="client"+str(i)
        removeCont(name)

    # remove netspace directories of client contianers
    for PID in clinet_PIDs:
        print "remove netspace folder /var/run/netns/"+str(PID) 
        dockerlib.run("rm /var/run/netns/"+str(PID))

    dockerlib.run("docker rmi "+server_image)
    dockerlib.run("docker rmi "+client_image)


    # Setup open vSwitch bridge
    (exitcode,contID,err)=dockerlib.run(bridge_remove)
    if (exitcode > 0):
        print "Error removing bridge with command:"+bridge_remove+"\nExitcode ("+str(exitcode)+ ")"
        if (err is not None and err != ""):
            print "Err: "+err
        sys.exit(1)
