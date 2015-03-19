#!/bin/bash
# echo Starting up SSH server and iperf client with options $@
/usr/sbin/sshd &
sleep 2
# sleep is to wait for all clients to startup
IP=$ISERV_PORT_5001_TCP_ADDR
touch /logs.txt
iperf -c $IP "$@" &>>/logs.txt &
iperf -c $IP "$@" &>>/logs.txt &
sleep 8
python /getiperfresults.py /logs.txt