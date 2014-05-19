#!/bin/bash
echo Starting up SSH server and iperf client with options $@
/usr/sbin/sshd &
sleep 3
ip a show eth1
iperf "$@" &>/logs.txt
python /getiperfresults.py /logs.txt