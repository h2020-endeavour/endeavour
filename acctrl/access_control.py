#!/usr/bin/env python

import os
import sys


isdx_folder = "iSDX"
home = os.path.expanduser("~/")
isdx_path = home + isdx_folder
if isdx_path not in sys.path:
    sys.path.append(isdx_path)
import util.log

from rest import AccessControlApp
from xctrl.flowmodmsg import FlowModMsgBuilder

from influxdb import InfluxDBClient

# TODO: Pass it via configuration.
INFLUXDB_DB = "sdx"
INFLUXDB_HOST = "localhost"
INFLUXDB_PORT = 8086
INFLUXDB_USER = ""
INFLUXDB_PASS = ""

ICMP_PROTO = 1
UDP_PROTO = 17
TCP_PROTO = 6

# Anomalies    
UDP_SCAN = 1   # 1) UDP Network scan (UDP Network scan targeting one port)
LARGE_ICMP = 2 # 2) Large ICMP echo (Large ICMP echo targeting one IP destination)
ICMP_SCAN = 3  # 3) ICMP network scan (Large ICMP echo to multiple destinations)
RST_ATK = 4    # 4) RST attack (Large RST towards one destination)
MULTIPOINT = 5 # 5) Large Point Multipoint (Very large Point Multipoints percentage)

class AccessControl(object):
    
    def __init__(self, config, flows, sender, logger, **kwargs):
        self.logger = logger
        self.sender = sender
        self.config = config
        table_id = None
        self.fm_builder = FlowModMsgBuilder(0, self.config.flanc_auth["key"])
        try:
            table_id =  config.tables['access-control']
        except KeyError, e:
            print "Access Control table does not exists in the sdx_global.cfg file! - Add a table named %s." % str(e)
        # Build initial monitoring flows
        self.access_control_flows_builder(flows)

    def process_access_control_flows(self, data):
        if "access_control_flows" in data:
            self.access_control_flows_builder(data)
            self.sender.send(self.fm_builder.get_msg())
            return True
        return False

    # TODO  implement deletion
    #       implement flow to OSNT.
    def access_control_flows_builder(self, flows):
        # Forward the packets to the Access Control table of the pipeline
        if "access_control_flows" not in flows:
            return
        for flow in flows["access_control_flows"]:
            if "action" not in flow:
                actions = {"fwd": ["load-balancer"]}
            else:
                if "accept" in flow["action"]:
                    actions = {"fwd": ["load-balancer"]}
                else:
                    actions = flow["action"]
            dps = flow["dpids"]
            match = flow["match"]
            priority = flow["priority"]
            # Flow cookie is a tuple (cookie, cookie_mask)
            cookie = (flow["cookie"], flow["cookie_mask"])
            for dp in dps:
                self.fm_builder.add_flow_mod("insert", "access-control", priority, match, actions, self.config.dpid_2_name[dp], cookie)



    def start(self):
        # Push initial monitoring flows
        self.sender.send(self.fm_builder.get_msg())
        # Start REST 
        #mon = AccessControlApp(self)
        #mon.app.run()


