#!/bin/bash

# Setup OVS connections from containers to ovs-bridge interface on host machine
# and setup tunnel from ovs-bridge to remote host with given IP.
# Takes three parametes: container IP with net mask, remote IP and OVS tunnel type

set -e

echo "v0.5"

usage=$(cat <<USAGE
Setup OVS connection from a container to ovs-bridge on host machine
and setup tunnel from ovs-bridge to remote host with given IP.
Parameters: container IP, remote host IP and OVS tunnel type.\n
USAGE
)

# Check that ovs_connect_container.sh exists
fname="ovs_connect_container.sh"
if [ ! -x "$fname" ]
then
    echo "Need executable $fname in the same directory."
    exit 1
fi

if [ $# -lt 2 ]
then
    echo "$usage"
    exit 0
fi

CntIP=$1
# Check if a subnet mask was provided.
echo $CntIP | grep -q / || {
    echo "The IP address must include a netmask."
    echo "Maybe you meant $CntIP/24 ?"
    exit 1
}
RmtIP=$2
TT="gre"
if [ $3 ]
then
    TT="$3"
fi

# Create bridge
bridge="ovs-bridge"
# Check if bridge existst
if [ -z "$(ip a s | grep $bridge)" ]
then
    ovs-vsctl add-br $bridge
fi

# Add port to bridge, create interface
port="ovs1"
echo "Setting bridge $bridge with tunnel $port type $TT to $RmtIP."
ovs-vsctl add-port $bridge $port -- set interface $port type=$TT options:remote_ip=$RmtIP

# Start container and connect it to the bridge
cont=$(docker run --name iperf_$TT -d peter/iperf /usr/sbin/sshd -D)
echo "Started container $cont \"iperf_$TT\"."

./ovs_connect_container.sh $cont $CntIP $bridge

echo "Setup complete"

