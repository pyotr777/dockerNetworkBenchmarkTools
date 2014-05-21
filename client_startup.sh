#!/bin/bash
/usr/sbin/sshd &
sleep 5
iperf "$@" &>/logs.txt
python /getiperfresults.py /logs.txt