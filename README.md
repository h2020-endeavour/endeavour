# Test Setup - MultiHop

Instructions to test the current code.

## Running with Torch

Torch has been adapted to run in Multi-Hop mode. Here is how to run it. 

```bash
$ cd ~/iSDX/test
$ sh buildall.sh
$ sudo bash startup.sh test1-mh
```

If you want to run the stats app with torch do:

```bash
$ sudo bash startup.sh --stats test1-mh
```
**Because configuration files for monitoring are not created by torch,
it is important to notice the need to add them to the folder of test1-mh/config/. 
You can find examples in /examples/test-mh/config/. You will need one config 
file for every switch that should be monitored.** 

Torch runs its tests and then quits. If you want to run in interactive mode, run as:
```bash
$ sudo bash startup.sh -i test1-mh
```

The above will run the system based on the test specification at https://github.com/h2020-endeavour/iSDX/blob/master/test/specs/test1-mh.spec

Read the Torch documentation at
https://github.com/h2020-endeavour/iSDX/blob/master/test/README.md

# Demo of use cases

## Advanced Blackholing demo
The advanced blackholing demo uses [test3-mh-bh.spec](https://github.com/h2020-endeavour/iSDX/blob/master/test/specs/test3-mh-bh.spec). 

The Grafana dashboard includes a blackholing-demo dashboard to visualize the traffic during the demo. The dashboard is available after reprovisioning of the VM: 

```bash
$ vagrant provision
``` 

Use the following instructions to run the blackholing demo it:

```bash
$ cd ~/iSDX/test
$ sh buildall.sh
$ sudo bash startup.sh --stats test3-mh-bh
```

# Previous instructions

## Logging to the ENDEAVOUR VM
Make sure that you are in the root folder containing all the files of this repo. The following command will start the ENDEAVOUR VM
```
vagrant up
```

The following command is used to log in to the vagrant VM
```
vagrant ssh
```

## Running the setup
The test-mh scenario has been wrapped in a tm-launch.sh shell script.
The tests from the setup are the same from the Multiple table with
a single switch scenario.

Before starting the tests, make sure to checkout the branch mh-ctrl in the 
iSDX repository of endeavour. 

## tmux script
This script will launch a tmux session with four windows running the components of the ENDEAVOUR platform. 
Login to the vagrant VM and run the following command: 

```bash
./endeavour/tm-launch.sh test-mh
```


As an alternative one can also start each component individually following the intructions below:

## Alternative Setup

```bash
$ cd ~/iSDX
$ git checkout mh-ctrlr
$ #git checkout add-grafana (if you want visualization)
```

### Log Server

```bash
$ cd ~
$ ./iSDX/launch.sh test-mh 1
```

This performs the following tasks:

```bash
$ cd ~/iSDX
$ sh pctrl/clean.sh
$ rm -f SDXLog.log
$ python logServer.py SDXLog.log
```

### Mininet
```bash
$ cd ~
$ ./endeavour/launch.sh test-mh 2
```

This performs the following tasks:

```bash
$ cd ~
$ sudo python endeavour/examples/test-mh/mininet/simple_sdx.py
```

### Run everything else
```bash
$ cd ~
$ ./endeavour/launch.sh test-mh 3 
$ #./endeavour/launch.sh --stats test-mh 3 if you want the stats app to be started.
```

This will start the following parts:

#### RefMon (Fabric Manager)
```bash
$ cd ~/iSDX/flanc
$ ryu-manager refmon.py --refmon-config ~/endeavour/examples/test-mh/config/sdx_global.cfg &
$ sleep 1
```

The RefMon module is based on Ryu. It listens for forwarding table modification instructions from the participant controllers and the IXP controller and installs the changes in the switch fabric. It abstracts the details of the underlying switch hardware and OpenFlow messages from the participants and the IXP controllers and also ensures isolation between the participants. Moreover, in the multi-hop scenario it decides in which switches the participants policies are installed. So far, it installs inbound polices in every edge of the fabric, while outbounds are installed in the respective participant edges.

#### xctrl (IXP Controller)
```bash
$ cd ~/iSDX/xctrl
$ python xctrl.py ~/endeavour/examples/test-mh/config/sdx_global.cfg
```

The IXP controller initializes the sdx fabric and installs all static default forwarding rules. 

#### uctrl (Umbrella Controller) (Still not sure if it will be joined with the IXP controller)

```bash
$ cd ~/endeavour/uctrl
$ python uctrl.py ~/endeavour/examples/test-mh/config/sdx_global.cfg
```

The Umbrella Controller installs flows to handle ARPs and traffic after processing on iSDX tables. Based on the destination, it encodes the path a packet will follow in the fabric on its destination MAC address. When the packet reaches the last hop, the real destination MAC address is rewritten. It also guarantees that ARPs from the fabric, queries and replies, reach the ARP relay and the respective participants, eliminating the need of broadcasts.

#### arpproxy (ARP Relay)
```bash
$ cd ~/iSDX/arproxy
$ sudo python arproxy.py test-mh &
$ sleep 1
```

This module receives ARP requests from the IXP fabric and it relays them to the corresponding participant's controller. It also receives ARP replies from the participant controllers which it relays to the IXP fabric. 

#### xrs (BGP Relay)
```bash
$ cd ~/iSDX/xrs
$ sudo python route_server.py test-mh &
$ sleep 1
```

The BGP relay is based on ExaBGP and is similar to a BGP route server in terms of establishing peering sessions with the border routers. Unlike a route server, it does not perform any route selection. Instead, it multiplexes all BGP routes to the participant controllers.

#### pctrl (Participant SDN Controller)
```bash
$ cd ~/iSDX/pctrl
$ sudo python participant_controller.py test-mh 1 &
$ sudo python participant_controller.py test-mh 2 &
$ sudo python participant_controller.py test-mh 3 &
$ sleep 1
```

Each participant SDN controller computes a compressed set of forwarding table entries, which are installed into the inbound and outbound switches via the fabric manager, and continuously updates the entries in response to the changes in SDN policies and BGP updates. The participant controller receives BGP updates from the BGP relay. It processes the incoming BGP updates by selecting the best route and updating the RIBs. The participant controller also generates BGP announcements destined to the border routers of this participant, which are sent to the routers via the BGP relay.

#### ExaBGP
```bash
$ cd ~/iSDX
$ exabgp examples/test-mh/config/bgp.conf
```

It is part of the `xrs` module itself and it handles the BGP sessions with all the border routers of the SDX participants.

## Testing the setup

### Test 1

Outbound policy of a1: match(tcp_port=80) >> fwd(b1)

```bash
mininext> h1_b1 iperf -s -B 120.0.0.1 -p 80 &  
mininext> h1_a1 iperf -c 120.0.0.1 -B 100.0.0.1 -p 80 -t 2
```

### Test 2

Outbound policy of a1: match(tcp_port=4321) >> fwd(c)
and Inbound policy of c: match(tcp_port=4321) >> fwd(c1)

```bash
mininext> h1_c1 iperf -s -B 140.0.0.1 -p 4321 &
mininext> h1_a1 iperf -c 140.0.0.1 -B 100.0.0.1 -p 4321 -t 2  
```

### Test 3 

Outbound policy of a1: match(tcp_port=4322) >> fwd(c)
and Inbound policy of c: match(tcp_port=4322) >> fwd(c2)

```bash
mininext> h1_c2 iperf -s -B 140.0.0.1 -p 4322 &  
mininext> h1_a1 iperf -c 140.0.0.1 -B 100.0.0.1 -p 4322 -t 2  
```

## Cleanup
Run the `clean` script:
```bash
$ sh ~/iSDX/pctrl/clean.sh
```

### Note
Always check with ```route``` whether ```a1``` sees ```120.0.0.0/24 ```, ```130.0.0.0/24```, ```140.0.0.0/24``` and ```150.0.0.0/24``` - ```b1``` sees ```100.0.0.0/24```, ```110.0.0.0/24```, ```140.0.0.0/24``` and ```150.0.0.0/24``` - ```c1 ```/```c2 ``` see ```100.0.0.0/24```, ```110.0.0.0.0/24```, ```120.0.0.0/24``` and ```130.0.0.0/24```
