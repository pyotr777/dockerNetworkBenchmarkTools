#!/bin/bash

set -e
set -x


contID=$1

command="docker inspect $contID"
echo $command
contPID=$($command | jq '.[0].State.Pid')
echo "Continer PID $contPID"
