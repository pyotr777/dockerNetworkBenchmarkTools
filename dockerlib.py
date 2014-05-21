# functions to work with docker API

import sys, re,subprocess,json

docker_api_sock=["docker"]
docker_api_port=["docker","-H","localhost:4243"]

docker_api=docker_api_sock

def confirm(message):
    sys.stdout.write(message+"\n[y/n]:")
    while True:
        answer=raw_input().lower()
        if (answer.find("y") >= 0):
            return True
        elif (answer.find("n") >= 0):
            return False
        else:
            sys.stdout.write("Only 'y' or 'n':")
            
# Remove virtual networking interfaces
# created by ip.sh for for assigning external IP addresses to Docker containers
def removeInterfaces(cont_names):
    for cont in cont_names:
        # do=confirm("Remove "+cont+"?")
        do = True
        if (do):
            br = getBridgeName(cont)
            print "Removing " + br            
            subprocess.call(["ip","link","set",br,"down"])
            ps_list=subprocess.Popen(["ps","ax"],stdout=subprocess.PIPE)
            dchp_proc=subprocess.Popen(["grep",br],stdin=ps_list.stdout,stdout=subprocess.PIPE)            
            procls, err = dchp_proc.communicate()
            procs = procls.split("\n")
            for proc in procs:
                if (proc.find("grep")==-1):
                    print "Stopping dhclient for "+br
                    subprocess.call(["dhclient","-d","-r",br])                    
                    m = re.match("\d+",proc)
                    if (m is not None):
                        procn = m.group(0)
                        print "Killing process "+procn
                        subprocess.call(["kill",procn])
            print "Deleting interface "+br
            subprocess.call(["ip","link","delete",br])

def getContNames():
    c = subprocess.Popen(docker_api+["ps"],stdout=subprocess.PIPE)
    cont_list, err = c.communicate()
    cont_names = []
    
    for line in cont_list.split("\n"):
        if "Up" in line:
            m=re.findall("[\w\/:\-\.]+",line)
            cont_names.append(m[len(m)-1])
    return cont_names

def getContID(cont_name):
    if (cont_name is None):
        return None
    #print "inspecting "+ cont_name
    c = subprocess.Popen(docker_api+["inspect",cont_name],stdout=subprocess.PIPE)
    r, err = c.communicate()
    if (len(r) < 5):
        return None
    jsn = json.loads(r)
    return jsn[0]["Config"]["Hostname"]

# Get container name
# cont_ID
def getContName(cont_ID):
    c = subprocess.Popen(docker_api+["inspect",cont_ID],stdout=subprocess.PIPE)
    r, err = c.communicate()
    if (len(r) < 5):
        return None
    jsn = json.loads(r)
    p = re.compile("^/")
    name = p.sub("",jsn[0]["Name"])
    return name


def getInternalIP(cont_name):
    c = subprocess.Popen(docker_api+["inspect",cont_name],stdout=subprocess.PIPE)
    r, err = c.communicate()
    if (len(r) < 5):
        return None
    jsn = json.loads(r)
    return jsn[0]["NetworkSettings"]["IPAddress"]

def getExternalIP(cont_name):
    br_name = getBridgeName(cont_name)
    c = subprocess.Popen(["./getip.sh",br_name],stdout=subprocess.PIPE)
    CIDR, err = c.communicate()
    if (len(CIDR) < 5):
        return None
    extip = CIDR.split("/")[0]
    return extip

def getBridgeName(cont_name):
    br_name = "br_"+cont_name
    if (len(br_name)>15):
        br_name = br_name[0:15]
    return br_name


def getContPID(cont_name):
    c = subprocess.Popen(docker_api+["inspect",cont_name],stdout=subprocess.PIPE)
    r, err = c.communicate()
    if (len(r) < 5):
        return None
    jsn = json.loads(r)
    return jsn[0]["State"]["Pid"]

# Run N containers
# command - command to start containers
#
# Returns containers long IDs
def runContainers(N,command):
    cont_longIDs = []
    i_start=1
    for i in range(i_start,N+1):
        name="cont"+str(i)
        print "Starting "+name
        docker_command = " run -d -name "+name + " " + command
        command_list = docker_command.split()
        c = subprocess.Popen(docker_api+command_list,stdout=subprocess.PIPE)
        num, err = c.communicate()
        # Detect error
        if (len(num)<1):
            i_start = i+1
            continue
        if (err is not None):
            i_start = i+1
            print "ERROR " + err
            continue
       
       #print num + " by name " +name
        cont_longIDs.append(num.replace('\n',''))
    return cont_longIDs

# Assign external IP (fixed or with DHCP) address with iptables.
# Parameters:
# container name
# IP address with mask or "dhcp"
def assignIPiptables(cont_name,IP):
    make_br = True
    add_routing = True
    use_dhcp = False

    if (IP=="dhcp"):
        use_dhcp = True
        IPa = "DHCP"
    else:
        IPa = IP

    cont_ID=getContID(str(cont_name))
    # print cont_ID+" \t: \t" + cont_name

    if (make_br):    
        print "Assigning " +IPa+ " to container " + cont_name
        
        br_name=getBridgeName(cont_ID)
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

        intip = getInternalIP(cont_ID)
        print cont_ID+ " : "+ extip + " - " + intip
        
        if (add_routing):
            if (extip is None):
                print "No ext IP for "+ cont_ID
            elif (intip is None):
                print "No int IP for " + cont_ID
            else :    
                subprocess.call(["./iptables.sh",cont_ID,extip,intip])


# Assign IP (fixed or with DHCP) address with pipework.
# Parameters:
# container name
# IP address with mask or "dhcp"
def assignIPpipework(cont_name,IP):
    c = subprocess.Popen(["./pipework.sh","br1",getContID(cont_name),IP],stdout=subprocess.PIPE)
    out, err = c.communicate()
    if out is not None and len(out)>1:
        print out
    if err is not None and len(err)>1:
        print "Err:"+err


# Assign fixed IP address to container port, attached to ovs_bridge bridge on the host
# Parameters:
# container ID
# IP address with mask
def assignIPovs(cont_name,IP):
    contID=getContID(cont_name)
    command=["./ovs_connect_container.sh",contID[:8],IP]
    print command
    c = subprocess.Popen(command,stdout=subprocess.PIPE)
    out, err = c.communicate()
    if out is not None and len(out)>1:
        print out
    if err is not None and len(err)>1:
        print "Err:"+err


# Clear docker ip settings
# Remove interfaces (br_...)
# Kill containers
# Remove stopped containers
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
        cont_ID=getContID(str(cont_name))
        if (cont_ID is None):
            # Probably we have container ID in command line parameters
            cont_ID = cont_name
        print "ID: "+ str(cont_ID)
        extip = getExternalIP(cont_ID)
        intip = getInternalIP(cont_ID)
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
        removeInterfaces([cont_ID])

        
    if (stop_containers):
        for cont_name in cont_names:
            print "Kill "+ cont_name
            subprocess.call(docker_api+["kill",cont_name])
    if (remove_containers):
        for cont_name in cont_names:
            print "Remove "+ cont_name
            subprocess.call(docker_api+["rm",cont_name])
