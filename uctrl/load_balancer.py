#!/usr/bin/env python
import random

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

    def ip_match(self, core_id, METADATA_MASK, ETH_TYPE_IP):
        metadata = [core_id, METADATA_MASK]
        if core_id == 16:
            ipv4_src=('1.0.0.0', '192.0.0.0')
        elif core_id == 32:
            ipv4_src=('64.0.0.0', '192.0.0.0')
        elif core_id == 48:
            ipv4_src=('128.0.0.0', '192.0.0.0')
        elif core_id == 64:
            ipv4_src=('192.0.0.0', '192.0.0.0')
        else:
            ipv4_src=('1.0.0.0', '0.0.0.0')
        match = {"eth_type": ETH_TYPE_IP, "ipv4_src": ipv4_src}
        return match, metadata

    def get_flow_mod():
        return flow_mods

    # Just send load balancer flows to umbrella. 
    def start(self, config, rule_type, LB_PRIORITY, METADATA_MASK, ETH_TYPE_IP):
        flow_mods = []
        # Rule for every Edge
        for edge in config.edge_core:
            # Rule to every Core
            for core in config.cores:
            
                # Decision for Match is core_id
                core_id = config.cores[core]
                match, metadata = self.ip_match(core_id, METADATA_MASK, ETH_TYPE_IP)

                # Build Instruction Meta-Information and Goto-Table
                instructions = {"meta": metadata, "goto": 'umbrella-edge'}

                # Send for every Core to every Edge
                flow_mods.append(["insert", rule_type, LB_PRIORITY, match, instructions, config.dpid_2_name[edge]]) 


    def lb_policy(self, edge_core):
        for edge in edge_core:
            self.edge_out_ports.setdefault(edge, {})
            core = random.choice([x for x in edge_core[edge]])
            self.edge_out_ports[edge] = (core, edge_core[edge][core])

    def lb_action(self, edge):
        return self.edge_out_ports[edge]

