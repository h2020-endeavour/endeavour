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
        
        
    def init_match(self, match_bytes):
        
        self.match_list = [] # list

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
        #for i in range(len(byte_array)):
        #    print byte_array[i]


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
        #for i in set_array:
        #    print i
        #print ("setarray: %s ") % set_array


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
        #print ("allset: %s ") % allset

        #print ("setarray: %s") % set_array[3]
        for match in set(set_array[3]):
            self.match_list.append(match)
        return self.match_list
        #print ("idlist: %s") % idlist
        #print ("len(idlist: %s") % len(idlist)
        #print ("setarray: %s") % set_array[3]

    def set_core_match(self, cores, match_list):
        self.id_matcher = {} # key value
        # link every core to a match
        for index, core in enumerate(cores):
            core_id = cores[core] # index or core
            elem = match_list[index%len(match_list)]
            self.id_matcher.update({core_id:elem})

    def get_ip_match(self, match_id, field):
        METADATA_MASK = 0xffffffff
        ETH_TYPE_IP = 0x0800
        metadata = [match_id, METADATA_MASK]
        mask = self.get_ip_network()
        checked_field = self.check_possibile_fields(field)
        ipv4 = 0

        if match_id in self.id_matcher:
            #return decimal mask
            ipv4 = (self.id_matcher[match_id], mask)
        match = {"eth_type": ETH_TYPE_IP, checked_field: ipv4}
        return match, metadata

    # -----------------------------------------------------------------------------------

    def init_multi_match(self, match_byte1, match_byte2):
        return self.init_match(match_byte1), self.init_match(match_byte2)


    def set_core_multi_match(cores, match_list):
        self.id_matcher = {} # key value
        subsets = get_subsets(match_list)
        # link every core to a match
        for index, core in enumerate(cores):
            core_id = cores[core] # index or core
            elem = subsets[index%len(subsets)]
            self.id_matcher.update({core_id:elem})
       
    def get_ip_multi_match(self, match_id, fields):
        METADATA_MASK = 0xffffffff
        ETH_TYPE_IP = 0x0800
        metadata = [match_id, METADATA_MASK]
        mask = self.get_ip_network()

        ipv4 = 0
        match = {"eth_type": ETH_TYPE_IP}

        for index, field in enumerate(fields):
            checked_field = self.check_possibile_fields(field)
            
            if match_id in self.id_matcher:
                #return decimal tupelmask
                ipv4 = self.id_matcher[match_id]
                match.update({checked_field : (ipv4[index], mask[index])})

        return match, metadata

  # -----------------------------------------------------------------------------------

    # need for mask
    def get_ip_network(self):
        return self.id_matcher[max(self.id_matcher, key=self.id_matcher.get)]

    # need for field_check
    def check_possibile_fields(self, field):
        ipv4_fields = ["ipv4_src", "ipv4_dst"]
        if field in ipv4_fields:
            return field
        else:
            return 0

    def get_subsets(set1, set2):
        new_set = set([])
        for elem1 in set1:
            for elem2 in set2:
                elem = (elem1,elem2)
                new_set.add(elem)
        return list(new_set)


    def get_flow_mod(self):
        return self.flow_mods

    def lb_policy(self, edge_core):
        for edge in edge_core:
            self.edge_out_ports.setdefault(edge, {})
            core = random.choice([x for x in edge_core[edge]])
            self.edge_out_ports[edge] = (core, edge_core[edge][core])

    def lb_action(self, edge):
        return self.edge_out_ports[edge]

