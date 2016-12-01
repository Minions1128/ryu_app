""" 1.3
    add vlan function in 3 switches, implement 'trunk' port
    we need to define vlan table stored on self.vlan_to_port
    the example topology is:


                 h1   h4   h6
                 |    |    |
            h2--sw1--sw2--sw3--h7
                 |    |    |
                h3   h4   h5

    h1, h3, h5, h7 belongs vlan 10
    h2, h4, h6, h8 belongs vlan 20
    links between s1, s2 and s2, s3 are trunk
    """


from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

from ryu.lib import dpid as dpid_lib
from ryu.lib.packet import vlan

TRUNK_VLAN = 0


class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.vlan_to_port = {
            dpid_lib.str_to_dpid('0000000000000001'):
                {1:10, 2:20, 3:10, 4:TRUNK_VLAN},
            dpid_lib.str_to_dpid('0000000000000002'):
                {1:20, 2:10, 3:TRUNK_VLAN, 4:TRUNK_VLAN},
            dpid_lib.str_to_dpid('0000000000000003'):
                {1:20, 2:10, 3:20, 4:TRUNK_VLAN}

        }
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler_for_2_switch(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        dst = eth.dst
        src = eth.src
        data = None
        if dst[0:5] == '33:33':
            return
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        self.logger.info("packet in dpid:%s %s %s in_port:%s", dpid, src, dst, in_port)
        in_port_is_trunk = (self.vlan_to_port[dpid][in_port] == TRUNK_VLAN)
        if in_port_is_trunk:
            data, vlan = self.de_encapsulate_dot1q(pkt)
        else:
            vlan = self.vlan_to_port[dpid][in_port]
        self.mac_to_port[dpid].setdefault(vlan, {})
        self.mac_to_port[dpid][vlan][src] = in_port
        out_ports = []
        if dst in self.mac_to_port[dpid][vlan]:
            is_add_flow = True
            out_ports.append(self.mac_to_port[dpid][vlan][dst])
        else:
            is_add_flow = False
            for port in self.vlan_to_port[dpid]:
                if port == in_port:
                    continue
                if self.vlan_to_port[dpid][port] == vlan:
                    out_ports.append(port)
        actions = []
        for out_port in out_ports:
            actions.append(parser.OFPActionOutput(out_port))
        # if is_add_flow and not in_port_is_trunk:
        if is_add_flow:
            match = parser.OFPMatch(in_port=in_port,
                eth_dst=dst, eth_src=src)
            self.add_flow(datapath, 1, match, actions)
        if in_port_is_trunk:
            out = parser.OFPPacketOut(datapath=datapath,
                buffer_id=ofproto.OFP_NO_BUFFER, in_port=in_port,
                actions=actions, data=data.data)
        else:
            data = msg.data
            out = parser.OFPPacketOut(datapath=datapath,
                buffer_id=ofproto.OFP_NO_BUFFER, in_port=in_port,
                actions=actions, data=data)

        trunk_ports = []
        for port in self.vlan_to_port[dpid]:
            if self.vlan_to_port[dpid][port] == TRUNK_VLAN:
                trunk_ports.append(port)
        for p in out_ports:
            if self.vlan_to_port[dpid][p] == TRUNK_VLAN:
                break
        else:
            datapath.send_msg(out)
        trunk_actions = []
        for trunk_port in trunk_ports:
            trunk_actions.append(
                parser.OFPActionOutput(trunk_port))
        trunk_data = self.encapsulate_dot1q(pkt, vlan)
        trunk_out = parser.OFPPacketOut(datapath=datapath,
            buffer_id=ofproto.OFP_NO_BUFFER, in_port=in_port,
            actions=trunk_actions, data=trunk_data.data)
        datapath.send_msg(trunk_out)

    # @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    # def packet_in_handler_for_2_switch(self, ev):
    #     msg = ev.msg
    #     datapath = msg.datapath
    #     ofproto = datapath.ofproto
    #     parser = datapath.ofproto_parser
    #     in_port = msg.match['in_port']
    #     pkt = packet.Packet(msg.data)
    #     eth = pkt.get_protocols(ethernet.ethernet)[0]
    #     if eth.ethertype == ether_types.ETH_TYPE_LLDP:
    #         return
    #     dst = eth.dst
    #     src = eth.src
    #     data = None
    #     if dst[0:5] == '33:33':
    #         return
    #     dpid = datapath.id
    #     self.mac_to_port.setdefault(dpid, {})
    #     self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)
    #     in_port_is_trunk = (self.vlan_to_port[dpid][in_port] == TRUNK_VLAN)
    #     if in_port_is_trunk:
    #         data, vlan = self.de_encapsulate_dot1q(pkt)
    #     else:
    #         vlan = self.vlan_to_port[dpid][in_port]
    #     self.mac_to_port[dpid].setdefault(vlan, {})
    #     self.mac_to_port[dpid][vlan][src] = in_port
    #     out_ports = []
    #     if dst in self.mac_to_port[dpid][vlan]:
    #         is_add_flow = True
    #         out_ports.append(self.mac_to_port[dpid][vlan][dst])
    #     else:
    #         is_add_flow = False
    #         for port in self.vlan_to_port[dpid]:
    #             if port == in_port:
    #                 continue
    #             if self.vlan_to_port[dpid][port] == vlan:
    #                 out_ports.append(port)
    #     actions = []
    #     for out_port in out_ports:
    #         actions.append(parser.OFPActionOutput(out_port))
    #     if is_add_flow:
    #         match = parser.OFPMatch(in_port=in_port,
    #             eth_dst=dst, eth_src=src)
    #         self.add_flow(datapath, 1, match, actions)
    #     if in_port_is_trunk:
    #         out = parser.OFPPacketOut(datapath=datapath,
    #             buffer_id=ofproto.OFP_NO_BUFFER, in_port=in_port,
    #             actions=actions, data=data.data)
    #     else:
    #         data = msg.data
    #         out = parser.OFPPacketOut(datapath=datapath,
    #             buffer_id=ofproto.OFP_NO_BUFFER, in_port=in_port,
    #             actions=actions, data=data)
    #     datapath.send_msg(out)
    #     trunk_ports = []
    #     for port in self.vlan_to_port[dpid]:
    #         if self.vlan_to_port[dpid][port] == TRUNK_VLAN:
    #             trunk_ports.append(port)
    #     trunk_actions = []
    #     for trunk_port in trunk_ports:
    #         trunk_actions.append(
    #             parser.OFPActionOutput(trunk_port))
    #     trunk_data = self.encapsulate_dot1q(pkt, vlan)
    #     trunk_out = parser.OFPPacketOut(datapath=datapath,
    #         buffer_id=ofproto.OFP_NO_BUFFER, in_port=in_port,
    #         actions=trunk_actions, data=trunk_data.data)
    #     datapath.send_msg(trunk_out)
    #     datapath.send_msg(out)

    def encapsulate_dot1q(self, pkt, tag):
        eth = pkt.get_protocol(ethernet.ethernet)
        if not eth:
            return
        e = pkt.protocols.pop(0)
        assert(eth == e)
        eth_rep = ethernet.ethernet(
            ethertype=ether_types.ETH_TYPE_8021Q,
            dst=eth.dst, src=eth.src)
        vlan_rep = vlan.vlan(vid=tag,
            ethertype=eth.ethertype)
        pkt.protocols.insert(0, eth_rep)
        pkt.protocols.insert(1, vlan_rep)
        pkt.serialize()
        return pkt

    def de_encapsulate_dot1q(self, pkt):
        eth_req = pkt.get_protocol(ethernet.ethernet)
        vlan_req = pkt.get_protocol(vlan.vlan)
        if not vlan_req:
            print pkt
            raise 'not 802.1q encapsulated packet'
        e = pkt.protocols.pop(0)
        v = pkt.protocols.pop(0)
        assert e == eth_req
        assert v == vlan_req
        eth_rep = ethernet.ethernet(
            ethertype=vlan_req.ethertype,
            dst=eth_req.dst, src=eth_req.src)
        pkt.protocols.insert(0, eth_rep)
        pkt.serialize()
        tag = vlan_req.vid
        return pkt, tag
