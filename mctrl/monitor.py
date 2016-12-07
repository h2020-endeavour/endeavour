#!/usr/bin/env python

import os
import sys


isdx_folder = "iSDX"
home = os.path.expanduser("~/")
isdx_path = home + isdx_folder
if isdx_path not in sys.path:
    sys.path.append(isdx_path)
import util.log

from rest import MonitorApp 
from query import StatsCollector
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

class Monitor(object):
    
    def __init__(self, config, flows, sender, logger, **kwargs):
        self.logger = logger
        self.sender = sender
        self.config = config
        # collector is a class to execute queries for network status.
        self.collector = StatsCollector(InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USER, password=INFLUXDB_PASS, database=INFLUXDB_DB, timeout=10))
        table_id = None
        self.fm_builder = FlowModMsgBuilder(0, self.config.flanc_auth["key"])
        try:
            table_id =  config.tables['monitor']
        except KeyError, e:
            print "Monitoring table does not exists in the sdx_global.cfg file! - Add a table named %s." % str(e) 
        # Build initial monitoring flows
        self.monitor_flows_builder(flows)

    def process_anomaly_data(self, data):
        # Anomaly detection
        if "anomalies" in data:
            self.block_anomaly_traffic(data["switch"], data["anomalies"])
            return True
        return False

    def process_monitor_flows(self, data):
        if "monitor_flows" in data:
            self.monitor_flows_builder(data)
            self.sender.send(self.fm_builder.get_msg())
            return True
        return False

    # TODO  implement deletion
    #       implement flow to OSNT.
    def monitor_flows_builder(self, flows):
        # Forward the packets to the Monitor table of the pipeline
        #actions = {"fwd": ["access-control"]}
        actions = {"fwd": ["main-in"]}
        for flow in flows["monitor_flows"]:
            dps = flow["dpids"]
            match = flow["match"]
            priority = flow["priority"]
            # Flow cookie is a tuple (cookie, cookie_mask)
            cookie = (flow["cookie"], flow["cookie_mask"])
            for dp in dps:
                self.fm_builder.add_flow_mod("insert", "monitor", priority, match, actions, self.config.dpid_2_name[dp], cookie)


    def block_anomaly_traffic(self, switch, anomalies):
        for anomaly in anomalies:
            dp = switch
            # key_type = field, point = value of the field.
            match = {anomaly["key_type"]:anomaly["point"]}
            # Create an empty action set to drop packets.
            action = {}
            anomaly_id = anomaly["anomaly_id"]

            # Block protocol of the attack type.
            if anomaly_id == UDP_SCAN:
                # Add UDP port value.
                match["ip_proto"] = UDP_PROTO
            elif anomaly_id == LARGE_ICMP or ICMP_SCAN:
                match["ip_proto"] = ICMP_PROTO
            elif anomaly_id == RST_ATK:
                match["ip_proto"] = TCP_PROTO
                                            
        # TODO: ADD proper priority
        self.fm_builder.add_flow_mod("insert", "monitor", 1000, match, action, self.config.dpid_2_name[dp])
        # Push flow now.        
        self.sender.send(self.fm_builder.get_msg())

    def start(self):
        # Push initial monitoring flows
        self.sender.send(self.fm_builder.get_msg())
        # Start REST 
        mon = MonitorApp(self)
        mon.app.run()


