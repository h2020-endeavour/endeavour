# generate network equivalent to generic test-mh
# 3 participants
# combination of inbound and outbound rules
# additional test for unmatched traffic on port 8888

mode multi-hop
participants 3
peers 1 2 3

participant 1 100 5 08:00:27:89:3b:9f 172.0.0.1/16
participant 2 200 6 08:00:27:92:18:1f 172.0.0.11/16
participant 3 300 7 08:00:27:54:56:ea 172.0.0.21/16 8 08:00:27:bd:f8:b2 172.0.0.22/16

#host AS ROUTER _ IP          # host names of form a1_100 a1_110
host h NETNUMB _ AS ROUTER    # host names of the form h1_a1 h2_a1

announce 1 100.0.0.0/24 110.0.0.0/24
announce 2 140.0.0.0/24 150.0.0.0/24
announce 3 140.0.0.0/24 150.0.0.0/24

flow a1 80 >> b
flow a1 4321 >> c
flow a1 4322 >> c
flow c1 << 4321
flow c2 << 4322

listener AUTOGEN 80 4321 4322 8888

test regress {
	test xfer
}

test init {
	listener
}

test xfer {
	verify h1_a1 h1_b1 80
	verify h1_a1 h1_c1 4321
	verify h1_a1 h1_c2 4322
	verify h1_a1 h1_b1 8888
}

test info {
	local ovs-ofctl dump-flows s1
	local ovs-ofctl dump-flows s2
	local ovs-ofctl dump-flows s3
	local ovs-ofctl dump-flows s4
	exec a1 ip route
	bgp a1
	exec b1 ip route
	bgp b1
	exec c1 ip route
	bgp c1
	exec c2 ip route
	bgp c2
}
