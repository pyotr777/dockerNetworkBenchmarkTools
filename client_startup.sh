#!/bin/bash
#  echo Starting up SSH server and iperf client with options $@
/usr/sbin/sshd &
sleep 5
# sleep is to wait for pipework to assign IP address to the contianer, otherwise iperf will fail (no connection to server)
touch /logs.txt
iperf "$@" &>>/logs.txt &
iperf "$@" &>>/logs.txt &
iperf "$@" &>>/logs.txt &
iperf "$@" &>>/logs.txt &
sleep 6
python /getiperfresults.py /logs.txt