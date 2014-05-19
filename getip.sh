#!/bin/bash

ip addres show $1 | grep 'inet ' | awk '{ print $2 }'
