#!/usr/bin/env python
import random

# Not supposed to be something dynamic, for now.
class Load_Balancer(object):
    def __init__(self):
        # Edge output ports in order of preference
        # It will be calculated in the load_balance method
        self.edge_out_ports = {}

    def lb_policy(self, edge_core):
        raise NotImplementedError

    def lb_action(self, edge):
        raise NotImplementedError


class Dummy_LBalancer(Load_Balancer):
    def __init__(self):
        super(Dummy_LBalancer, self).__init__()

    def lb_policy(self, edge_core):
        for edge in edge_core:
            self.edge_out_ports.setdefault(edge, {})
            core = random.choice([x for x in edge_core[edge]])
            self.edge_out_ports[edge] = (core, edge_core[edge][core])

    def lb_action(self, edge):
        return self.edge_out_ports[edge]


class IP_LBalancer(Load_Balancer):
    def __init__(self, config):
        super(IP_LBalancer, self).__init__()
        self.id_matcher = {}

    
    def init(self, cores, match_bytes):
        
        
        # fill bytearray with match
        # string like '00000011' or
        # int from 0 to 255
        arr_bytes = bytearray(len(match_bytes))
        for i in range(len(match_bytes)): 
            val = match_bytes[i]
            if isinstance(val, str):
                arr_bytes[i] = int(val, 2)
            elif isinstance(val,int):
                arr_bytes[i] = val
        #debug print
        #for i in range(len(arr_bytes)):
        #    print arr_bytes[i]


        # set for every match
        # [set([0]), set([0]), set([0]), set([0, 32, 64, 96])]
        # match_bytes [0, 0, 0, "01100000"]
        setarray = []
        for i in range(len(arr_bytes)):
            se = set([])
            for j in range(0, 255):
                se.add(arr_bytes[i] & j)
            setarray.append(se)
        #debug print
        #for i in se:
        #    print i
        print ("setarray: %s ") % setarray


        ##todo
        # idea to build matches from the different bytes 
        allset = set([])
        for index, value in enumerate(setarray):
            print(index, value)
            if len(value) > 1:
                setlist = list(value)
        for set_elem in setlist:
            var = (index+1-len(setlist))*256
            if (var == 0): 
                var=1
            allset.add(set_elem * var)
        #debug print
        print ("allset: %s ") % allset

        print ("setarray: %s") % setarray[3]
        idlist = []
        for id in set(setarray[3]):
            idlist.append(id)
        print ("idlist: %s") % idlist
        print ("len(idlist): %s" % len(idlist)

        print ("setarray: %s") % setarray[3]



        # link every core to a match
        # works only for the 4. byte
        for index, core in enumerate(cores):
            core_id = cores[core]
            
            set_elem = setarray[3] # fix atm look only at byte 4
            #elem = set_elem.pop()

            elem = idlist[index%len(cores)]
            print "elem: %s" % elem
            print "index,core: %s %s" % (index%len(cores),core)

            self.id_matcher.update({core_id:elem})

        #debug print    
        print ("id_matcher: %s ") % self.id_matcher


        #debug print
        for key, value in self.id_matcher.iteritems():
            print ("key[%s] = %s " % (key, value))
        print ("id_matcher[48]: %s ") % self.id_matcher[48]

    def get_ip_network(self):
        return self.id_matcher[max(self.id_matcher, key=self.id_matcher.get)]

    def check_possibile_fields(self, field):
        ipv4_fields = ["ipv4_src", "ipv4_dst"]
        if field in ipv4_fields:
            return field
        else:
            return 0

    def get_ip_match(self, match_id, field):
        METADATA_MASK = 0xffffffff
        ETH_TYPE_IP = 0x0800
        metadata = [match_id, METADATA_MASK]
        mask = self.get_ip_network()
        checked_field = self.check_possibile_fields(field)
        print ("mask: %s" % mask)
        ipv4_src = 0

        if match_id in self.id_matcher:
            #return decimal mask
            ipv4_src = (self.id_matcher[match_id], mask)
            #todo multi match
        match = {"eth_type": ETH_TYPE_IP, checked_field: ipv4_src, "ipv4_dst": ipv4_src}
        return match, metadata

    def get_flow_mod(self):
        return self.flow_mods

    def lb_policy(self, edge_core):
        for edge in edge_core:
            self.edge_out_ports.setdefault(edge, {})
            core = random.choice([x for x in edge_core[edge]])
            self.edge_out_ports[edge] = (core, edge_core[edge][core])

    def lb_action(self, edge):
        return self.edge_out_ports[edge]

