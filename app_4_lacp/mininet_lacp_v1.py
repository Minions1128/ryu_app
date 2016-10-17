#LACP link between h1 and s1


from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.log import setLogLevel

from functools import partial


def create_lacp_net():
	ryu_info = {
		'ip':'10.207.51.119',
		'port':6633
	}

	mini_info = {
		'controller':partial(RemoteController, **ryu_info), 
		'autoSetMacs':True
	}

	net = Mininet(**mini_info)

	c0 = net.addController()
	s1 = net.addSwitch('s1')

	yes = True

	for i in range(4):
		host_info = {
			'name':'h{}'.format(i+1),
			'ip':'10.0.0.{}/24'.format(i+1),
			'mac':'00:00:00:00:00:0{}'.format(i+1)
		}
		host = net.addHost(**host_info)
		if yes:
			net.addLink(s1, host)
			yes = False
		net.addLink(s1, host)

	net.start()
	h1 = net.get('h1')
	h1.cmd('modprobe bonding')
	h1.cmd('ip link add bond0 type bond')
	h1.cmd('ip link set bond0 address aa:aa:dd:dd:11:11')
	h1.cmd('ip link set h1-eth0 down')
	h1.cmd('ip link set h1-eth0 address 00:00:00:00:00:11')
	h1.cmd('ip link set h1-eth0 master bond0')
	h1.cmd('ip link set h1-eth1 down')
	h1.cmd('ip link set h1-eth1 address 00:00:00:00:00:12')
	h1.cmd('ip link set h1-eth1 master bond0')
	h1.cmd('ip addr del 10.0.0.1/24 dev h1-eth0')
	h1.cmd('ip addr add 10.0.0.1/24 dev bond0')
	h1.cmd('ip link set bond0 up')
	#s1.cmd('ovs-vsctl set Bridge s1 protocols=OpenFlow13')

	CLI(net)
	net.stop()


if __name__ == '__main__':
	setLogLevel('info')
	create_lacp_net()
