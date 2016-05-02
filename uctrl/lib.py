#!/usr/bin/env python

import json
import logging
import os
import sys
from collections import namedtuple

isdx_folder = "iSDX"
home = os.path.expanduser("~/")
isdx_path = home + isdx_folder
if isdx_path not in sys.path:
    sys.path.append(isdx_path)
#import util.log

class Config(object):
    def __init__(self, config_file):
        # Connections between core and edge
        self.core_edge = {}
        self.edge_peers = {}
        self.edge_to_edge = {}
        self.edge_core = {}
        self.participants = {}
        self.refmon =  None
        self.flanc_auth = None
        self.route_server = None
        self.arp_proxy = None
        config = json.load(open(config_file, 'r'))

        if "RefMon Server" in config:
            self.refmon = config["RefMon Server"]

        if "Flanc Auth Info" in config:
            self.flanc_auth = config["Flanc Auth Info"]

        if "Route Server" in config:
            self.route_server = config["Route Server"]

        if "ARP Proxy" in config:
            self.arp_proxy = config["ARP Proxy"]

        if "Participants" in config:
            self.participants = config["Participants"]

        if "RefMon Settings" in config:
            if "fabric options" in config["RefMon Settings"]:
                datapaths = config["RefMon Settings"]["fabric options"]["dpids"]
                edges = {x:datapaths[x] for x in datapaths if x.find('edge') == 0}
                cores = {x:datapaths[x] for x in datapaths if x.find('core') == 0}
            if "fabric connections" in config["RefMon Settings"]:
                datapaths_conns = config["RefMon Settings"]["fabric connections"]
                for dp in edges:
                    if dp in datapaths_conns:
                        edge = edges[dp]
                        self.parse_edge_peers(edge, self.participants, datapaths_conns[dp])
                        self.parse_edge_core(edge, cores, datapaths_conns[dp])
                        self.parse_edge_to_edge(edge, edges, datapaths_conns[dp])
                for dp in cores:
                    if dp in datapaths_conns:
                        core = cores[dp]
                        self.parse_core_edge(core, edges, datapaths_conns[dp])

    # Code could be simpler with a different specification of configuration
    # However, we want as few as possible modifications to iSDX
    def parse_edge_peers(self, edge, participants, dp_conns):
        self.edge_peers.setdefault(edge, {})
        for conn in dp_conns:
            # Only peer connections
            if conn in participants:
                ports = participants[conn]["Ports"]
                # Eder: Would be interesting to have peers per ports in the
                # configuration file?
                # peers = participants[conn]["Peers"]
                for port in ports:
                    ip = port["IP"]
                    mac = port["MAC"]
                    port = Port(mac, ip)
                    self.edge_peers[edge][port] = dp_conns[conn]


    # Builds a list with:
    # edge dp id - core dp id -> port
    def parse_edge_core(self, edge, cores, dp_conns):
        self.edge_core.setdefault(edge, {})
        for dp in dp_conns:
            if dp in cores:
                dpid = cores[dp]
                self.edge_core[edge][dpid] = dp_conns[dp]

    def parse_core_edge(self, core, edges, dp_conns):
        self.core_edge.setdefault(core, {})
        for dp in dp_conns:
            if dp in edges:
                dpid = edges[dp]
                self.core_edge[core][dpid] = dp_conns[dp]

    def parse_edge_to_edge(self, edge, edges, dp_conns):
        self.edge_to_edge.setdefault(edge, {})
        for dp in dp_conns:
            if dp in edges:
                self.edge_to_edge[edge][dp] = dp_conns[dp]

Port = namedtuple('Peer', "mac ip")
