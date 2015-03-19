# Scripts for setting up performance measurement environments for Docker Inter-Container Communications

## Open vSwitch

Measure ICC performance for containers connected with OVS through "ovs-bridge" bridge on host

```bash
iovs <servers> <clients> <processes>
```
servers -- number of iperf server containers
clients -- number of iperf client containers
processes -- number of iperf processes in each client container

#### Uses:
    ipref_ovs_multiproc.py
    dockerlib.py
    ovs_connect_containers.sh
    getiperfresults.py

## Utilities

### clean_containers.py

Clean network settings (virtual interfaces, etc.) created by start_containers_iptabes.py

#### Uses:
	dockerlib.py
	iptablesclean.sh


### cleanuser.sh

Removes user on the server and removes users's containers.

### cleanroutes.sh

Removes from iptables all rules created by start_containers_iptables.py that have IP address with “172”


### iptablesclean.sh

Cleans iptables records related to container with name in command-line argument.

### getContPID.sh

Return process ID as seen from host for process 1 inside container.
Parameter: container ID

### Docker.iperf/Dockerfile

Dockerfile for building image with iperf
