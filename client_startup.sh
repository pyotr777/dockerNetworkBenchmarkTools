#!/bin/bash
echo Starting up SSH server and iperf client with options $@
/usr/sbin/sshd &
sleep 3
ip a show
iperf "$@"
