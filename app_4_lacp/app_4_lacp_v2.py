from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import lacplib
from ryu.lib.dpid import str_to_dpid
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from s_lib import S_Lacp


class SimpleSwitchLacp13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'lacplib':S_Lacp}

    def __init__(self, *args, **kwargs):
        super(SimpleSwitchLacp13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self._s_ports = [1, 2]
        self._lacp = kwargs['lacplib']
        self._lacp.add(
            dpid=str_to_dpid('0000000000000001'),
            ports=self._s_ports)
        self._lacp.add(
            dpid=str_to_dpid('0000000000000002'),
            ports=self._s_ports)
        self.loop_restrain = {}
        # {dpid:{(src,dst):port}}

    def add_flow(self, datapath, priority, match, actions):
        # the same with simple_switch_13
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS,
            actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority, match=match,
            instructions=inst)
        datapath.send_msg(mod)

    def del_flow(self, dp, match):
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        mod = parser.OFPFlowMod(
            datapath=dp, match=match,
            command=ofproto.OFPFC_DELETE,
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY)
        # command=ofproto.OFPFC_DELETE
        dp.send_msg(mod)

    def _s_get_other_ports(in_port):
        other_ports = []
        for port in self._s_ports:
            if port != in_port:
                other_ports.append(port)
        return other_ports

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        # the same with simple switch 13
        dp = ev.msg.datapath
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(
            ofproto.OFPP_CONTROLLER,
            ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(dp, 0, match, actions)

    @set_ev_cls(lacplib.EventPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        in_port = msg.match['in_port']
        # acquire in_port info of version OF 1.3
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        dst = eth.dst
        src = eth.src
        dpid = dp.id
        self.mac_to_port.setdefault(dpid, {})
        self.loop_restrain.setdefault(dpid, {})
        if (src, dst) in self.loop_restrain[dpid]:
            if self.loop_restrain[dpid][(src, dst)] != in_port:
                return
        self.loop_restrain[dpid][(src, dst)] = in_port
        # default mac address table
        self.logger.info("packet in [dpid]=%s [src]=%s [dst]=%s [in_port]=%s",
            dpid, src, dst, in_port)
        if in_port in self._s_ports:
            self.mac_to_port[dpid][src] = 'bond1'
        else:
            self.mac_to_port[dpid][src] = in_port
        if dst in self.mac_to_port[dpid]:
            if self.mac_to_port[dpid][dst] == 'bond1':
                out_port = int(src[len(src)-2:len(src)], 16) % len(self._s_ports) + 1
            else:
                out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD
        actions = [parser.OFPActionOutput(out_port)]
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(dp, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = parser.OFPPacketOut(datapath=dp,
                buffer_id=msg.buffer_id, in_port=in_port,
                actions=actions, data=data)
        dp.send_msg(out)

    @set_ev_cls(lacplib.EventSlaveStateChanged, MAIN_DISPATCHER)
    def _slave_state_changed_handler(self, ev):
        # delete the flow entry and mac table of slave port
        dp = ev.datapath
        dpid = dp.id
        port_no = ev.port
        enabled = ev.enabled
        if enabled:
            self.logger.info("Slave State changed, Port: %d is Up",
                port_no)
        else:
            self.logger.info("Slave State changed, Port: %d is Down", 
                port_no)
            self._lacp._s_lacp_1_p = True
        if dpid in self.mac_to_port:
            for mac in self.mac_to_port[dpid]:
                match = dp.ofproto_parser.OFPMatch(eth_dst=mac)
                self.del_flow(dp, match)
            del self.mac_to_port[dpid]
        self.mac_to_port.setdefault(dpid, {})
