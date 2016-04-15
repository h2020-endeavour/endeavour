from oslo.config import cfg
import json
import sys

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import dpid as dpid_lib
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet


class Umbrella(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(Umbrella, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        # Maps of ports.
        self.core_to_edge = {}
        self.edge_to_peers = {}
        self.parse_fabric_config()

    def parse_fabric_config(self):
        conf = cfg.CONF
        conf.register_opts([
            cfg.StrOpt('fabric_file', default='None')])
        conf(sys.argv[2:])
        with open(conf.fabric_file, 'r') as file:
            fabric = json.load(file)
            links = fabric["fabric_links"]
            # Set core to edge links.
            for link in links:
                self.core_to_edge[int(link)] = {}
                edges = links[link]
                for edge in edges:
                    port = edges[edge]
                    self.core_to_edge[int(link)][int(edge)] = int(port)
            # Set edge to peers links.
            edges = fabric["edge_switches"]
            for edge in edges:
                self.edge_to_peers.setdefault(int(edge), {})
            participants = fabric["participants"]
            for peer in participants:
                edge = participants[peer]["datapath"]
                mac = participants[peer]["mac"]
                ip = participants[peer]["ip"]
                port = participants[peer]["port"]
                # Convert to string because mac and ip are unicodes.
                host = (str(mac), str(ip))
                self.edge_to_peers[edge][host] = port

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        self.send_group_mod(datapath, 1, [4, 3, 2, 1])
        self.send_group_mod(datapath, 2, [3, 4, 1, 2])
        self.send_group_mod(datapath, 3, [2, 1, 4, 3])
        self.send_group_mod(datapath, 4, [1, 2, 3, 4])
        # Install Umbrella edge flows.
        if datapath.id in self.edge_to_peers:
            self.add_ingress_flows(datapath)
            self.add_egress_flows(datapath)
        else:
            self.add_core_flows(datapath)

    # Installs flows for packets coming into the IXP fabric through an edge 
    # switch. For now, we consider all participants peer between each other. 
    def add_ingress_flows(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id
        # Install flows for switches in the same edge. MAC rewriting is not 
        # required, since there is no need for the segment routing MAC.
        for host in self.edge_to_peers[dpid]:
            ip = host[1]
            out_port = self.edge_to_peers[dpid][host]
            # Flow to handle ARP request.
            match = parser.OFPMatch(eth_type=0x806, arp_op=1, arp_tpa=ip)
            actions = [parser.OFPActionOutput(out_port)]
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                                 actions)]
            self.add_flow(datapath, 1000, inst, match, 0)
            # Flow to handle data.
            dst = host[0]
            match = parser.OFPMatch(eth_dst=dst)
            self.add_flow(datapath, 1000, inst, match, 0)

        # Install flows for peers in different edge switches.
        for target_dp, hosts in self.edge_to_peers.iteritems():
            if target_dp == dpid:
                continue
            else:
                for host in hosts:
                    ip = host[1]
                    # Very simple load balancing among cores
                    # Fast fail-over by groups
                    cores_num = len(self.core_to_edge)
                    out_group = ((target_dp % cores_num) + 1)
                    dp_out_port = out_group * 16
                    core_port = self.core_to_edge[dp_out_port][target_dp]
                    # Format to umbrella fabric mac address.
                    # First byte: core switch connected to the destination's
                    # edge switch.
                    # Second byte: one of the edges ports connected to the
                    # destination peer. 
                    mac_1st_byte = '{}'.format('0' + format(core_port, 'x') if len(hex(core_port)) == 3 else format(core_port, 'x'))
                    edge_port = self.edge_to_peers[target_dp][host]
                    mac_2nd_byte = '{}'.format('0' + format(edge_port, 'x') if len(hex(edge_port)) == 3 else format(edge_port, 'x'))
                    dst = '%s:%s:00:00:00:00' % (mac_1st_byte, mac_2nd_byte)
                    # Flow to handle ARP request
                    match = parser.OFPMatch(
                        eth_type=0x806, arp_op=1, arp_tpa=ip)
                    actions = [parser.OFPActionSetField(
                        eth_dst=dst), parser.OFPActionGroup(out_group)]
                    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
                    self.add_flow(datapath, 1000, inst, match, 0)
                    # Flow to handle data
                    dst = host[0]
                    match = parser.OFPMatch(eth_dst=dst)
                    self.add_flow(datapath, 1000, inst, match, 0)

    # Installs flow in the edge that turns an umbrella segment routing MAC 
    # into its original form and forwards the packet for the respective host.
    def add_egress_flows(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id
        for host in self.edge_to_peers[dpid]:
            # Flow match destination MAC is based on the edge port connected
            # to the peering router.
            edge_port = self.edge_to_peers[dpid][host]
            mac_2nd_byte = '{}'.format('0' + format(edge_port, 'x') if len(hex(edge_port)) == 3 else format(edge_port, 'x'))
            sh_mac = '00:%s:00:00:00:00' % (mac_2nd_byte)
            match = parser.OFPMatch(eth_dst=(sh_mac, '00:ff:00:00:00:00'))
            dst = host[0]
            actions = [parser.OFPActionSetField(
                eth_dst=dst), parser.OFPActionOutput(edge_port)]
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                                 actions)]
            self.add_flow(datapath, 1500, inst, match, 0)

    # Installs flows for the IXP core switches. 
    def add_core_flows(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id
        for edge in self.core_to_edge[dpid]:
            # Flow match is based on the core port connected to the
            # edge switch
            out_port = self.core_to_edge[dpid][edge]
            mac_1byte = '{}'.format('0' + format(out_port, 'x') if len(hex(out_port)) == 3 else format(out_port, 'x'))
            dst = '%s:00:00:00:00:00' % (mac_1byte)
            match = parser.OFPMatch(eth_dst=(dst, 'ff:00:00:00:00:00'))
            actions = [parser.OFPActionOutput(out_port)]
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                                 actions)]
            self.add_flow(datapath, 1000, inst, match, 0)

    def send_group_mod(self, datapath, gid, switch_ports):
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        weight = 0
        max_len = 2000
        watch_group = 0
        buckets = []
        for port in switch_ports:
            watch_port = port
            action = [ofp_parser.OFPActionOutput(port, max_len)]
            buckets.append(ofp_parser.OFPBucket(weight, watch_port,
                                                watch_group, action))
        group_id = gid
        req = ofp_parser.OFPGroupMod(datapath, ofp.OFPGC_ADD,
                                     ofp.OFPGT_FF, group_id, buckets)
        datapath.send_msg(req)

    def add_flow(self, datapath, priority, inst,  match, table):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                table_id=table,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    def delete_flow(self, datapath, table):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        for dst in self.mac_to_port[datapath.id].keys():
            match = parser.OFPMatch(eth_dst=dst)
            mod = parser.OFPFlowMod(
                datapath, command=ofproto.OFPFC_DELETE,
                out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
                table_id=table, priority=1, match=match)
            datapath.send_msg(mod)
