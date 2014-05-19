#!/bin/bash
echo Starting up SSH server and iperf server with options: $1
/usr/sbin/sshd &
iperf -s &> /log.txt
