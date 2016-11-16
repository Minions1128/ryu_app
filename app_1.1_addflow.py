# add flow table

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.app import simple_switch_13


class AutoAddflowSwitch(simple_switch_13.SimpleSwitch13):
    def __init__(self, *args, **kwargs):
        super(AutoAddflowSwitch, self).__init__(*args, **kwargs)     

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def auto_add_flow(self, ev):
        datapath = ev.msg.datapath
        dpid = datapath.id
        parser = datapath.ofproto_parser
        port1 = 1
        port2 = 2
        port3 = 3
        mac_h1 = '00:00:00:00:00:01'
        mac_h2 = '00:00:00:00:00:02'
        mac_h3 = '00:00:00:00:00:03'

        actions1 = [parser.OFPActionOutput(port1)]
        actions2 = [parser.OFPActionOutput(port2)]
        actions3 = [parser.OFPActionOutput(port3)]

        if dpid == 1:
            match1_1 = parser.OFPMatch(eth_dst=mac_h1)
            match1_2 = parser.OFPMatch(eth_dst=mac_h2)
            match1_3 = parser.OFPMatch(eth_dst=mac_h3)

            self.add_flow(datapath, 1, match1_1, actions1)
            self.add_flow(datapath, 1, match1_2, actions2)
            self.add_flow(datapath, 1, match1_3, actions2)
        elif dpid == 2:
            match2_1 = parser.OFPMatch(eth_dst=mac_h1)
            match2_2 = parser.OFPMatch(eth_dst=mac_h2)
            match2_3 = parser.OFPMatch(eth_dst=mac_h3)

            self.add_flow(datapath, 1, match2_1, actions2)
            self.add_flow(datapath, 1, match2_2, actions1)
            self.add_flow(datapath, 1, match2_3, actions3)
        elif dpid == 3:
            match3_1 = parser.OFPMatch(eth_dst=mac_h1)        
            match3_2 = parser.OFPMatch(eth_dst=mac_h2)
            match3_3 = parser.OFPMatch(eth_dst=mac_h3)

            self.add_flow(datapath, 1, match3_1, actions2)
            self.add_flow(datapath, 1, match3_2, actions2)
            self.add_flow(datapath, 1, match3_3, actions1)
        else:
            print 'no such a switch...'
