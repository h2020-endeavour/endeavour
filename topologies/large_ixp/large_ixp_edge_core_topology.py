from mininet.net import Mininet
from mininet.topo import Topo
from mininet.util import quietRun
from mininet.node import OVSSwitch, Controller, RemoteController
from mininet.cli import CLI

# Topology to mimic the Edge-Core topology of a large IXP.
# four edge switches
# four core switches
# each edge switch is connected to all four core switches.

net = Mininet()
h1 = net.addHost('h1')
h2 = net.addHost('h2')
h3 = net.addHost('h3')
h4 = net.addHost('h4')
h5 = net.addHost('h5')
h6 = net.addHost('h6')
h7 = net.addHost('h7')
h8 = net.addHost('h8')

# edge switches
edge_switches = []
for i in range(1, 5):
    print 'Edge Switch ID: %s' % i
    edge_switches.append(net.addSwitch(
        'e%s' % i, dpid='000000000000000%s' % i))

# core switches
core_switches = []
for i in range(1, 5):
    print 'Core Switch ID: %s' % i
    core_switches.append(net.addSwitch(
        'c%s' % i, dpid='00000000000000%s0' % i))

c0 = net.addController('c0', controller=RemoteController,
                       ip='127.0.0.1', port=6633)

# connect host links
index = 0
for host in net.hosts:
    net.addLink(host, net.switches[index])
    index = index + 1


# connect edge to core links
for edge_switch in edge_switches:
    for core_switch in core_switches:
        net.addLink(edge_switch, core_switch)


# set easy mac addresses for hosts
for host in net.hosts:
    id = host.name[-1:]
    host.setIP('10.0.0.%s' % id, '18')
    host.setMAC('00:00:00:00:00:0%s' % id)

net.start()

# start CLI mode
CLI(net)

net.stop()
