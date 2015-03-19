#!/bin/bash
echo Starting up SSH server and iperf server with options: $@
/usr/sbin/sshd &
iperf -s &> /log.txt
