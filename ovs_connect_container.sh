#!/bin/bash

# Connect container to OVS bridge ovs-bridge (must exist!) on host machine.
# Takes two parameters: container ID (name) and IP address.

set -e

echo "v0.6"

usage=$(cat  <<USAGE
Connects container to OVS bridge (ovs-bridge by default, must exist) on host machine.
Takes two or three parameters: container ID (name) and IP address, OVS bridge name and MTU (optional).
USAGE
)

if [ $# -lt 3 ]
then
    echo "$usage"
    exit 0
fi

contID=$1
IP=$2 

[ "$IP" ] || {
    echo "$usage"
    exit 0
}

echo $IP | grep -q / || {
        echo "The IP address should include a netmask."
        echo "Maybe you meant $IP/24 ?"
        exit 1
}

bridge="ovs-bridge"
if [ $3 ] 
then
    bridge="$3"
fi

if [ $4 ]
then
    MTU=$4
fi

echo "contID=$contID IP=$IP bridge=$bridge mtu=$MTU"

command="docker inspect $contID"
contPID=$($command  | jq '.[0].State.Pid')
echo "Continer PID $contPID"

[ "$contPID" ] || {
    echo "Couldn't inspect container $contID"
    exit 1
}

if [ ! -d /var/run/netns/ ]
then 
    mkdir -p /var/run/netns/
fi

ln -s /proc/$contPID/ns/net /var/run/netns/$contPID 

ifName="tap$contPID"

ovs-vsctl add-port $bridge $ifName -- set Interface $ifName type=internal
if [ -n $MTU ]
then
    ifconfig $ifName mtu 1450
fi
ip link set $ifName netns $contPID

ip netns exec $contPID ip link set dev $ifName up
ip netns exec $contPID ip addr add dev $ifName $IP
