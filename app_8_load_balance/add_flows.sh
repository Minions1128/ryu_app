ovs-ofctl -O OpenFlow13 add-group s1 group_id=5566,type=select,bucket=weight:10,output:2,bucket=weight=90,output:3
# ovs-ofctl -O OpenFlow13 add-group s1 group_id=5566,type=select,bucket=weight:50,output:2,bucket=weight=50,output:3
ovs-ofctl -O OpenFlow13 add-flow s1 in_port=1,actions=group:5566
ovs-ofctl -O OpenFlow13 add-flow s1 eth_type=0x0800,ip_dst=10.0.0.1,actions=output:1
ovs-ofctl -O OpenFlow13 add-flow s1 eth_type=0x0806,ip_dst=10.0.0.1,actions=output:1

ovs-ofctl -O OpenFlow13 add-flow s2 in_port=1,actions=output:2
ovs-ofctl -O OpenFlow13 add-flow s2 in_port=2,actions=output:1

ovs-ofctl -O OpenFlow13 add-flow s3 in_port=1,actions=output:2
ovs-ofctl -O OpenFlow13 add-flow s3 in_port=2,actions=output:1

ovs-ofctl -O OpenFlow13 add-flow s4 eth_type=0x0800,ip_dst=10.0.0.2,actions=output:3
ovs-ofctl -O OpenFlow13 add-flow s4 eth_type=0x0800,ip_dst=10.0.0.3,actions=output:4

ovs-ofctl -O OpenFlow13 add-flow s4 eth_type=0x0806,ip_dst=10.0.0.2,actions=output:3
ovs-ofctl -O OpenFlow13 add-flow s4 eth_type=0x0806,ip_dst=10.0.0.3,actions=output:4

# ovs-ofctl -O OpenFlow13 add-group s4 group_id=5567,type=select,bucket=weight:50,output:1,bucket=weight=50,output:2
ovs-ofctl -O OpenFlow13 add-group s4 group_id=5567,type=select,bucket=weight:10,output:1,bucket=weight=90,output:2
ovs-ofctl -O OpenFlow13 add-flow s4 eth_type=0x0800,ip_dst=10.0.0.1,actions=group:5567
ovs-ofctl -O OpenFlow13 add-flow s4 eth_type=0x0806,ip_dst=10.0.0.1,actions=group:5567

