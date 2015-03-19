# Docker containers service

## Files 

### clean_containers.py

Clean network settings (virtual interfaces, etc.) created by start_containers_iptabes.py

#### Calls:
	dockerlib.py
	iptablesclean.sh


### cleanuser.sh

Removes user on the server and removes users's containers.

### cleanroutes.sh

Removes from iptables all rules created by start_containers_iptables.py that have IP address with “172”  


### iptablesclean.sh

Cleans iptables records related to container with name in command-line argument.
