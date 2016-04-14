#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.node import RemoteController, OVSSwitch
from sdnip import BgpRouter, SdnipHost

ROUTE_SERVER_IP = '172.0.255.254'
ROUTE_SERVER_ASN = 65000


class SDXTopo( Topo ):
    def __init__( self, *args, **kwargs ):
        Topo.__init__( self, *args, **kwargs )
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



        # Add node for central Route Server"
        route_server = self.addHost('rs1', ip = '172.0.255.254/24', mac='08:00:27:89:3b:ff', inNamespace = False)
        self.addLink(switch_3, route_server, 48)

        
        # Add Participants to the IXP (one for each edge switch)

        self.addParticipant(fabric=switch_1,
                            name="a1",
                            port=1,
                            mac="3F:67:15:25:14:3C",
                            ip="172.0.255.132/24",
                            networks=["172.1.0.0/16", "172.2.0.0/16"],
                            asn=100)

        self.addParticipant(fabric=switch_2,
                            name="b1",
                            port=1,
                            mac="55:22:61:94:47:CE",
                            ip="172.0.255.210/24",
                            networks=["172.9.25.0/24", "172.9.96.0/24"],
                            asn=200)

        self.addParticipant(fabric=switch_3,
                            name="c1",
                            port=1,
                            mac="58:14:5D:ED:55:81",
                            ip="172.0.255.39/24",
                            networks=["172.3.0.0/16", "172.4.0.0/16"],
                            asn=300)

    def addParticipant(self,fabric,name,port,mac,ip,networks,asn):
        intfs = {}

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
    topo = SDXTopo()

    net = Mininet(topo=topo, controller=RemoteController, switch=OVSSwitch)

    net.start()

    CLI(net)

    net.stop()
