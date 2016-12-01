#!/usr/bin/env python

import json
import logging
import os
import sys
from collections import namedtuple
from netaddr import IPNetwork

isdx_folder = "iSDX"
home = os.path.expanduser("~/")
isdx_path = home + isdx_folder
if isdx_path not in sys.path:
    sys.path.append(isdx_path)
import util.log

class Config(object):
    def __init__(self, config_file):
        # Connections between core and edge
        # TODO: do I really need all this information?
        self.dpids = {}
        self.dpid_2_name = {}
        self.participants = {}
        self.tables = {}
        self.refmon =  None
        self.flanc_auth = None
        self.route_server = None
        self.arp_proxy = None
        self.vnhs = None
        config = json.load(open(config_file, 'r'))

        # TODO: Parsing of configuration information should 
        # be moved to a lib to avoid the repetition
        if "RefMon Server" in config:
            self.refmon = config["RefMon Server"]

        if "Flanc Auth Info" in config:
            self.flanc_auth = config["Flanc Auth Info"]

        if "Route Server" in config:
            route_server = config["Route Server"]
            self.route_server = Port(route_server['Port'], route_server["MAC"], route_server["IP"], route_server["switch"], route_server["ASN"])
        if "ARP Proxy" in config:
            arp_proxy = config["ARP Proxy"]
            # Arp proxy ASN does not make sense. It is here because
            # I do not want another named tuple only for this case
            self.arp_proxy = Port(arp_proxy['Port'], arp_proxy["MAC"], arp_proxy["IP"], arp_proxy["switch"], route_server["ASN"])

        if "Participants" in config:
            self.participants = config["Participants"]

        if "RefMon Settings" in config:
            if "dpids" in config["RefMon Settings"]["fabric options"]:
                    self.dpids = config["RefMon Settings"]["fabric options"]["dpids"]
                    for k,v in self.dpids.iteritems():
                        self.dpid_2_name[v] = k
            if "tables" in config["RefMon Settings"]["fabric options"]:
                self.tables = self.dpids = config["RefMon Settings"]["fabric options"]["tables"]
        if "VNHs" in config:
            self.vnhs = IPNetwork(config["VNHs"])
        
Port = namedtuple('Port', "id mac ip switch asn")
