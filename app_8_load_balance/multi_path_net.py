from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.log import setLogLevel, info

from functools import partial
import threading
import time


def get_controller_info(msg='ryu'):
    if msg == 'ryu':
        ryu_info = {
            'ip':'10.207.51.121',
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


def create_multi_path_net():
    net = Mininet(**get_controller_info())

    info('*** Adding controller\n')
    c0 = net.addController()

    info('*** Adding switches\n')
    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    s3 = net.addSwitch('s3')
    s4 = net.addSwitch('s4')

    info('*** Adding hosts\n')
    h1 = net.addHost(**get_host_info(1))
    h2 = net.addHost(**get_host_info(2))
    h3 = net.addHost(**get_host_info(3))

    info('*** Adding links\n')
    net.addLink(s1, h1, 1)
    net.addLink(s4, h2, 3)
    net.addLink(s4, h3, 4)
    net.addLink(s1, s2, 2, 1)
    net.addLink(s1, s3, 3, 1)
    net.addLink(s2, s4, 2, 1)
    net.addLink(s3, s4, 2, 2)

    net.start()
    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    create_multi_path_net()