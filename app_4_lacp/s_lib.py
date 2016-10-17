# -*- coding: UTF-8 -*-

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
from ryu.lib.packet import slow
from ryu.ofproto import ether
from ryu.lib.dpid import dpid_to_str
from ryu.ofproto import ofproto_v1_0

import time
import threading

# _count_wait_packet = 0


def wait_x_seconds(_t, note=None):
    if not (isinstance(_t, int) and _t <= 30 and _t >= 0):
        _t = 1
    # if note:
    #     print note
    # else:
    #     print 'wait {} sec'.format(_t)
    time.sleep(_t)
    # global _count_wait_packet
    # print _count_wait_packet, 'packets are waiting...'


class S_Lacp(lacplib.LacpLib):
    """docstring for S_Lacp"""
    def __init__(self):
        super(S_Lacp, self).__init__()
        self._s_lacp_1_p = True
        self._s_lacp_1_handler = True
        # self._s_lacp_2_p = True
        self._s_is_distributing = False

    def _s_create_lacp_first_packet(self, datapath, port):
        actor_system = datapath.ports[datapath.ofproto.OFPP_LOCAL].hw_addr
        req = slow.lacp(actor_key=13,
            actor_port=port,
            actor_port_priority=0xff,
            actor_state_activity=slow.lacp.LACP_STATE_ACTIVE,
            actor_state_aggregation=slow.lacp.LACP_STATE_AGGREGATEABLE,
            actor_state_defaulted=slow.lacp.LACP_STATE_DEFAULED_PARTNER,
            actor_state_expired=slow.lacp.LACP_STATE_EXPIRED,
            actor_system=actor_system,
            actor_system_priority=0xffff,
            partner_key=1,
            partner_port=port,
            partner_port_priority=0xff,
            partner_state_activity=slow.lacp.LACP_STATE_ACTIVE,
            partner_state_timeout=slow.lacp.LACP_STATE_SHORT_TIMEOUT,
            partner_system_priority=0xffff)
        self.logger.info("SW=%s PORT=%d LACP sent.",
                         dpid_to_str(datapath.id), port)
        self.logger.debug(str(req))
        return req

    def _s_create_eth_packet(self, datapath, port, lacp_packet):
        src = datapath.ports[port].hw_addr
        res_ether = ethernet.ethernet(
            slow.SLOW_PROTOCOL_MULTICAST, src, ether.ETH_TYPE_SLOW)
        res_pkt = packet.Packet()
        res_pkt.add_protocol(res_ether)
        res_pkt.add_protocol(lacp_packet)
        res_pkt.serialize()
        return res_pkt

    def _s_get_ports(self, dp):
        ports = []
        for bond in self._bonds:
            _dpid = bond.get(dp.id)
            if _dpid != None:
                for port in _dpid:
                    ports.append(port)
        return ports

    def _s_lacp_active(self, ev):
        datapath = ev.msg.datapath
        dpid = datapath.id
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        ports = self._s_get_ports(datapath)
        for port in ports:
            if not self._get_slave_enabled(dpid, port):
                self.logger.info(
                    "SW=%s PORT=%d the slave i/f has just been up.",
                    dpid_to_str(dpid), port)
                self._set_slave_enabled(dpid, port, True)
                self.send_event_to_observers(
                    lacplib.EventSlaveStateChanged(datapath, port, True))
            lacp_packet_1 = self._s_create_lacp_first_packet(datapath, port)
            eth_lacp_packet_1 = self._s_create_eth_packet(datapath, port, lacp_packet_1)
            out_port = port
            actions = [parser.OFPActionOutput(out_port)]
            out = parser.OFPPacketOut(datapath=datapath,
                buffer_id=ofproto.OFP_NO_BUFFER, data=eth_lacp_packet_1.data,
                in_port=ofproto.OFPP_CONTROLLER, actions=actions)
            datapath.send_msg(out)

    def _s_lacp_active_2(self, req_lacp, src, msg):
        # 将端口变为up，enabled
        # 修改timeout
        # 创建LACP报文，封装到ethernet中
        # 发送
        """packet-in process when the received packet is LACP."""
        datapath = msg.datapath
        dpid = datapath.id
        if dpid == 2:
            return
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        if ofproto.OFP_VERSION == ofproto_v1_0.OFP_VERSION:
            port = msg.in_port
        else:
            port = msg.match['in_port']
        self.logger.info("SW=%s PORT=%d LACP received.",
                         dpid_to_str(dpid), port)
        self.logger.debug(str(req_lacp))

        # when LACP arrived at disabled port, update the status of
        # the slave i/f to enabled, and send a event.
        if not self._get_slave_enabled(dpid, port):
            self.logger.info(
                "SW=%s PORT=%d the slave i/f has just been up.",
                dpid_to_str(dpid), port)
            self._set_slave_enabled(dpid, port, True)
            self.send_event_to_observers(
                EventSlaveStateChanged(datapath, port, True))

        # set the idle_timeout time using the actor state of the
        # received packet.
        if req_lacp.LACP_STATE_SHORT_TIMEOUT == \
           req_lacp.actor_state_timeout:
            idle_timeout = req_lacp.SHORT_TIMEOUT_TIME
        else:
            idle_timeout = req_lacp.LONG_TIMEOUT_TIME

        # when the timeout time has changed, update the timeout time of
        # the slave i/f and re-enter a flow entry for the packet from
        # the slave i/f with idle_timeout.
        if idle_timeout != self._get_slave_timeout(dpid, port):
            self.logger.info(
                "SW=%s PORT=%d the timeout time has changed.",
                dpid_to_str(dpid), port)
            self._set_slave_timeout(dpid, port, idle_timeout)
            func = self._add_flow.get(ofproto.OFP_VERSION)
            assert func
            func(src, port, idle_timeout, datapath)

        actor_system=datapath.ports[datapath.ofproto.OFPP_LOCAL].hw_addr
        if req_lacp.actor_state_synchronization == req_lacp.LACP_STATE_IN_SYNC:
            actor_state_collecting = req_lacp.LACP_STATE_COLLECTING_ENABLED
            actor_state_distributing = req_lacp.LACP_STATE_DISTRIBUTING_ENABLED
        elif req_lacp.actor_state_synchronization == req_lacp.LACP_STATE_OUT_OF_SYNC:
            actor_state_collecting = req_lacp.LACP_STATE_COLELCTING_DISABLED
            actor_state_distributing = req_lacp.LACP_STATE_DISTRIBUTING_DISABLED
        else:
            raise
        actor_state_synchronization = req_lacp.LACP_STATE_IN_SYNC
        # create a response packet.
        res = slow.lacp(#version=LACP_VERSION_NUMBER,
            actor_system_priority=0xffff,
            actor_system=actor_system,
            actor_key=req_lacp.actor_key,
            actor_port_priority=0xff,
            actor_port=req_lacp.actor_port,
            actor_state_activity=req_lacp.LACP_STATE_ACTIVE,
            actor_state_timeout=req_lacp.actor_state_timeout,
            actor_state_aggregation=req_lacp.actor_state_aggregation,
            actor_state_defaulted=req_lacp.actor_state_defaulted,
            actor_state_expired=req_lacp.actor_state_expired,
            actor_state_collecting=actor_state_collecting,
            actor_state_distributing=actor_state_distributing,
            actor_state_synchronization=actor_state_synchronization,
            partner_system_priority=req_lacp.actor_system_priority,
            partner_system=req_lacp.actor_system,
            partner_key=req_lacp.actor_key,
            partner_port_priority=req_lacp.actor_port_priority,
            partner_port=req_lacp.actor_port,
            partner_state_activity=req_lacp.actor_state_activity,
            partner_state_timeout=req_lacp.actor_state_timeout,
            partner_state_aggregation=req_lacp.actor_state_aggregation,
            partner_state_synchronization=req_lacp.actor_state_synchronization,
            partner_state_collecting=req_lacp.actor_state_collecting,
            partner_state_distributing=req_lacp.actor_state_distributing,
            partner_state_defaulted=req_lacp.actor_state_defaulted,
            partner_state_expired=req_lacp.actor_state_expired,
            collector_max_delay=0)

        # create a response packet.
        res_pkt = self._s_create_eth_packet(datapath, port, res)

        # packet-out the response packet.
        # out_port = port
        out_port = ofproto.OFPP_IN_PORT
        actions = [parser.OFPActionOutput(out_port)]
        # out = datapath.ofproto_parser.OFPPacketOut(
        #     datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
        #     data=res_pkt.data, in_port=port, actions=actions)
        out = parser.OFPPacketOut(
            datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
            data=res_pkt.data, in_port=port, actions=actions)
        datapath.send_msg(out)
        if req_lacp.actor_state_distributing == req_lacp.LACP_STATE_DISTRIBUTING_ENABLED:
            self._s_is_distributing = True

    def _s_wait_for_syn(self, ev):
        global _count_wait_packet
        _count_wait_packet += 1
        while not self._s_is_distributing:
            wait_x_seconds('wait 1 sec')
        self.send_event_to_observers(lacplib.EventPacketIn(ev.msg))

    def _s_wait_lacp_echo(self, req_lacp, src, msg):
        if self._s_is_distributing:
            wait_x_seconds(30, 'lacp echo')
        self._s_lacp_active_2(req_lacp, src, msg)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, evt):
        """PacketIn event handler. when the received packet was LACP,
        proceed it. otherwise, send a event."""        
        req_pkt = packet.Packet(evt.msg.data)
        (req_eth, ) = req_pkt.get_protocols(ethernet.ethernet)
        dst = req_eth.dst
        if dst[0:5] == "33:33":
            return
        if self._s_lacp_1_p:
            self._s_lacp_1_p = False
            self._s_lacp_active(evt)
            # self._s_wait_for_syn(evt)
            first_thread = threading.Thread(target=self._s_wait_for_syn, args=(evt, ))
            first_thread.start()
            return
        if slow.lacp in req_pkt:
            (req_lacp, ) = req_pkt.get_protocols(slow.lacp)
            if req_lacp.actor_state_activity == slow.lacp.LACP_STATE_PASSIVE:
                echo_thread = threading.Thread(target=self._s_wait_lacp_echo, args=(req_lacp, req_eth.src, evt.msg))
                echo_thread.start()
            elif req_lacp.actor_state_activity == slow.lacp.LACP_STATE_ACTIVE:
                # wait_x_seconds(2, 'syn passive')
                self._do_lacp(req_lacp, req_eth.src, evt.msg)
            else:
                raise
        elif not self._s_is_distributing:
            new_thread = threading.Thread(target=self._s_wait_for_syn, args=(evt, ))
            new_thread.start()
        else:
            self.send_event_to_observers(lacplib.EventPacketIn(evt.msg))
