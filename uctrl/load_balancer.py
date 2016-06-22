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
        

    
    def init(self, cores, match_bytes):
        
        self.id_matcher = {}

        # fill bytearray with match
        # string like '00000011' or
        # int from 0 to 255
        byte_array = bytearray(len(match_bytes))
        for i in range(len(match_bytes)): 
            val = match_bytes[i]
            if isinstance(val, str):
                byte_array[i] = int(val, 2)
            elif isinstance(val,int):
                byte_array[i] = val
        #debug print
        #for i in range(len(arr_bytes)):
        #    print arr_bytes[i]


        # set for every match
        # [set([0]), set([0]), set([0]), set([0, 32, 64, 96])]
        # match_bytes [0, 0, 0, "01100000"]
        set_array = []
        for i in range(len(byte_array)):
            new_set = set([])
            for j in range(0, 255):
                new_set.add(byte_array[i] & j) # logic AND
            set_array.append(new_set)
        #debug print
        #for i in se:
        #    print i
        print ("setarray: %s ") % set_array


        ##todo
        # idea to build matches from the different bytes 
        allset = set([])
        for index, value in enumerate(set_array):
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

        print ("setarray: %s") % set_array[3]
        

        idlist = []
        for id in set(set_array[3]):
            idlist.append(id)
        print ("idlist: %s") % idlist
        print ("len(idlist: %s") % len(idlist)

        print ("setarray: %s") % set_array[3]



        # link every core to a match
        # works only for the 4. byte
        for index, core in enumerate(cores):
            core_id = cores[core]
            
            set_elem = set_array[3] # fix atm look only at byte 4
            #elem = set_elem.pop()

            elem = idlist[index%len(idlist)]
            print "elem: %s" % elem
            print "index,core: %s %s" % (index%len(idlist),core)

            self.id_matcher.update({core_id:elem})

        #debug print    
        print ("id_matcher: %s ") % self.id_matcher
        return self.id_matcher

        #debug print
        #for key, value in self.id_matcher.iteritems():
        #    print ("key[%s] = %s " % (key, value))
        #print ("id_matcher[48]: %s ") % self.id_matcher[48]

    def get_ip_network(self):
        return self.id_matcher[max(self.id_matcher, key=self.id_matcher.get)]

    def get_ip_network(self, network):
        return network[max(network, key=network.get)]

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
        ipv4_src = 0

        if match_id in self.id_matcher:
            #return decimal mask
            ipv4_src = (self.id_matcher[match_id], mask)
            #todo multi match
        #match = {"eth_type": ETH_TYPE_IP, checked_field: ipv4_src, "ipv4_dst": ipv4_src}
        match = {"eth_type": ETH_TYPE_IP, checked_field: ipv4_src}
        return match, metadata

    def get_ip_multi_match(self, match_id, *matches):
        METADATA_MASK = 0xffffffff
        ETH_TYPE_IP = 0x0800
        metadata = [match_id, METADATA_MASK]
        match = {"eth_type": ETH_TYPE_IP}
        ipv4 = 0
        mask = 0

        #print (matches)

        #new_set = set([])
        #for j in range(0, 255):
        #new_set.add(byte_array[i] & j) # logic AND
        #set_array.append(new_set)

        for element in matches:
            print ("element: %s") % element

            for field_key in element:
                id_matcher = element[field_key]
                print ("id_matcher: %s") % id_matcher

                checked_field = self.check_possibile_fields(field_key)
                mask = self.get_ip_network(id_matcher)

                #print ("match_id: %s matches[field_key]: %s field_key: %s match_id: %s mask: %s") % (match_id, element[field_key], field_key, match_id, mask)

                if match_id in element[field_key]:
                    ipv4 = (id_matcher[match_id], mask)

            add_match = {checked_field: ipv4}
            match.update(add_match)

        print match
            
        #for field_key in matches:
        #    checked_field = self.check_possibile_fields(field_key)
            #mask = self.get_ip_network(matches[field_key])
        #    print ("match_id: %s matches[field_key]: %s field_key: %s match_id: %s mask: %s") % (match_id, matches[field_key], field_key, match_id, mask)

        #    if match_id in matches[field_key]:
        #        print ("true") 
                #ipv4 = (matches[field_key][match_id], mask)
            
        #    add_match = {checked_field: ipv4}
        #    match.update(add_match)
        #    print matches[field_key]
       
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

