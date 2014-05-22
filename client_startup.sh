#!/bin/bash
/usr/sbin/sshd &
sleep 5
touch /logs.txt
iperf "$@" &>>/logs.txt &
iperf "$@" &>>/logs.txt &
iperf "$@" &>>/logs.txt &
iperf "$@" &>>/logs.txt &
iperf "$@" &>>/logs.txt &
iperf "$@" &>>/logs.txt &
iperf "$@" &>>/logs.txt &
iperf "$@" &>>/logs.txt &
iperf "$@" &>>/logs.txt &
iperf "$@" &>>/logs.txt &
iperf "$@" &>>/logs.txt &
iperf "$@" &>>/logs.txt &
iperf "$@" &>>/logs.txt &
iperf "$@" &>>/logs.txt &
iperf "$@" &>>/logs.txt &
iperf "$@" &>>/logs.txt &
sleep 5
python /getiperfresults.py /logs.txt