# Tests connection performance between containers with iperf.
# First parameter (N) - number of containers.
# Start containers: 1 with iperf server, N with iperf clients.
# Assign IPs with pipework: 10.0.0.3/24 to server, 10.0.0.4/24,... to clients.

import sys,subprocess,dockerlib,time

N = 2
IPbase = "10.0.0." 
server_iplow = 3  # lower number in IP address of the server
ServerIP = IPbase+str(server_iplow)
image_name = "peter/iperf"  # This image with iperf installed must exist
server_image="peter/iserv"  # These two images will be created
client_image="peter/iclient"
measure_time = 5
client_options="-c "+ServerIP+" -P 1 -i 1 -p 5001 -f g -t "+str(measure_time)

if (len(sys.argv) > 1):
    N = int(sys.argv[1])
    if (N > 250):
	   print "Can create max 250 containers.\n"
	   sys.exit(1)

# Procedure for running shell commands 
# Prints out command stdout and (after it) stderr
# Returns exit code, stdout and stderr
def run(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    errs = ""
    outs = ""
    while True:
        out = p.stdout.read(1)
        err = p.stderr.read(1)
        if out == '' and p.poll() != None:
            break
        if out != '':
            outs = outs + out
            sys.stdout.write(out)
            sys.stdout.flush()
        if err != '':
            errs = errs + err
            sys.stderr.flush()
    if errs != "":
        print "Err:"+errs
    return p.returncode,outs,errs    


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
fclntstp.write("echo Starting up SSH server and iperf client with options $@\n")
fclntstp.write("/usr/sbin/sshd &\n")
fclntstp.write("sleep 3\n")
# sleep is to wait for pipework to assign IP address to the contianer, otherwise iperf will fail (no connection to server)

fclntstp.write("ip a show eth1\n")
# check IP settings

fclntstp.write("iperf \"$@\" &>/logs.txt\n")
# $@ - commandline parameters from "docker run ..." command
# console output records inside of a stopped contaier can be viewed using "docker logs" command
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
run("docker build --rm=true -t "+server_image+" .")


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
run("docker build --rm=true -t "+client_image+" .")



# Running containers
print "Running server container"
(exitcode,contID,err)=run("docker run -d -p 22 -p 5001 -name iserv "+server_image+" runoptions")
print "Started server container "+contID[:8]

# Assign IP to server
print "Assigning IP address"
IP=ServerIP+"/24"
print "./pipework.sh","br1","iserv",IP
c = subprocess.Popen(["./pipework.sh","br1",dockerlib.getContID("iserv"),IP],stdout=subprocess.PIPE)
out, err = c.communicate()
print out


print "Running client containers"
for i in range(N):    
    name="client"+str(i)
    print name
    run("docker run -d -p 22 -p 5001 -name "+name+" "+client_image+" "+client_options)

# Assign IP to client
print "Assigning IPs to clients"
for i in range(N):
    name="client"+str(i)
    IP=IPbase+str(i+server_iplow+1)+"/24"
    print "./pipework.sh","br1",name,IP
    c = subprocess.Popen(["./pipework.sh","br1",dockerlib.getContID(name),IP],stdout=subprocess.PIPE)
    out, err = c.communicate()
    print out


time.sleep(measure_time + 5)
for i in range(N):
    name="client"+str(i)
    print name
    run("docker logs "+name)

ifremove=raw_input('Remove containers and images? (y/n) : ')

if ifremove == 'y':
    run("docker kill "+dockerlib.getContID("iserv"))
    run("docker rm "+dockerlib.getContID("iserv"))
    for i in range(N):
        name="client"+str(i)
        run("docker kill "+dockerlib.getContID(name))
        run("docker rm "+dockerlib.getContID(name))
    run("docker rmi "+server_image)
    run("docker rmi "+client_image)