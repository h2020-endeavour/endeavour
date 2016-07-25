# documentation of table content for the ENDEAVOUR architecture

# edge-1 switch

## table 0 - main-in
purpose of this table: 

* match BGP traffic (rule cookie=0x0)
* match ARP traffic (rule cookie=0x35)
* empty match is forwarded to table 3 (rule cookie=0x34)

```
vagrant@endeavour:~/endeavour$ sudo ovs-ofctl dump-flows edge-1 -O OpenFlow13 table=0
OFPST_FLOW reply (OF1.3) (xid=0x2):
 cookie=0x33, duration=116.468s, table=0, n_packets=0, n_bytes=0, priority=2,dl_dst=80:00:00:00:00:00/80:00:00:00:00:00 actions=goto_table:1
 cookie=0x32, duration=116.469s, table=0, n_packets=4, n_bytes=168, priority=9,arp,dl_dst=00:00:00:01:00:03/00:00:03:ff:ff:ff actions=set_field:08:00:27:bd:f8:b2->eth_dst,goto_table:4
 cookie=0x2f, duration=116.474s, table=0, n_packets=6, n_bytes=252, priority=9,arp,dl_dst=00:00:00:00:00:01/00:00:03:ff:ff:ff actions=set_field:08:00:27:89:3b:9f->eth_dst,goto_table:4
 cookie=0x31, duration=116.473s, table=0, n_packets=4, n_bytes=168, priority=9,arp,dl_dst=00:00:00:00:00:03/00:00:03:ff:ff:ff actions=set_field:08:00:27:54:56:ea->eth_dst,goto_table:4
 cookie=0x30, duration=116.473s, table=0, n_packets=6, n_bytes=252, priority=9,arp,dl_dst=00:00:00:00:00:02/00:00:03:ff:ff:ff actions=set_field:08:00:27:92:18:1f->eth_dst,goto_table:4
 cookie=0x0, duration=116.965s, table=0, n_packets=333, n_bytes=25250, priority=8,tcp,tp_src=179 actions=goto_table:4
 cookie=0x34, duration=116.468s, table=0, n_packets=208, n_bytes=17984, priority=1 actions=goto_table:3
 cookie=0x0, duration=116.965s, table=0, n_packets=1, n_bytes=70, priority=0 actions=CONTROLLER:65535
 cookie=0x1, duration=116.479s, table=0, n_packets=3, n_bytes=218, priority=5,in_port=5 actions=set_field:08:00:27:89:3b:9f->eth_src,goto_table:1
 cookie=0x35, duration=116.467s, table=0, n_packets=0, n_bytes=0, priority=8,arp,arp_tpa=172.0.1.0/24 actions=set_field:08:00:27:89:33:ff->eth_dst,goto_table:4
 cookie=0x0, duration=116.965s, table=0, n_packets=9, n_bytes=378, priority=7,arp actions=goto_table:5

```

## table 1 - outbound
purpose of this table: 

* empty match is forwarded to table 2 (rule cookie=0x38)

```
vagrant@endeavour:~/endeavour$ sudo ovs-ofctl dump-flows edge-1 -O OpenFlow13 table=1
OFPST_FLOW reply (OF1.3) (xid=0x2):
 cookie=0x10001, duration=96.933s, table=1, n_packets=0, n_bytes=0, priority=2,tcp,dl_src=08:00:27:89:3b:9f,dl_dst=10:00:00:00:00:00/50:00:00:00:00:00,tp_dst=80 actions=set_field:80:00:00:00:00:02->eth_dst,goto_table:2
 cookie=0x38, duration=104.837s, table=1, n_packets=3, n_bytes=218, priority=1 actions=goto_table:2
 cookie=0x0, duration=105.337s, table=1, n_packets=0, n_bytes=0, priority=0 actions=CONTROLLER:65535
 cookie=0x10002, duration=96.933s, table=1, n_packets=0, n_bytes=0, priority=2,tcp,dl_src=08:00:27:89:3b:9f,dl_dst=20:00:00:00:00:00/60:00:00:00:00:00,tp_dst=4321 actions=set_field:80:00:00:00:00:03->eth_dst,goto_table:2
 cookie=0x10003, duration=96.933s, table=1, n_packets=0, n_bytes=0, priority=2,tcp,dl_src=08:00:27:89:3b:9f,dl_dst=20:00:00:00:00:00/60:00:00:00:00:00,tp_dst=4322 actions=set_field:80:00:00:00:00:03->eth_dst,goto_table:2
```


## table 2 - inbound
purpose of this table: 

* empty match is forwarded to table 3 (rule cookie=0x37)

```
vagrant@endeavour:~/endeavour$ sudo ovs-ofctl dump-flows edge-1 -O OpenFlow13 table=2
OFPST_FLOW reply (OF1.3) (xid=0x2):
 cookie=0x37, duration=92.692s, table=2, n_packets=3, n_bytes=218, priority=1 actions=goto_table:3
 cookie=0x0, duration=93.191s, table=2, n_packets=0, n_bytes=0, priority=0 actions=CONTROLLER:65535
 cookie=0x30001, duration=84.954s, table=2, n_packets=0, n_bytes=0, priority=4,tcp,dl_dst=00:00:00:00:00:03/00:00:00:00:ff:ff,tp_dst=4321 actions=set_field:00:00:00:00:00:03->eth_dst,goto_table:3
 cookie=0x30002, duration=84.954s, table=2, n_packets=0, n_bytes=0, priority=4,tcp,dl_dst=00:00:00:00:00:03/00:00:00:00:ff:ff,tp_dst=4322 actions=set_field:00:00:00:01:00:03->eth_dst,goto_table:3
 cookie=0x36, duration=92.692s, table=2, n_packets=0, n_bytes=0, priority=3,dl_dst=00:00:00:00:00:03/00:00:00:00:ff:ff actions=set_field:00:00:00:00:00:03->eth_dst,goto_table:3

```

## table 3 - main-out
purpose of this table: 

* empty match is forwarded to table 4 (rule cookie=0x3d)

``` 
vagrant@endeavour:~/endeavour$ sudo ovs-ofctl dump-flows edge-1 -O OpenFlow13 table=3
OFPST_FLOW reply (OF1.3) (xid=0x2):
 cookie=0x3d, duration=83.018s, table=3, n_packets=161, n_bytes=14042, priority=1 actions=goto_table:4
 cookie=0x0, duration=83.520s, table=3, n_packets=0, n_bytes=0, priority=0 actions=CONTROLLER:65535
 cookie=0x39, duration=83.020s, table=3, n_packets=0, n_bytes=0, priority=4,dl_dst=00:00:00:00:00:03/00:00:03:ff:ff:ff actions=set_field:08:00:27:54:56:ea->eth_dst,goto_table:4
 cookie=0x3a, duration=83.019s, table=3, n_packets=0, n_bytes=0, priority=4,dl_dst=00:00:00:01:00:03/00:00:03:ff:ff:ff actions=set_field:08:00:27:bd:f8:b2->eth_dst,goto_table:4
 cookie=0x3b, duration=83.019s, table=3, n_packets=0, n_bytes=0, priority=4,dl_dst=00:00:00:00:00:01/00:00:00:00:ff:ff actions=set_field:08:00:27:89:3b:9f->eth_dst,goto_table:4
 cookie=0x3c, duration=83.018s, table=3, n_packets=6, n_bytes=420, priority=4,dl_dst=00:00:00:00:00:02/00:00:00:00:ff:ff actions=set_field:08:00:27:92:18:1f->eth_dst,goto_table:4
```

## table 4 - load-balancer

```
vagrant@endeavour:~/endeavour$ sudo ovs-ofctl dump-flows edge-1 -O OpenFlow13 table=4
OFPST_FLOW reply (OF1.3) (xid=0x2):
 cookie=0x0, duration=70.847s, table=4, n_packets=6, n_bytes=420, priority=0 actions=CONTROLLER:65535
 cookie=0x81, duration=69.939s, table=4, n_packets=20, n_bytes=840, priority=10,arp actions=write_metadata:0x40/0xffffffffff,goto_table:5
 cookie=0x7f, duration=69.939s, table=4, n_packets=0, n_bytes=0, priority=10,ip,nw_src=0.0.0.0/0.0.0.64,nw_dst=0.0.0.0/0.0.0.32 actions=write_metadata:0x30/0xffffffff,goto_table:5
 cookie=0x80, duration=69.939s, table=4, n_packets=0, n_bytes=0, priority=10,ip,nw_src=0.0.0.64/0.0.0.64,nw_dst=0.0.0.32/0.0.0.32 actions=write_metadata:0x40/0xffffffff,goto_table:5
 cookie=0x7e, duration=69.939s, table=4, n_packets=213, n_bytes=16350, priority=10,ip,nw_src=0.0.0.0/0.0.0.64,nw_dst=0.0.0.32/0.0.0.32 actions=write_metadata:0x20/0xffffffff,goto_table:5
 cookie=0x7d, duration=69.939s, table=4, n_packets=145, n_bytes=12522, priority=10,ip,nw_src=0.0.0.64/0.0.0.64,nw_dst=0.0.0.0/0.0.0.32 actions=write_metadata:0x10/0xffffffff,goto_table:5
```


## table 5 - umbrella-edge

```
vagrant@endeavour:~/endeavour$ sudo ovs-ofctl dump-flows edge-1 -O OpenFlow13 table=5
OFPST_FLOW reply (OF1.3) (xid=0x2):
 cookie=0x25, duration=49.486s, table=5, n_packets=4, n_bytes=168, priority=4,metadata=0x40,dl_dst=08:00:27:54:56:ea actions=set_field:03:05:00:00:00:00->eth_dst,output:4
 cookie=0x28, duration=49.483s, table=5, n_packets=0, n_bytes=0, priority=4,metadata=0x20,dl_dst=08:00:27:bd:f8:b2 actions=set_field:04:05:00:00:00:00->eth_dst,output:2
 cookie=0x27, duration=49.484s, table=5, n_packets=28, n_bytes=2453, priority=4,metadata=0x10,dl_dst=08:00:27:bd:f8:b2 actions=set_field:04:05:00:00:00:00->eth_dst,output:1
 cookie=0x20, duration=49.486s, table=5, n_packets=0, n_bytes=0, priority=4,metadata=0x20,dl_dst=08:00:27:92:18:1f actions=set_field:02:05:00:00:00:00->eth_dst,output:2
 cookie=0x1f, duration=49.486s, table=5, n_packets=31, n_bytes=2651, priority=4,metadata=0x10,dl_dst=08:00:27:92:18:1f actions=set_field:02:05:00:00:00:00->eth_dst,output:1
 cookie=0x21, duration=49.486s, table=5, n_packets=6, n_bytes=252, priority=4,metadata=0x40,dl_dst=08:00:27:92:18:1f actions=set_field:02:05:00:00:00:00->eth_dst,output:4
 cookie=0x24, duration=49.486s, table=5, n_packets=0, n_bytes=0, priority=4,metadata=0x20,dl_dst=08:00:27:54:56:ea actions=set_field:03:05:00:00:00:00->eth_dst,output:2
 cookie=0x26, duration=49.486s, table=5, n_packets=0, n_bytes=0, priority=4,metadata=0x30,dl_dst=08:00:27:54:56:ea actions=set_field:03:05:00:00:00:00->eth_dst,output:3
 cookie=0x22, duration=49.486s, table=5, n_packets=0, n_bytes=0, priority=4,metadata=0x30,dl_dst=08:00:27:92:18:1f actions=set_field:02:05:00:00:00:00->eth_dst,output:3
 cookie=0x29, duration=49.483s, table=5, n_packets=4, n_bytes=168, priority=4,metadata=0x40,dl_dst=08:00:27:bd:f8:b2 actions=set_field:04:05:00:00:00:00->eth_dst,output:4
 cookie=0x23, duration=49.486s, table=5, n_packets=30, n_bytes=2585, priority=4,metadata=0x10,dl_dst=08:00:27:54:56:ea actions=set_field:03:05:00:00:00:00->eth_dst,output:1
 cookie=0x2a, duration=49.482s, table=5, n_packets=0, n_bytes=0, priority=4,metadata=0x30,dl_dst=08:00:27:bd:f8:b2 actions=set_field:04:05:00:00:00:00->eth_dst,output:3
 cookie=0x0, duration=50.292s, table=5, n_packets=1, n_bytes=42, priority=0 actions=CONTROLLER:65535
 cookie=0x3, duration=49.486s, table=5, n_packets=4, n_bytes=168, priority=8,arp,arp_tpa=172.0.255.254 actions=set_field:08:00:27:89:3b:ff->eth_dst,output:6
 cookie=0x1, duration=49.494s, table=5, n_packets=0, n_bytes=0, priority=8,arp,arp_tpa=172.0.255.253 actions=set_field:08:00:27:89:33:ff->eth_dst,output:7
 cookie=0x9, duration=49.486s, table=5, n_packets=1, n_bytes=42, priority=8,arp,arp_tpa=172.0.0.22 actions=set_field:04:05:00:00:00:00->eth_dst,output:2
 cookie=0x8, duration=49.486s, table=5, n_packets=1, n_bytes=42, priority=8,arp,arp_tpa=172.0.0.21 actions=set_field:03:05:00:00:00:00->eth_dst,output:2
 cookie=0x2, duration=49.486s, table=5, n_packets=1, n_bytes=42, priority=8,arp,arp_tpa=172.0.0.1 actions=set_field:08:00:27:89:3b:9f->eth_dst,output:5
 cookie=0x7, duration=49.486s, table=5, n_packets=1, n_bytes=42, priority=8,arp,arp_tpa=172.0.0.11 actions=set_field:02:05:00:00:00:00->eth_dst,output:2
 cookie=0x77, duration=49.384s, table=5, n_packets=0, n_bytes=0, priority=4,dl_dst=00:07:00:00:00:00/00:ff:00:00:00:00 actions=set_field:08:00:27:89:33:ff->eth_dst,output:7
 cookie=0x79, duration=49.384s, table=5, n_packets=117, n_bytes=9042, priority=4,dl_dst=00:06:00:00:00:00/00:ff:00:00:00:00 actions=set_field:08:00:27:89:3b:ff->eth_dst,output:6
 cookie=0x78, duration=49.384s, table=5, n_packets=0, n_bytes=0, priority=4,dl_dst=00:05:00:00:00:00/00:ff:00:00:00:00 actions=set_field:08:00:27:89:3b:9f->eth_dst,output:5
 cookie=0x1b, duration=49.486s, table=5, n_packets=40, n_bytes=3080, priority=4,dl_dst=08:00:27:89:3b:ff actions=output:6
 cookie=0x19, duration=49.486s, table=5, n_packets=0, n_bytes=0, priority=4,dl_dst=08:00:27:89:33:ff actions=output:7
 cookie=0x1a, duration=49.486s, table=5, n_packets=34, n_bytes=2705, priority=4,dl_dst=08:00:27:89:3b:9f actions=output:5
``