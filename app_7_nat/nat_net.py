from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.log import setLogLevel, info

from functools import partial
import threading
import time


def add_default_route(host):
    time.sleep(3)
    host.cmd('route add -net 0.0.0.0/0 gw 10.0.0.254')


def get_controller_info(msg='ryu'):
    if msg == 'ryu':
        ryu_info = {
            'ip':'10.207.51.119',
            'port':6633
        }
        return {
            'controller':partial(RemoteController, **ryu_info),
            'autoSetMacs':True
        }
    else:
        return {}


def get_host_info(n):
    return {
        'name':'h{}'.format(n),
        'ip':'10.0.0.{}/24'.format(n),
        'mac:':'00:00:00:00:00:0{}'.format(n)
    }


def create_nat_net():
    net = Mininet(**get_controller_info())

    info('*** Adding controller\n')
    c0 = net.addController()

    info('*** Adding switch\n')
    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')

    info('*** Adding hosts\n')
    h1 = net.addHost(**get_host_info(1))
    h2 = net.addHost(**get_host_info(2))
    h3 = net.addHost(**get_host_info(3))
    h4 = net.addHost(name='h4', ip='2.2.2.2/30', mac='aa:bb:cc:dd:ee:11')

    info('*** Adding links\n')
    net.addLink(s1, h1)
    net.addLink(s1, h2)
    net.addLink(s1, h3)
    net.addLink(s2, h4)
    net.addLink(s1, s2)

    info('*** Starting network\n')
    net.start()

    temp_thread = threading.Thread(target=add_default_route, args=(h1,))
    temp_thread.start()
    temp_thread = threading.Thread(target=add_default_route, args=(h2,))
    temp_thread.start()
    temp_thread = threading.Thread(target=add_default_route, args=(h3,))
    temp_thread.start()

    CLI(net)
    net.stop()


if __name__ == '__main__':

    setLogLevel('info')
    create_nat_net()
