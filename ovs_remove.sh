#!/bin/bash

# Remove containers named iperfserv and iperfclient
# and ovs ports tap1 and tap2

docker rm $(docker kill iperfserv iperfclient)
ovs-vsctl del-port tap1
ovs-vsctl del-port tap2