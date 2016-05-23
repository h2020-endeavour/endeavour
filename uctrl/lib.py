#!/usr/bin/env python

import json
import logging
import os
import sys
import copy
from collections import namedtuple
from netaddr import IPNetwork

isdx_folder = "iSDX"
home = os.path.expanduser("~/")
isdx_path = home + isdx_folder
if isdx_path not in sys.path:
    sys.path.append(isdx_path)
#import util.log

class Config(object):
    def __init__(self, config_file):
        # Connections between core and edge
        # TODO: do I really need all this information?
        self.dpids = {}
        self.dpid_2_name = {}
        self.core_edge = {}
        self.edges = {}
        self.edge_peers = {}
        self.edge_to_edge = {}
        self.edge_core = {}
        self.participants = {}
        self.refmon =  None
        self.flanc_auth = None
        self.route_server = None
        self.arp_proxy = None
        self.vnhs = None
        config = json.load(open(config_file, 'r'))

        if "RefMon Server" in config:
            self.refmon = config["RefMon Server"]

        if "Flanc Auth Info" in config:
            self.flanc_auth = config["Flanc Auth Info"]

        if "Route Server" in config:
            route_server = config["Route Server"]
            self.route_server = RS(route_server['Port'], route_server["MAC"], route_server["IP"], route_server["switch"], route_server["ASN"])

        if "ARP Proxy" in config:
            arp_proxy = config["ARP Proxy"]
            self.arp_proxy = Port(arp_proxy['Port'], arp_proxy["MAC"], arp_proxy["IP"], arp_proxy["switch"])

        if "Participants" in config:
            self.participants = config["Participants"]

        if "RefMon Settings" in config:
            if "fabric options" in config["RefMon Settings"]:
                datapaths = config["RefMon Settings"]["fabric options"]["dpids"]
                self.edges = {x:datapaths[x] for x in datapaths if x.find('edge') == 0}
                cores = {x:datapaths[x] for x in datapaths if x.find('core') == 0}

            if "dpids" in config["RefMon Settings"]["fabric options"]:
                    self.dpids = config["RefMon Settings"]["fabric options"]["dpids"]
                    for k,v in self.dpids.iteritems():
                        self.dpid_2_name[v] = k

            if "fabric connections" in config["RefMon Settings"]:
                datapaths_conns = config["RefMon Settings"]["fabric connections"]
                for dp in edges:
                    self.edge_peers.setdefault(self.dpids[dp], {})
                    if dp in datapaths_conns:
                        edge = edges[dp]
                        self.parse_edge_core(edge, cores, datapaths_conns[dp])
                        self.parse_edge_to_edge(edge, edges, datapaths_conns[dp])
                self.parse_edge_peers(datapaths_conns)
                for dp in cores:
                    if dp in datapaths_conns:
                        core = cores[dp]
                        self.parse_core_edge(core, edges, datapaths_conns[dp])

                #  ARP proxy and Route Server are not peers but forwarding in 
                #  umbrella  is the same for every node connected to the 
                #  edges of the fabric
                self.edge_peers[self.dpids[self.arp_proxy.switch]][self.arp_proxy] = self.arp_proxy.id
                self.edge_peers[self.dpids[self.route_server.switch]][self.route_server] = self.route_server.id
        if "VNHs" in config:
            self.vnhs = IPNetwork(config["VNHs"])

    def parse_edge_peers(self, dp_conns):
        for dp in dp_conns:
            links = dp_conns[dp]
            for p in links:
                ports = links[p]
                if isinstance(ports, int):
                    ports = [ports]
                i = 0
                if p in self.participants:
                    for port in self.participants[p]["Ports"]:
                         if port["switch"] == dp:
                            port = Port(port['Id'], port["MAC"], port["IP"], port["switch"])
                            dpid = self.dpids[dp]
                            self.edge_peers[dpid][port] = ports[i]
                            i += 1
                            #print self.edge_peers

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
 
Port = namedtuple('Port', "id mac ip switch")
RS = namedtuple('RS', "id mac ip switch asn")