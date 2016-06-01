#!/usr/bin/python

import argparse
import os
import sys
import json

sys.path.append('/home/vagrant/endeavour/uctrl')
from lib import Config

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.node import RemoteController, OVSSwitch
from sdnip import BgpRouter, SdnipHost

path_mininet_config = '/home/vagrant/endeavour/examples/test-de/mininet/mininet.cfg'



class SDXTopo( Topo ):
    def __init__( self, config, *args, **kwargs ):
        Topo.__init__( self, *args, **kwargs )
        self.config = config
        # Describe Code
        # Set up data plane switch - this is the emulated router dataplane
        # Note: The controller needs to be configured with the specific driver that
        # will be attached to this switch.

        # IXP fabric
        switch_1 = self.addSwitch('e1')
        switch_2 = self.addSwitch('e2')
        switch_3 = self.addSwitch('e3')

        # Add links for loop topology
        # e1 <-> e2
        self.addLink(switch_1, switch_2, 51, 49)
        # e3 <-> e2
        self.addLink(switch_3, switch_2, 51, 50)
        # e3 <-> e1
        self.addLink(switch_3, switch_1, 50, 50)


        participant_config = json.load(open(path_mininet_config, 'r'))

        # Add node for central Route Server"
        route_server = self.addHost('rs1', ip=self.config.route_server.ip, mac=self.config.route_server.mac, inNamespace = False)
        self.addLink(switch_3, route_server, 48, 1)

        
        # Add Participants to the IXP (one for each edge switch)
        name = 'a1'
        self.addParticipant(fabric=switch_1,
                            name=name,
                            port=participant_config[name]['port'],
                            mac=participant_config[name]['mac'],
                            ip=participant_config[name]['ip'],
                            networks=participant_config[name]['networks'],
                            asn=participant_config[name]['asn'])

        name = 'b1'
        self.addParticipant(fabric=switch_2,
                            name=name,
                            port=participant_config[name]['port'],
                            mac=participant_config[name]['mac'],
                            ip=participant_config[name]['ip'],
                            networks=participant_config[name]['networks'],
                            asn=participant_config[name]['asn'])

        name = 'c1'
        self.addParticipant(fabric=switch_1,
                            name=name,
                            port=participant_config[name]['port'],
                            mac=participant_config[name]['mac'],
                            ip=participant_config[name]['ip'],
                            networks=participant_config[name]['networks'],
                            asn=participant_config[name]['asn'])


    def addParticipant(self,fabric,name,port,mac,ip,networks,asn):
        # Adds the interface to connect the router to the Route server
        peereth0 = [{'mac': mac, 'ipAddrs': [ip]}]
        intfs = {name + '-eth0': peereth0}

        # Adds 1 gateway interface for each network connected to the router
        for net in networks:
            eth = {'ipAddrs': [replace_ip(net, '254')]}  # ex.: 100.0.0.254
            i = len(intfs)
            intfs[name + '-eth' + str(i)] = eth
            
        # Set up the peer router
        neighbors = [{'address': self.config.route_server.ip, 'as': self.config.route_server.asn}]
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