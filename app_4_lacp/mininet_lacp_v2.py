#LACP link between s1 and s2


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
		'controller':partial(RemoteController, 
			**ryu_info), 
		'autoSetMacs':True
	}
	net = Mininet(**mini_info)	
	c0 = net.addController()
	s1 = net.addSwitch('s1')
	s2 = net.addSwitch('s2')
	l_host = []
	for i in range(4):
		host_info = {
			'name':'h{}'.format(i+1),
			'ip':'10.0.0.{}/24'.format(i+1),
			'mac':'00:00:00:00:00:0{}'.format(i+1)
		}
		host = net.addHost(**host_info)
		l_host.append(host)		          
	s11_s2_addr = 'aa:02:01:aa:01:01'
	s12_s2_addr = 'aa:02:02:aa:01:02'
	# s13_h1_addr = 'bb:01:01:aa:01:03'
	# s14_h2_addr = 'bb:02:01:aa:01:04'
	s21_s1_addr = 'aa:01:01:aa:02:01'
	s22_s1_addr = 'aa:01:02:aa:02:02'
	# s23_h3_addr = 'bb:03:01:aa:02:03'
	# s24_h4_addr = 'bb:04:01:aa:02:04'
	net.addLink(s1, s2, addr1=s11_s2_addr, addr2=s21_s1_addr)
	net.addLink(s1, s2, addr1=s12_s2_addr, addr2=s22_s1_addr)
	net.addLink(s1, l_host[0])
	net.addLink(s1, l_host[1])
	net.addLink(s2, l_host[2])
	net.addLink(s2, l_host[3])

	net.start()
	CLI(net)
	net.stop()


if __name__ == '__main__':
	setLogLevel('info')
	create_lacp_net()
