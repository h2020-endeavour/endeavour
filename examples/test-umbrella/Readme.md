# Test Setup - MultiHop for Umbrella flows (large IXP setup)

The test topology is a mesh network, with 4 edge switches connected to 4 core 
switches, as illustrated below:

![Test Topology](https://github.com/h2020-endeavour/endeavour/blob/master/examples/test-umbrella/large_ixp_edge_core_topology_visual.png)

In this test there are 4 peering routers, running Quagga, named 
**a1**, **b1**, **c1** and **c2**. These peers are configured to peer 
with the fabric central route server named **x1**.

Each router is a gateway for another 2 hosts:

    a1 <- h1_a1, h2_a1
    b1 <- h1_b1, h2_b1
    c1 <- h1_c1, h2_c1
    c2 <- h1_c2, h2_c2

This setup considers that all participants peer between each other, so that, 
after the initial flow setup, every host connected to a peer should be able to
exchange packets.

## Running the test

Start the topology on Mininet.

```bash
$ cd endeavour && python examples/test-umbrella/mininet/simple_sdx.py
```
    
In another terminal session.
```bash
$ cd endeavour && ryu-manager umbrella/umbrella.py --config-file umbrella/fabric.cfg
```

Flows and groups installed can be checked with ovs-ofctl. E.g:

**Groups installed in the switch edge1 **
```
$ sudo ovs-ofctl -O OpenFlow13 dump-groups edge1
OFPST_GROUP_DESC reply (OF1.3) (xid=0x2):
group_id=4,type=ff,bucket=weight:0,watch_port:1,watch_group:0,actions=output:1,bucket=weight:0,watch_port:2,watch_group:0,actions=output:2,bucket=weight:0,watch_port:3,watch_group:0,actions=output:3,bucket=weight:0,watch_port:4,watch_group:0,actions=output:4
group_id=1,type=ff,bucket=weight:0,watch_port:4,watch_group:0,actions=output:4,bucket=weight:0,watch_port:3,watch_group:0,actions=output:3,bucket=weight:0,watch_port:2,watch_group:0,actions=output:2,bucket=weight:0,watch_port:1,watch_group:0,actions=output:1
group_id=2,type=ff,bucket=weight:0,watch_port:3,watch_group:0,actions=output:3,bucket=weight:0,watch_port:4,watch_group:0,actions=output:4,bucket=weight:0,watch_port:1,watch_group:0,actions=output:1,bucket=weight:0,watch_port:2,watch_group:0,actions=output:2
group_id=3,type=ff,bucket=weight:0,watch_port:2,watch_group:0,actions=output:2,bucket=weight:0,watch_port:1,watch_group:0,actions=output:1,bucket=weight:0,watch_port:4,watch_group:0,actions=output:4,bucket=weight:0,watch_port:3,watch_group:0,actions=output:3
```

**Flows installed in the switch edge1**

```
$ sudo ovs-ofctl -O OpenFlow13 dump-flows edge1
 OFPST_FLOW reply (OF1.3) (xid=0x2):
 cookie=0x0, duration=106.971s, table=0, n_packets=214, n_bytes=16498, priority=1500,dl_dst=00:06:00:00:00:00/00:ff:00:00:00:00 actions=set_field:08:00:27:89:3b:ff->eth_dst,output:6
 cookie=0x0, duration=106.971s, table=0, n_packets=0, n_bytes=0, priority=1500,dl_dst=00:05:00:00:00:00/00:ff:00:00:00:00 actions=set_field:08:00:27:89:3b:9f->eth_dst,output:5
 cookie=0x0, duration=106.972s, table=0, n_packets=73, n_bytes=5705, priority=1000,dl_dst=08:00:27:92:18:1f actions=set_field:02:05:00:00:00:00->eth_dst,group:3
 cookie=0x0, duration=106.973s, table=0, n_packets=54, n_bytes=4429, priority=1000,dl_dst=08:00:27:89:3b:ff actions=output:6
 cookie=0x0, duration=106.971s, table=0, n_packets=76, n_bytes=5940, priority=1000,dl_dst=08:00:27:54:56:ea actions=set_field:03:05:00:00:00:00->eth_dst,group:4
 cookie=0x0, duration=106.971s, table=0, n_packets=77, n_bytes=6006, priority=1000,dl_dst=08:00:27:bd:f8:b2 actions=set_field:04:05:00:00:00:00->eth_dst,group:1
 cookie=0x0, duration=106.974s, table=0, n_packets=80, n_bytes=6186, priority=1000,dl_dst=08:00:27:89:3b:9f actions=output:5
 cookie=0x0, duration=106.973s, table=0, n_packets=0, n_bytes=0, priority=1000,arp,arp_tpa=172.0.0.11,arp_op=1 actions=set_field:02:05:00:00:00:00->eth_dst,group:3
 cookie=0x0, duration=106.971s, table=0, n_packets=1, n_bytes=42, priority=1000,arp,arp_tpa=172.0.0.21,arp_op=1 actions=set_field:03:05:00:00:00:00->eth_dst,group:4
 cookie=0x0, duration=106.971s, table=0, n_packets=1, n_bytes=42, priority=1000,arp,arp_tpa=172.0.0.22,arp_op=1 actions=set_field:04:05:00:00:00:00->eth_dst,group:1
 cookie=0x0, duration=106.973s, table=0, n_packets=1, n_bytes=42, priority=1000,arp,arp_tpa=172.0.255.254,arp_op=1 actions=output:6
 cookie=0x0, duration=106.975s, table=0, n_packets=0, n_bytes=0, priority=1000,arp,arp_tpa=172.0.0.1,arp_op=1 actions=output:5
```

**Flows installed in the switch core1**
```
sudo ovs-ofctl -O OpenFlow13 dump-flows core1
 OFPST_FLOW reply (OF1.3) (xid=0x2):
 cookie=0x0, duration=730.778s, table=0, n_packets=478, n_bytes=36381, priority=1000,dl_dst=03:00:00:00:00:00/ff:00:00:00:00:00 actions=output:3
 cookie=0x0, duration=730.778s, table=0, n_packets=0, n_bytes=0, priority=1000,dl_dst=01:00:00:00:00:00/ff:00:00:00:00:00 actions=output:1
 cookie=0x0, duration=730.777s, table=0, n_packets=0, n_bytes=0, priority=1000,dl_dst=04:00:00:00:00:00/ff:00:00:00:00:00 actions=output:4
 cookie=0x0, duration=730.778s, table=0, n_packets=0, n_bytes=0, priority=1000,dl_dst=02:00:00:00:00:00/ff:00:00:00:00:00 actions=output:2
```
