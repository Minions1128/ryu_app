# Multipath
This module is a group table example for load balance.
## Topo
Topology is as follows:


                |--------switch2 --------|     |-----host2
   host1 --- switch1                     switch4
                |                        |     |-----host3
                -------- switch3 ---------

# #multi_path_net.py
Define network topology using mininet.
## dump_flows.sh
dump the flows and groups info.
## multi_path.py
The multipath ryu app.
## add_flows.sh
Add the flows and groups on Open vSwitch directly.