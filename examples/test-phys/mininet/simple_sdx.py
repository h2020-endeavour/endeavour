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
from mininet.log import setLogLevel, info
from mininet.node import RemoteController, OVSSwitch, Node
from sdnip import BgpRouter, SdnipHost
from lib import Config

path_mininet_config = '/home/vagrant/endeavour/examples/test-phys/mininet/mininet.cfg'
default_isdx_config = '/home/vagrant/endeavour/examples/test-phys/config/sdx_global.cfg'

def addParticipant(mn, fabric, name, port, mac, ip, networks, asn, config):
        # Adds the interface to connect the router to the Route server
        peereth0 = [{'mac': mac, 'ipAddrs': [ip]}]
        intfs = {name + '-eth0': peereth0}

        # Adds 1 gateway interface for each network connected to the router
        for net in networks:
            eth = {'ipAddrs': [replace_ip(net, '254')]}  # ex.: 100.0.0.254
            i = len(intfs)
            intfs[name + '-eth' + str(i)] = eth

        # Set up the peer router
        neighbors = [{'address': config.route_server.ip, 'as': config.route_server.asn}]
        peer = mn.addHost(name,
                            intfDict=intfs,
                            asNum=asn,
                            neighbors=neighbors,
                            routes=networks,
                            cls=BgpRouter)
        mn.addLink(fabric, peer, port)

        # Adds a host connected to the router via the gateway interface
        i = 0
        for net in networks:
            i += 1
            ips = [replace_ip(net, '1')]  # ex.: 100.0.0.1/24
            hostname = 'h' + str(i) + '_' + name  # ex.: h1_a1
            host = mn.addHost(hostname,
                                cls=SdnipHost,
                                ips=ips,
                                gateway=replace_ip(net, '254').split('/')[0])  # ex.: 100.0.0.254
            # Set up data plane connectivity
            mn.addLink(peer, host)      

def create_topo(net, config):
        participant_config = json.load(open(path_mininet_config, 'r'))
        edge = net.addSwitch('edges', dpid=format(1, '016x'))

        # core switches
        core_switches = []
        for i in range(1, len(filter(lambda s: 'core' in str(s), config.dpids))+1):
            core_switches.append(net.addSwitch(
                'core-%s' % i, dpid=format(config.dpids['core-%s' % i], '016x')))

        #connect edge to core links
        for core_switch in core_switches:
            for j in range (0, 4):
                net.addLink(edge, core_switch)
                

        # connect route server to edge 0 port 7
        route_server = net.addHost('x1', ip=config.route_server.ip, mac=config.route_server.mac, inNamespace=False)
        net.addLink(edge, route_server, 17)


        # # Add node for ARP Proxy"
        arp_proxy = net.addHost('x2', ip=config.arp_proxy.ip, mac=config.arp_proxy.mac, inNamespace=False)
        net.addLink(edge, arp_proxy, 18)

        # Add Participants to the IXP
        # Connects one participant to one of the four edge switches
        # Each participant consists of 1 quagga router PLUS
        # 1 host per network advertised behind quagga
 
        name = 'a1'
        addParticipant(mn=net,fabric=edge,
                             name=name,
                            port=participant_config[name]['port'],
                            mac=participant_config[name]['mac'],
                            ip=participant_config[name]['ip'],
                            networks=participant_config[name]['networks'],
                            asn=participant_config[name]['asn'], 
                            config=config)

        name = 'b1'
        addParticipant(mn=net,fabric=edge,
                             name=name,
                            port=participant_config[name]['port'],
                            mac=participant_config[name]['mac'],
                            ip=participant_config[name]['ip'],
                            networks=participant_config[name]['networks'],
                            asn=participant_config[name]['asn'], 
                            config=config)

        name = 'c1'
        addParticipant(mn=net,fabric=edge,
                             name=name,
                            port=participant_config[name]['port'],
                            mac=participant_config[name]['mac'],
                            ip=participant_config[name]['ip'],
                            networks=participant_config[name]['networks'],
                            asn=participant_config[name]['asn'],
                            config=config)

        name = 'c2'
        addParticipant(mn=net, fabric=edge,
                             name=name,
                            port=participant_config[name]['port'],
                            mac=participant_config[name]['mac'],
                            ip=participant_config[name]['ip'],
                            networks=participant_config[name]['networks'],
                            asn=participant_config[name]['asn'],
                            config=config)


def replace_ip(network, ip):
    net, subnet = network.split('/')
    gw = net.split('.')
    gw[3] = ip
    gw = '.'.join(gw)
    gw = '/'.join([gw, subnet])
    return gw

if __name__ == "__main__":
    setLogLevel('info')

    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='path of config file', nargs='?', default= default_isdx_config)
    args = parser.parse_args()

    # locate config file
    config_file = os.path.abspath(args.config)

    config = Config(config_file)

    net = Mininet(switch=OVSSwitch)
    net.addController( 'c0', controller=RemoteController, ip='127.0.0.1', port= 6633)
    create_topo(net, config)
    net.start()

    CLI(net)

    net.stop()

    info("done\n")
