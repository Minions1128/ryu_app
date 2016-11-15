from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.log import setLogLevel

from functools import partial
import time
import threading


def _sw_cmd(l_sw):
    time.sleep(10)
    print '\n'
    print '\n'
    for i in range(len(l_sw)):
        _cmd = 'ovs-vsctl set Bridge s{} protocols=OpenFlow13'.format(i+1)
        print _cmd
        l_sw[i].cmd(_cmd)
    print '\n'
    print '\n'


def create_stp_net():
    _count_sw = 4
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

    s1p2_mac = 'aa:aa:aa:c1:c2:02'
    s1p3_mac = 'aa:aa:aa:c1:c2:03'
    s1p4_mac = 'aa:aa:aa:c1:c3:04'
    s1p5_mac = 'aa:aa:aa:c1:c3:05'

    s2p2_mac = 'aa:aa:aa:c2:c1:02'
    s2p3_mac = 'aa:aa:aa:c2:c1:03'
    s2p4_mac = 'aa:aa:aa:c2:c4:04'
    s2p5_mac = 'aa:aa:aa:c2:c4:05'

    s3p2_mac = 'aa:aa:aa:c3:c1:02'
    s3p3_mac = 'aa:aa:aa:c3:c1:03'
    s3p4_mac = 'aa:aa:aa:c3:c4:04'
    s3p5_mac = 'aa:aa:aa:c3:c4:05'

    s4p2_mac = 'aa:aa:aa:c4:c3:02'
    s4p3_mac = 'aa:aa:aa:c4:c3:03'
    s4p4_mac = 'aa:aa:aa:c4:c2:04'
    s4p5_mac = 'aa:aa:aa:c4:c2:05'

    net.addLink(l_sw[0], l_sw[1], addr1=s1p2_mac, addr2=s2p2_mac)
    net.addLink(l_sw[0], l_sw[1], addr1=s1p3_mac, addr2=s2p3_mac)
    net.addLink(l_sw[2], l_sw[3], addr1=s3p2_mac, addr2=s4p2_mac)
    net.addLink(l_sw[2], l_sw[3], addr1=s3p3_mac, addr2=s4p3_mac)

    net.addLink(l_sw[0], l_sw[2], addr1=s1p4_mac, addr2=s3p4_mac)
    net.addLink(l_sw[0], l_sw[2], addr1=s1p5_mac, addr2=s3p5_mac)
    net.addLink(l_sw[1], l_sw[3], addr1=s2p4_mac, addr2=s4p4_mac)
    net.addLink(l_sw[1], l_sw[3], addr1=s2p5_mac, addr2=s4p5_mac)

    
    net.start()

    _s_cmd_thread = threading.Thread(target=_sw_cmd,args=(l_sw,))
    _s_cmd_thread.start()

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    create_stp_net()
