#!/usr/bin/env python

import os
import sys

isdx_folder = "iSDX"
home = os.path.expanduser("~/")
isdx_path = home + isdx_folder
if isdx_path not in sys.path:
    sys.path.append(isdx_path)
import util.log

from xctrl.flowmodmsg import FlowModMsgBuilder

DEFAULT_PRIORITY = 1
FORWARDING_PRIORITY = 4
ARP_PRIORITY = 8
LB_PRIORITY = 10
METADATA_MASK = 0xffffffff
ETH_TYPE_ARP = 0x0806
ETH_TYPE_IP = 0x0800
ETH_BROADCAST_MAC = "ff:ff:ff:ff:ff:ff"


class Umbrella(object):
    def __init__(self, config, sender, logger, lbal):
        # Maps of ports.
        self.logger = logger
        self.sender = sender
        self.config = config
        self.lbal = lbal
        self.fm_builder = FlowModMsgBuilder(0, self.config.flanc_auth["key"])
        lbal.lb_policy(self.config.edge_core)
    # Format to umbrella fabric mac address.
    # core_port: core switch port connected to the edge
    # edge_port: edge port connected to a participant
    def create_umbrella_mac(self, core_port, edge_port):
        # First byte: core switch port connected to the 
        # destination's edge switch.
        mac_1st_byte = '{}'.format('0' + format(core_port, 'x') if len(hex(core_port)) == 3 else format(core_port, 'x'))
        # Second byte: one of the edges ports connected to the
        # destination peer.
        mac_2nd_byte = '{}'.format('0' + format(edge_port, 'x') if len(hex(edge_port)) == 3 else format(edge_port, 'x'))
        mac = '%s:%s:00:00:00:00' % (mac_1st_byte, mac_2nd_byte)
        return mac

    def ARP_match(self, arp_tpa):
         match = {"eth_type": ETH_TYPE_ARP, "eth_dst": ETH_BROADCAST_MAC, "arp_tpa":arp_tpa}
         return match

    def l2_match(self, eth_dst):
        match = {"eth_dst":eth_dst}
        return match

    #TODO: Add identification cookie of the flows
    def handle_ARP(self, rule_type):
        # peers are in the same edge
        for dp in self.config.edge_peers:
            peers = self.config.edge_peers[dp]
            for peer in peers:
                out_port = peers[peer]
                match = self.ARP_match(peer.ip)
                action = {"fwd": [out_port]}
                self.fm_builder.add_flow_mod("insert", rule_type, ARP_PRIORITY, match, action, self.config.dpid_2_name[dp])

        #TODO: peers are in different edges. Edges connected directly.
        # Or create a different class to handle topologies like this 

        # peers are in different edges. Edges are connected through cores.
        for edge in self.config.edge_peers:
            for target_dp, hosts in self.config.edge_peers.iteritems():
                if target_dp == edge:
                    continue
                else:
                    for host in hosts:
                        core, out_port_to_core = self.lbal.lb_action(edge) 
                        core_port_to_target = self.config.core_edge[core][target_dp]
                        edge_port = self.config.edge_peers[target_dp][host]
                        match = self.ARP_match(host.ip)
                        actions = {"set_eth_dst": self.create_umbrella_mac(core_port_to_target, edge_port), "fwd": [out_port_to_core]}
                        self.fm_builder.add_flow_mod("insert", rule_type, ARP_PRIORITY, match, actions, self.config.dpid_2_name[edge]) 

    def handle_ingress_l2(self, rule_type):
        # peers are in the same edge
        for dp in self.config.edge_peers:
            peers = self.config.edge_peers[dp]
            for peer in peers:
                out_port = peers[peer]
                match = self.l2_match(peer.mac)
                action = {"fwd": [out_port]}
                self.fm_builder.add_flow_mod("insert", rule_type, FORWARDING_PRIORITY, match, action, self.config.dpid_2_name[dp])
        
        for edge in self.config.edge_peers:
            for target_dp, hosts in self.config.edge_peers.iteritems():
                if target_dp == edge:
                    continue
                else:
                    for host in hosts:
                        core, out_port_to_core = self.lbal.lb_action(edge) 
                        core_port_to_target = self.config.core_edge[core][target_dp]
                        edge_port = self.config.edge_peers[target_dp][host]
                        match = self.l2_match(host.mac)
                        actions = {"set_eth_dst": self.create_umbrella_mac(core_port_to_target, edge_port), "fwd": [out_port_to_core]}
                        self.fm_builder.add_flow_mod("insert", rule_type, FORWARDING_PRIORITY, match, actions, self.config.dpid_2_name[edge]) 

    def create_egress_match(self, edge_port):
        mac_2nd_byte = '{}'.format('0' + format(edge_port, 'x') if len(hex(edge_port)) == 3 else format(edge_port, 'x'))
        eth_dst = ('00:%s:00:00:00:00' % (mac_2nd_byte), "00:ff:00:00:00:00")
        match = {"eth_dst":eth_dst}
        return match

    def handle_egress(self, rule_type):
        for dp in self.config.edge_peers:
            peers = self.config.edge_peers[dp]
            for peer in peers:
                # Flow match destination MAC is 
                #based on the edge port connected
                edge_port = self.config.edge_peers[dp][peer]
                match = self.create_egress_match(edge_port)
                peer_mac = peer.mac
                action = {"set_eth_dst": peer_mac, "fwd": [edge_port]}
                self.fm_builder.add_flow_mod("insert", rule_type, FORWARDING_PRIORITY, match, action, self.config.dpid_2_name[dp]) 

    def create_core_match(self, out_port):
        mac_1st_byte = '{}'.format('0' + format(out_port, 'x') if len(hex(out_port)) == 3 else format(out_port, 'x'))
        eth_dst = ('%s:00:00:00:00:00' % (mac_1st_byte), "ff:00:00:00:00:00")
        match = {"eth_dst": eth_dst}
        return match

    def handle_core_switches(self, rule_type):
        for core in self.config.core_edge:
            for edge in self.config.core_edge[core]:
                # Flow match is based on the core port connected to the
                # edge switch
                out_port = self.config.core_edge[core][edge]
                match = self.create_core_match(out_port)
                action = {"fwd": [out_port]}

                self.fm_builder.add_flow_mod("insert", rule_type, FORWARDING_PRIORITY, match, action, self.config.dpid_2_name[core] )

    # Just send load balancer flows to umbrella. 
    def handle_load_balancer(self, rule_type):

        match_bytes = [0, 0, 0, "11000000"]
        self.lbal.init(self.config.cores, match_bytes)

        # Rule for every Edge
        for edge in self.config.edge_core:
            # Rule to every Core
            for core in self.config.cores:
            
                # Decision for Match is core_id
                core_id = self.config.cores[core]
                match, metadata = self.lbal.get_ip_match(core_id, "ipv4_dst")

                # Build Instruction Meta-Information and Goto-Table
                instructions = {"meta": metadata, "goto": ["umbrella-edge"]}

                print("match: %s" % match)
 
                # Send for every Core to every Edge
                self.fm_builder.add_flow_mod("insert", rule_type, LB_PRIORITY, match, instructions, self.config.dpid_2_name[edge]) 


    def start(self):
        self.logger.info('start')
        self.handle_ARP("umbrella-edge")
        self.handle_ingress_l2("umbrella-edge")
        self.handle_core_switches("umbrella-core")
        self.handle_egress("umbrella-edge")
        self.handle_load_balancer("load-balancer")
        #self.lbalancer_flow("load-balancer")
        self.sender.send(self.fm_builder.get_msg())
        self.logger.info('sent flow mods to reference monitor')
