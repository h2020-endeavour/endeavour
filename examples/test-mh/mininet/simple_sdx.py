#!/usr/bin/python
import argparse
import os
import sys

sys.path.append('endeavour/uctrl/')

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import RemoteController, OVSSwitch, Node
from sdnip import BgpRouter, SdnipHost
from lib import Config

ROUTE_SERVER_IP = '172.0.255.254'
ROUTE_SERVER_ASN = 65000


class SDXTopo( Topo ):
    def __init__( self, config, *args, **kwargs ):
        Topo.__init__( self, *args, **kwargs )
        self.config = config
        # Describe Code
        # Set up data plane switch - this is the emulated router dataplane
        # Note: The controller needs to be configured with the specific driver that
        # will be attached to this switch.

        # IXP fabric
        # edge switches
        edge_switches = []
        for i in range(1, 5):
            edge_switches.append(self.addSwitch(
                'edge%s' % i, dpid='000000000000000%s' % i))

        # core switches
        core_switches = []
        for i in range(1, 5):
            core_switches.append(self.addSwitch(
                'core%s' % i, dpid='00000000000000%s0' % i))

        # connect edge to core links
        for edge_switch in edge_switches:
            for core_switch in core_switches:
                self.addLink(edge_switch, core_switch)


        # connect arp switch to edge 0 port 6
        arp_switch = self.addSwitch( 's2' , dpid='1000000000000000')
        self.addLink(edge_switches[0], arp_switch, 6, 1)

        # connect route server to edge 0 port 7
        route_server = self.addHost('x1', ip = self.config.route_server['IP'], mac=self.config.route_server['MAC'], inNamespace = False)
        self.addLink(edge_switches[0], route_server, 7)

        # Add node for ARP Proxy"
        arp_proxy = self.addHost('x2', ip = self.config.arp_proxy['IP'], mac=self.config.arp_proxy['MAC'], inNamespace = False)
        self.addLink(arp_switch, arp_proxy, 2)

        # Add Participants to the IXP
        # Connects one participant to one of the four edge switches
        # Each participant consists of 1 quagga router PLUS
        # 1 host per network advertised behind quagga
        name = 'a1'
        self.addParticipant(fabric=edge_switches[0],
                            name=name,
                            port=self.config.participants[name]['Ports'][0]['Id'],
                            mac=self.config.participants[name]['Ports'][0]['MAC'],
                            ip=self.config.participants[name]['Ports'][0]['IP'],
                            networks=['100.0.0.0/24', '110.0.0.0/24'],
                            asn=self.config.participants[name]['ASN'])

        name = 'b1'
        self.addParticipant(fabric=edge_switches[1],
                            name=name,
                            port=self.config.participants[name]['Ports'][0]['Id'],
                            mac=self.config.participants[name]['Ports'][0]['MAC'],
                            ip=self.config.participants[name]['Ports'][0]['IP'],
                            networks=['140.0.0.0/24', '150.0.0.0/24'],
                            asn=self.config.participants[name]['ASN'])

        name = 'c1'
        self.addParticipant(fabric=edge_switches[2],
                            name=name,
                            port=self.config.participants[name]['Ports'][0]['Id'],
                            mac=self.config.participants[name]['Ports'][0]['MAC'],
                            ip=self.config.participants[name]['Ports'][0]['IP'],
                            networks=['140.0.0.0/24', '150.0.0.0/24'],
                            asn=self.config.participants[name]['ASN'])

        name = 'c2'
        self.addParticipant(fabric=edge_switches[3],
                            name=name,
                            port=self.config.participants[name]['Ports'][0]['Id'],
                            mac=self.config.participants[name]['Ports'][0]['MAC'],
                            ip=self.config.participants[name]['Ports'][0]['IP'],
                            networks=['140.0.0.0/24', '150.0.0.0/24'],
                            asn=self.config.participants[name]['ASN'])




    def addParticipant(self,fabric,name,port,mac,ip,networks,asn):
        # Adds the interface to connect the router to the Route server
        peereth0 = [{'mac': mac, 'ipAddrs': [ip]}]
        intfs = {name+'-eth0': peereth0}

        # Adds 1 gateway interface for each network connected to the router
        for net in networks:
            eth = {'ipAddrs': [replace_ip(net, '254')]}  # ex.: 100.0.0.254
            i = len(intfs)
            intfs[name + '-eth' + str(i)] = eth

        # Set up the peer router
        neighbors = [{'address': ROUTE_SERVER_IP, 'as': ROUTE_SERVER_ASN}]
        peer = self.addHost(name,
                            intfDict=intfs,
                            asNum=asn,
                            neighbors=neighbors,
                            routes=networks,
                            cls=BgpRouter)
        self.addLink(fabric, peer, port)

        # Adds a host connected to the router via the gateway interface
        i = 0
        for net in networks:
            i += 1
            ips = [replace_ip( net, '1' )]  # ex.: 100.0.0.1/24
            hostname = 'h' + str(i) + '_' + name  # ex.: h1_a1
            host = self.addHost(hostname ,
                                cls=SdnipHost,
                                ips=ips,
                                gateway = replace_ip(net, '254').split('/')[0])  #ex.: 100.0.0.254
            # Set up data plane connectivity
            self.addLink( peer, host )

def replace_ip(network, ip):
    net,subnet=network.split('/')
    gw=net.split('.')
    gw[3]=ip
    gw='.'.join(gw)
    gw='/'.join([gw,subnet])
    return gw

if __name__ == "__main__":
    setLogLevel('info')

    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='path of config file')
    args = parser.parse_args()

    # locate config file
    config_file = os.path.abspath(args.config)

    config = Config(config_file)

    topo = SDXTopo(config)

    net = Mininet(topo=topo, controller=RemoteController, switch=OVSSwitch)

    net.start()

    CLI(net)

    net.stop()

    info("done\n")
