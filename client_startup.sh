#!/bin/bash
set +x
echo Started client with parameters "$@"
sleep 2
touch /logs.txt
echo Measurements start
iperf $@ &>>/logs.txt
cat /logs.txt
echo Measurements finished
python /getiperfresults.py /logs.txt