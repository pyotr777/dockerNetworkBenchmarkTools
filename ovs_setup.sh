#!/bin/bash

# Setup OVS connections from two containers to ovs-bridge interface on host machine

if [ $# -gt 1 ]
then
    printf 'Setup OVS connections between two containers via ovs-bridge (must exist!) on host machine\nContainers will be named iperfserv and iperfclient with IP 10.0.0.5 and 10.0.0.6, created from image peter/iperf.\nNeed no parameters.\n'
    exit 0
fi

set -e

clnt=$(docker run -name iperfclient -d peter/iperf /usr/sbin/sshd -D)
serv=$(docker run -name iperfserv -d peter/iperf /usr/sbin/sshd -D)

echo "Created containers iperfserv $serv and iperfclient $clnt"

clntPID=$(docker inspect iperfclient | jq '.[0].State.Pid')
servPID=$(docker inspect iperfserv | jq '.[0].State.Pid')

if [ ! -d /var/run/netns/ ]
then 
    mkdir -p /var/run/netns/
fi

ln -s /proc/$clntPID/ns/net /var/run/netns/$clntPID 
ln -s /proc/$servPID/ns/net /var/run/netns/$servPID

ovs-vsctl add-port ovs-bridge tap1 -- set Interface tap1 type=internal
ovs-vsctl add-port ovs-bridge tap2 -- set Interface tap2 type=internal
ip link set tap1 netns $clntPID
ip link set tap2 netns $servPID

ip netns exec $clntPID ip link set dev tap1 up
ip netns exec $servPID ip link set dev tap2 up
ip netns exec $clntPID ip addr add dev tap1 10.0.0.5/24
ip netns exec $servPID ip addr add dev tap2 10.0.0.6/24