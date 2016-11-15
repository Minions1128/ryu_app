from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.log import setLogLevel

from functools import partial
import time
import threading


def _sw_cmd(l_sw):
    time.sleep(5)
    for i in range(len(l_sw)):
        l_sw[i].cmd('ovs-vsctl set Bridge s{} protocols=OpenFlow13'.format(i+1))


def create_stp_net():
    _count_sw = 3
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
    l_sw = []
    for i in range(_count_sw):
        host_info = {
            'name':'h{}'.format(i+1),
            'ip':'10.0.0.{}/24'.format(i+1),
            'mac':'00:00:00:00:00:0{}'.format(i+1)
        }
        host = net.addHost(**host_info)
        switch = net.addSwitch('s{}'.format(i+1))
        l_sw.append(switch)
        net.addLink(switch, host)
    s1p2_mac = 'aa:aa:aa:aa:11:22'
    s1p3_mac = 'aa:aa:aa:aa:11:33'
    s2p2_mac = 'aa:aa:aa:aa:22:11'
    s2p3_mac = 'aa:aa:aa:aa:22:33'
    s3p2_mac = 'aa:aa:aa:aa:33:11'
    s3p3_mac = 'aa:aa:aa:aa:33:22'
    net.addLink(l_sw[0], l_sw[1], addr1=s1p2_mac, addr2=s2p2_mac)
    net.addLink(l_sw[0], l_sw[2], addr1=s1p3_mac, addr2=s2p2_mac)
    net.addLink(l_sw[1], l_sw[2], addr1=s2p3_mac, addr2=s3p3_mac)
    
    net.start()

    _s_cmd_thread = threading.Thread(target=_sw_cmd,args=(l_sw,))
    _s_cmd_thread.start()

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    create_stp_net()
