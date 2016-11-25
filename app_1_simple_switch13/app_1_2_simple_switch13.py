# 1.2 
# add vlan function in one switch
# we need to define vlan table stored on self.vlan_to_port
# the topology we need is linear topo


from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

from ryu.lib import dpid as dpid_lib


class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.vlan_to_port = {1:10, 2:20, 3:10, 4:20, 5:10, 6:20}
        self.mac_to_port = {}
        # self.mac_to_port = {
        #     dpid1:{
        #         vlan1:{
        #             mac1:port1,
        #             mac2:port2
        #         },
        #         vlan2:{mac3:port3}
        #     },
        #     dpid2:{}
        # }

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
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler_for_1_switch(self, ev):
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
        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)
        vlan = self.vlan_to_port[in_port]
        self.mac_to_port[dpid].setdefault(vlan, {})
        self.mac_to_port[dpid][vlan][src] = in_port
        out_ports = []
        is_add_flow = True
        if dst in self.mac_to_port[dpid][vlan]:
            out_ports.append(self.mac_to_port[dpid][vlan][dst])
        else:
            is_add_flow = False
            for port in self.vlan_to_port:
                if port == in_port:
                    continue
                if self.vlan_to_port[port] == vlan:
                    # or self.vlan_to_port[port] == 0
                    out_ports.append(port)
        actions = []
        for out_port in out_ports:
            actions.append(parser.OFPActionOutput(out_port))
        if is_add_flow:
            match = parser.OFPMatch(in_port=in_port,
                eth_dst=dst, eth_src=src)
            self.add_flow(datapath, 1, match, actions)
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = parser.OFPPacketOut(datapath=datapath,
            buffer_id=msg.buffer_id, in_port=in_port,
            actions=actions, data=data)
        datapath.send_msg(out)
