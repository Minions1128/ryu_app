# -*- coding: UTF-8 -*-


import urllib2
import json


def get_all_switches():
    """ para: none
        return: a list whitch contain switches info
        example:
            [
                {
                    "ports": [
                        {
                            "hw_addr": "12:ad:47:17:6d:1d",
                            "name": "s1-eth1",
                            "port_no": "00000001",
                            "dpid": "0000000000000001"
                        },
                        {
                            "hw_addr": "62:bf:89:79:68:67",
                            "name": "s1-eth2",
                            "port_no": "00000002",
                            "dpid": "0000000000000001"
                        }
                    ],
                    "dpid": "0000000000000001"
                },
                {
                    "ports": [
                        {
                            "hw_addr": "da:d7:cb:f8:a4:7f",
                            "name": "s2-eth1",
                            "port_no": "00000001",
                            "dpid": "0000000000000002"
                        },
                        {
                            "hw_addr": "ce:31:74:a1:c1:2d",
                            "name": "s2-eth2",
                            "port_no": "00000002",
                            "dpid": "0000000000000002"
                        }
                    ],
                    "dpid": "0000000000000002"
                },
                {
                    "ports": [
                        {
                            "hw_addr": "ea:c5:e8:ee:72:f7",
                            "name": "s3-eth1",
                            "port_no": "00000001",
                            "dpid": "0000000000000003"
                        },
                        {
                            "hw_addr": "da:57:80:b2:74:67",
                            "name": "s3-eth2",
                            "port_no": "00000002",
                            "dpid": "0000000000000003"
                        }
                    ],
                    "dpid": "0000000000000003"
                }
            ]
        """
    url = "http://127.0.0.1:8080/v1.0/topology/switches"
    req = urllib2.Request(url)
    res_data = urllib2.urlopen(req)
    res = res_data.read()
    res = json.loads(res)
    return res


def get_all_links():
    """ para: none
        return: a list whitch contain links info
        example:
            [
                {
                    "src": {
                        "hw_addr": "12:ad:47:17:6d:1d",
                        "name": "s1-eth1",
                        "port_no": "00000001",
                        "dpid": "0000000000000001"
                    },
                    "dst": {
                        "hw_addr": "da:d7:cb:f8:a4:7f",
                        "name": "s2-eth1",
                        "port_no": "00000001",
                        "dpid": "0000000000000002"
                    }
                },
                {
                    "src": {
                        "hw_addr": "ea:c5:e8:ee:72:f7",
                        "name": "s3-eth1",
                        "port_no": "00000001",
                        "dpid": "0000000000000003"
                    },
                    "dst": {
                        "hw_addr": "ce:31:74:a1:c1:2d",
                        "name": "s2-eth2",
                        "port_no": "00000002",
                        "dpid": "0000000000000002"
                    }
                },
                {
                    "src": {
                        "hw_addr": "da:d7:cb:f8:a4:7f",
                        "name": "s2-eth1",
                        "port_no": "00000001",
                        "dpid": "0000000000000002"
                    },
                    "dst": {
                        "hw_addr": "12:ad:47:17:6d:1d",
                        "name": "s1-eth1",
                        "port_no": "00000001",
                        "dpid": "0000000000000001"
                    }
                },
                {
                    "src": {
                        "hw_addr": "ce:31:74:a1:c1:2d",
                        "name": "s2-eth2",
                        "port_no": "00000002",
                        "dpid": "0000000000000002"
                    },
                    "dst": {
                        "hw_addr": "ea:c5:e8:ee:72:f7",
                        "name": "s3-eth1",
                        "port_no": "00000001",
                        "dpid": "0000000000000003"
                    }
                }
            ]
        """
    url = "http://127.0.0.1:8080/v1.0/topology/links"
    req = urllib2.Request(url)
    res_data = urllib2.urlopen(req)
    res = res_data.read()
    res = json.loads(res)
    return res


def get_switch(dpid):
    """ para: dpid is a string, i,e., "0000000000000001"
        return: a list whitch contain this switch info
        example:
            [
                {
                    "ports": [
                        {
                            "hw_addr": "12:ad:47:17:6d:1d",
                            "name": "s1-eth1",
                            "port_no": "00000001",
                            "dpid": "0000000000000001"
                        },
                        {
                            "hw_addr": "62:bf:89:79:68:67",
                            "name": "s1-eth2",
                            "port_no": "00000002",
                            "dpid": "0000000000000001"
                        }
                    ],
                    "dpid": "0000000000000001"
                }
            ]
        """
    url = "http://127.0.0.1:8080/v1.0/topology/switches/" + dpid
    req = urllib2.Request(url)
    res_data = urllib2.urlopen(req)
    res = res_data.read()
    res = json.loads(res)
    return res


def get_flow_entries(dpid):
    """ para: dpid is a string, i,e., "0000000000000001"
        return: a dict whitch contain this flow tables
        example:
            {
                "1": [
                    {
                        "actions": [
                            "OUTPUT:65533"
                        ],
                        "idle_timeout": 0,
                        "cookie": 0,
                        "packet_count": 2252,
                        "hard_timeout": 0,
                        "byte_count": 114852,
                        "duration_nsec": 370000000,
                        "priority": 65535,
                        "duration_sec": 2026,
                        "table_id": 0,
                        "match": {
                            "dl_type": 35020,
                            "nw_dst": "0.0.0.0",
                            "dl_vlan_pcp": 0,
                            "dl_src": "00:00:00:00:00:00",
                            "nw_tos": 0,
                            "tp_src": 0,
                            "dl_vlan": 0,
                            "nw_src": "0.0.0.0",
                            "nw_proto": 0,
                            "tp_dst": 0,
                            "dl_dst": "01:80:c2:00:00:0e",
                            "in_port": 0
                        }
                    },
                    {
                        "actions": [
                            "OUTPUT:2"
                        ],
                        "idle_timeout": 0,
                        "cookie": 0,
                        "packet_count": 0,
                        "hard_timeout": 0,
                        "byte_count": 0,
                        "duration_nsec": 864000000,
                        "priority": 1111,
                        "duration_sec": 104,
                        "table_id": 0,
                        "match": {
                            "dl_type": 0,
                            "nw_dst": "0.0.0.0",
                            "dl_vlan_pcp": 0,
                            "dl_src": "00:00:00:00:00:00",
                            "nw_tos": 0,
                            "tp_src": 0,
                            "dl_vlan": 0,
                            "nw_src": "0.0.0.0",
                            "nw_proto": 0,
                            "tp_dst": 0,
                            "dl_dst": "00:00:00:00:00:00",
                            "in_port": 1
                        }
                    }
                ]
            }
        """
    url = "http://127.0.0.1:8080/stats/flow/" + dpid
    req = urllib2.Request(url)
    res_data = urllib2.urlopen(req)
    res = res_data.read()
    res = json.loads(res)
    return res


def add_flow_entry(dpid, match, priority, actions):
    """ para: dpid, match, priority, actions
        return: int, http status code, 200 stands for success.
        example: 200, 403, 404
        """
    url = "http://127.0.0.1:8080/stats/flowentry/add"
    post_data = "{'dpid':%s,'match':%s,'priority':%s,'actions':%s}" % (dpid,str(match),priority,str(actions))
    req = urllib2.Request(url,post_data)
    res = urllib2.urlopen(req)
    return res.getcode()


def delete_flow_entry(dpid, match=None, priority=None, actions=None):
    """ para: dpid, match, priority, actions
        return: int, http status code, 200 stands for success.
        example: 200, 403, 404
        """
    url = "http://127.0.0.1:8080/stats/flowentry/delete"
    post_data = "{'dpid':%s" % dpid
    if match is not None:
        post_data += ",'match':%s" % str(match)
    if priority is not None:
        post_data += ",'priority':%s" % priority
    if actions is not None:
        post_data += ",'actions':%s" % str(actions)
    post_data += "}"
    req = urllib2.Request(url,post_data)
    res = urllib2.urlopen(req)
    return res.getcode()
