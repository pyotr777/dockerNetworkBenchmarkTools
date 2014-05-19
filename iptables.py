# Assign external IP (fixed or with DHCP) address with iptables.
# Parameters:
# 1st - container ID
# 1st - IP address with mask or "dhcp"


import sys,dockerlib

if (len(sys.argv) < 3):
    print "Provide container ID and IP address or 'dhcp'"
    sys.exit(1)

if (len(sys.argv) >= 3):
    dockerlib.assignIPiptables(sys.argv[1],sys.argv[2])

