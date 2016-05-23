#!/usr/bin/env python
import random
from ryu.ofproto import parser

# Not supposed to be something dynamic, for now.
class Load_Balancer(object):
    def __init__(self):
        # Edge output ports in order of preference
        # It will be calculated in the load_balance method
        self.edge_out_ports = {}

    def lb_policy(self, edge_core):
        raise NotImplementedError

    def lb_action(self, edge):
        raise NotImplementedError


class Dummy_LBalancer(Load_Balancer):
    def __init__(self):
        super(Dummy_LBalancer, self).__init__()

    def lb_policy(self, edge_core):
        for edge in edge_core:
            self.edge_out_ports.setdefault(edge, {})
            core = random.choice([x for x in edge_core[edge]])
            self.edge_out_ports[edge] = (core, edge_core[edge][core])

    def lb_action(self, edge):
        return self.edge_out_ports[edge]



class IP_LBalancer(Load_Balancer):
    def __init__(self, config):
        super(IP_LBalancer, self).__init__()




    def lb_policy(self, edge_core):
        for edge in edge_core:
            print "edge_core: %s" % edge_core
            self.edge_out_ports.setdefault(edge, {})
            core = random.choice([x for x in edge_core[edge]])
            self.edge_out_ports[edge] = (core, edge_core[edge][core])

    def lb_action(self, edge):
        return self.edge_out_ports[edge]


    def generate_load_balancing_matches(self, config):

        datapaths = config.datapaths
        cores = [datapaths[x] for x in datapaths if x.find("core") == 0]

        metadata = []
        for core in cores:
            metadata.append(core.id)

        # test matches, to be extended
        match0 = parser.OFPMatch(eth_type=0x0800, ipv4_src=('1.0.0.0', '192.0.0.0'))
        match1 = parser.OFPMatch(eth_type=0x0800, ipv4_src=('64.0.0.0', '192.0.0.0'))
        match2 = parser.OFPMatch(eth_type=0x0800, ipv4_src=('128.0.0.0', '192.0.0.0'))
        match3 = parser.OFPMatch(eth_type=0x0800, ipv4_src=('192.0.0.0', '192.0.0.0'))
        matches = [match0, match1, match2, match3]

        return matches, metadata
