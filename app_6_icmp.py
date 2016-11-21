from ryu.base import app_manager

from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls

from ryu.ofproto import ofproto_v1_3

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import icmp

class IcmpResponder(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(IcmpResponder, self).__init__(*args, **kwargs)
        self.hw_addr = 'aa:bb:cc:dd:ee:ff'
        self.ip_addr = '1.1.1.2'

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _switch_features_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        actions = [parser.OFPActionOutput(
            port=ofproto.OFPP_CONTROLLER,
            max_len=ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(
            type_=ofproto.OFPIT_APPLY_ACTIONS,
            actions=actions)]
        mod = parser.OFPFlowMod(datapath=datapath,
            priority=0, match=parser.OFPMatch(),
            instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        port = msg.match['in_port']
        pkt = packet.Packet(data=msg.data)
        eth_req = pkt.get_protocol(ethernet.ethernet)
        if not eth_req:
            return
        if eth_req.dst[0:5] == '33:33':
            return
        self.logger.info("PACKET_IN\n{}\n\n".format(pkt,))
        arp_req = pkt.get_protocol(arp.arp)
        if arp_req:
            self.arp_handler(datapath, port, eth_req,
                arp_req)
            return
        ipv4_req = pkt.get_protocol(ipv4.ipv4)
        icmp_req = pkt.get_protocol(icmp.icmp)
        if icmp_req:
            self.icmp_handler(datapath, port,
                eth_req, ipv4_req, icmp_req)
        return

    def arp_handler(self, dp, port, eth_req, arp_req):
        if arp_req.opcode != arp.ARP_REQUEST:
            return
        eth_rep = ethernet.ethernet(
            ethertype=eth_req.ethertype,
            dst=eth_req.src,
            src=self.hw_addr)
        arp_rep = arp.arp(opcode=arp.ARP_REPLY,
            src_mac=self.hw_addr,
            src_ip=self.ip_addr,
            dst_mac=arp_req.src_mac,
            dst_ip=arp_req.src_ip)
        pkt_rep = packet.Packet()
        pkt_rep.add_protocol(eth_rep)
        pkt_rep.add_protocol(arp_rep)
        self.send_packet(dp, port, pkt_rep)

    def icmp_handler(self, dp, port, eth_req, ipv4_req, icmp_req):
        if icmp_req.type != icmp.ICMP_ECHO_REQUEST:
            return
        eth_rep = ethernet.ethernet(
            ethertype=eth_req.ethertype,
            dst=eth_req.src,
            src=self.hw_addr)
        ipv4_rep = ipv4.ipv4(proto=ipv4_req.proto,
            dst=ipv4_req.src, src=self.ip_addr)
        icmp_rep = icmp.icmp(type_=icmp.ICMP_ECHO_REPLY,
            code=icmp.ICMP_ECHO_REPLY_CODE, csum=0,
            data=icmp_req.data)
        pkt = packet.Packet()
        pkt.add_protocol(eth_rep)
        pkt.add_protocol(ipv4_rep)
        pkt.add_protocol(icmp_rep)
        self.send_packet(dp, port, pkt)

    def send_packet(self, datapath, port, pkt):
        pkt.serialize()        
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        data = pkt.data
        actions = [parser.OFPActionOutput(port=port)]
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=ofproto.OFP_NO_BUFFER,
            in_port=ofproto.OFPP_CONTROLLER,
            actions=actions,
            data=data)
        datapath.send_msg(out)
        self.logger.info("PACKET_OUT\n{}\n\n".format(pkt,))
