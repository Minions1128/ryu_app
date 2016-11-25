# v1.1 
# add loop restrain and ignore ipv6 discovery packet

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types


class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    # Import ofproto.ofproto_v1_3
    # Import ofproto.ofproto_v1_3_parser

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        # mac address table, example:
        #     self.mac_to_port = {
        #         dpid1:{
        #             mac1:{port1},
        #             mac2:{port2}
        #         },
        #         dpid2:{
        #             mac3:{port3}
        #         }
        #     }
	self.loop_restrain = {}
	# {dpid:{(src,dst):port}}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
            Import ofproto.ofproto_v1_3_parser.OFPSwitchFeatures
            Encapsulated in feature reply message.
        """
        datapath = ev.msg.datapath
        # Import ryu.controller.controller
        ofproto = datapath.ofproto
        # Import ofproto.ofproto_v1_3
        parser = datapath.ofproto_parser
        # Import ofproto.ofproto_v1_3_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        # Import ofproto.ofproto_v1_3_parser.OFPMatch
        # i.e.. match all
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        # Import ofproto.ofproto_v1_3_parser.OFPActionOutput
        # First args means send to controller.
        # Second args indicates that no buffering should be
        # applied and the whole packet is to be
        # sent to the controller.
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        # Import ofproto.ofproto_v1_3_parser.OFPInstructionActions
        # Actions instruction 
        # This instruction writes/applies/clears the actions.
        # First args applies the action(s) immediately
        # Second args is actions
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
            # Import ofproto.ofproto_v1_3_parser.OFPFlowMod
            # Modify Flow entry message
            # The controller sends this message to modify the flow table.            
        datapath.send_msg(mod)
        # Queue an OpenFlow message to send to the corresponding switch.

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        # Import ???
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        # Structure like ofproto.ofproto_v1_3_parser.OFPMatch
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        # Obtain the first ethernet info

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src
        data = None

        if dst[0:5] == '33:33':
            # ignore ipv6 neighbor discovery packet in
            return

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        self.loop_restrain.setdefault(dpid, {})


        if (src, dst) in self.loop_restrain[dpid]:
            if self.loop_restrain[dpid][(src, dst)] != in_port:
                return
        self.loop_restrain[dpid][(src, dst)] = in_port

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        # Import ofproto.ofproto_v1_3_parser.OFPPacketOut
        datapath.send_msg(out)