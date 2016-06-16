#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import RemoteController, OVSSwitch, Node
from sdnip import BgpRouter, SdnipHost
import sys, json, yaml

sys.path.append('/home/vagrant/endeavour/uctrl')
from lib import Config


ROUTE_SERVER_IP = '172.0.255.254'
ROUTE_SERVER_ASN = 65000


class SDXTopo(Topo):
    def __init__(self, *args, **kwargs):
        Topo.__init__(self, *args, **kwargs)
        config = args[0][0]
        config_global = Config(args[0][1])
        # Describe Code
        # Set up data plane switch - this is the emulated router dataplane
        # Note: The controller needs to be configured with the specific driver that
        # will be attached to this switch.

        # IXP fabric
        # edge switches
        edge_switches = []

        for i in range(1, len(filter(lambda s: 'edge' in str(s), config_global.dpids)) + 1):
            edge_switches.append(self.addSwitch(
                'edge-%s' % i, dpid=format(config_global.dpids['edge-%s' % i], '016x')))

        # core switches
        core_switches = []
        for i in range(1, len(filter(lambda s: 'core' in str(s), config_global.dpids)) + 1):
            core_switches.append(self.addSwitch(
                'core-%s' % i, dpid=format(config_global.dpids['core-%s' % i], '016x')))

        # connect edge to core links
        for edge_switch in edge_switches:
            for core_switch in core_switches:
                self.addLink(edge_switch, core_switch)

        # connect arp switch to edge 0 port 6
        # arp_switch = self.addSwitch('s2', dpid=format(config_global.dpids['arp-switch'], '016x'))
        # self.addLink(edge_switches[0], arp_switch, 6, 1)

        # connect route server to edge 0 port 7
        route_server = self.addHost('x1', ip=config_global.route_server.ip, mac=config_global.route_server.mac,
                                    inNamespace=False)
        self.addLink(edge_switches[0], route_server, 6)

        # Add node for ARP Proxy"
        arp_proxy = self.addHost('x2', ip=config_global.arp_proxy.ip, mac=config_global.arp_proxy.mac, inNamespace=False)
        self.addLink(edge_switches[0], arp_proxy, 7)

        # Add Participants to the IXP
        # Connects one participant to one of the four edge switches
        # Each participant consists of 1 quagga router PLUS
        # 1 host per network advertised behind quagga

        name = 'a1'
        self.addParticipant(fabric=edge_switches[0],
                            name=name,
                            port=config[name]['port'],
                            mac=config[name]['mac'],
                            ip=config[name]['ip'],
                            networks=config[name]['networks'],
                            asn=config[name]['asn'],
                            announcements=config[name]['networks'],
                            netnames=config[name]['netnames'])

        name = 'b1'
        self.addParticipant(fabric=edge_switches[1],
                            name=name,
                            port=config[name]['port'],
                            mac=config[name]['mac'],
                            ip=config[name]['ip'],
                            networks=config[name]['networks'],
                            asn=config[name]['asn'],
                            announcements=config[name]['networks'],
                            netnames=config[name]['netnames'])

        name = 'c1'
        self.addParticipant(fabric=edge_switches[2],
                            name=name,
                            port=config[name]['port'],
                            mac=config[name]['mac'],
                            ip=config[name]['ip'],
                            networks=config[name]['networks'],
                            asn=config[name]['asn'],
                            announcements=config[name]['networks'],
                            netnames=config[name]['netnames'])

        name = 'c2'
        self.addParticipant(fabric=edge_switches[3],
                            name=name,
                            port=config[name]['port'],
                            mac=config[name]['mac'],
                            ip=config[name]['ip'],
                            networks=config[name]['networks'],
                            asn=config[name]['asn'],
                            announcements=config[name]['networks'],
                            netnames=config[name]['netnames'])


    def addParticipant(self, fabric, name, port, mac, ip, networks, asn, netnames, announcements):
        print 'name=' + name + ' ip=' + ip + ' networks=' + str(networks)
        # Adds the interface to connect the router to the Route server
        peereth0 = [{'mac': mac, 'ipAddrs': [ip]}]
        intfs = {name + '-eth0': peereth0}

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
                            routes=announcements,
                            cls=BgpRouter)
        self.addLink(fabric, peer, port)

        # Adds a host connected to the router via the gateway interface
        i = 0
        for net in networks:
            i += 1
            ips = [replace_ip(net, '1')]  # ex.: 100.0.0.1/24
            hostname = 'h' + str(i) + '_' + name  # ex.: h1_a1
            hostname = netnames[i - 1]
            host = self.addHost(hostname,
                                cls=SdnipHost,
                                ips=ips,
                                gateway=replace_ip(net, '254').split('/')[0])  # ex.: 100.0.0.254
            # Set up data plane connectivity
            self.addLink(peer, host)


def replace_ip(network, ip):
    net, subnet = network.split('/')
    gw = net.split('.')
    gw[3] = ip
    gw = '.'.join(gw)
    gw = '/'.join([gw, subnet])
    return gw


if __name__ == "__main__":
    setLogLevel('info')

    argc = len(sys.argv)
    if argc < 3 or argc > 5:
        raise Exception('usage: sdx_mininet config.json sdx_global.cfg [ path_to_tnode.py [ [ semaphore_name ]')
    config_file = sys.argv[1]

    configfd = open(config_file)
    config = yaml.safe_load(configfd)
    configfd.close()

    config_global = sys.argv[2]

    if argc > 3:
        tnode_file = sys.argv[3]
    else:
        tnode_file = None

    topo = SDXTopo((config, config_global))

    net = Mininet(topo=topo, controller=RemoteController, switch=OVSSwitch)

    net.start()

    # start traffic nodes on all interior hosts - host names are free form, but are found in config
    if tnode_file is not None:
        tnodenames = []
        for h in config:
            tnodenames.append(h)
            for nn in config[h]['netnames']:
                tnodenames.append(nn)

        for host in net.hosts:
            if host.name in tnodenames:
                host.cmd('python ' + tnode_file + ' ' + host.name + '&')

    # if a semaphore was provided, write into it to signal the next process to start
    if argc > 4:
        semaphore_file = sys.argv[4]
        sync = open(semaphore_file, 'w')
        sync.write("MININET READY\n")
        sync.close()

    CLI(net)

    net.stop()

    info("done\n")
