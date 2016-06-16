'''
Created on Mar 17, 2016

@author: Marc Pucci
'''
import json

class parser:
    
    bgprouters = []                 # hosts that are routers, not listeners, but we may want to send commands to anyway
    peers = []                      # holds multiple peer group relationships
    listeners = {}                  # holds details for a listener
    tests = {}                      # holds details for named tests
    mode = None                     # multi-switch or multi-table
    policies = {}                   # details on participant policies (flow rules)
    participants = {}               # details on each participant
    cookie_id = 1                   # common cookie ID for flow rules (should this be per participant?)

    def __init__(self, cfile):

        try:
            f = open(cfile)
        except Exception, e:
            raise Exception('cannot open configuration file: ' + cfile + ': ' + repr(e))
        
        lines = 0    
        for line in f:
            lines += 1
            line = line.partition('#')[0]
            
            gather = []
            if "{" in line:
                got = False
                for line2 in f:
                    line2 = line2.partition('#')[0]

                    lines += 1
                    if '}' in line2:
                        got = True
                        break
                    gather.append(line2)
                if not got:
                    f.close()
                    raise Exception('Fatal error on line ' + str(lines) + ': unmatched { ... }')
            
            try:
                self._parse(line, gather)
            except Exception as err:
                f.close()
                raise Exception('Fatal error on line ' + str(lines) + ': ' + line + ' (' + str(err) + ')')
        f.close
        self._seenall()
        
        
    def _parse (self, line, gather):
        tokens = line.split()
        if len(tokens) == 0:
            return
        self._seen(tokens[0])
        
        if tokens[0] == 'participants':
            self._do_participants(tokens)
        elif tokens[0] == 'participant':
            self._do_participant(tokens)
        elif tokens[0] == 'flow':
            self._do_flow(tokens)
        elif tokens[0] == 'announce':
            self._do_announce(tokens)
        elif tokens[0] == 'peers':
            self._do_peers(tokens)
        elif tokens[0] == 'mode':
            self._do_mode(tokens)
        elif tokens[0] == 'test':
            self._do_test(tokens, gather)
        elif tokens[0] == 'listener':
            self._do_listener(tokens)
        elif tokens[0] == 'host':
            self._do_host(tokens)
        else:
            raise Exception('unrecognized command')
    
    
    def _do_participants (self, args):        
        number = args[1]
        for i in range(1, int(number) + 1):
            self._get_policy(str(i))
        self.number_of_participants = int(number)
    
            
    def _do_flow (self, args):
        if args[3] == '>>':
            self._outbound(args[1], args[2], args[4])
        elif args[2] == '<<':
            self._inbound(args[1], args[3])
        else:
            raise Exception('bad flow format')
        
            
    def _get_policy (self, name):        
        try:
            policy = self.policies[name]
        except:
            policy = {}
            policy["outbound"] = []
            policy["inbound"] = []
            self.policies[name] = policy
        return policy
    
                  
    def _inbound (self, dst, port):        
        #print 'inbound: dst=' + dst + ' port=' + port
        das, dasport = host2as_router(dst)
        n = as2part(das)
        
        policy = self._get_policy(n)
        tmp_policy = {}
        tmp_policy["cookie"] = self.cookie_id
        self.cookie_id += 1
    
        tmp_policy["match"] = {}
        tmp_policy["match"]["tcp_dst"] = int(port)
        tmp_policy["action"] = {"fwd": int(dasport)}
    
        # Add this to participants' outbound policies
        policy["inbound"].append(tmp_policy)
            
    
    def _outbound (self, src, port, dst):        
        #print 'outbound: src=' + src + ' port=' + port + ' dst=' + dst
        sas, sasport = host2as_router(src)
        das = dst  # destination is an AS not a host !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1
        #print 'sas=' + sas + ' sasport=' + sasport + ' das=' + das
        
        n = as2part(sas)
        policy = self._get_policy(n)
            
        tmp_policy = {}
    
        # Assign Cookie ID
        tmp_policy["cookie"] = self.cookie_id
        self.cookie_id += 1
    
        # Match
        tmp_policy["match"] = {}
        tmp_policy["match"]["tcp_dst"] = int(port)
        # forward to participant number: convert name to assumed number (a=1)
        tmp_policy["action"] = {"fwd": int(as2part(das))}
        
        policy["outbound"].append(tmp_policy)
    
    
    # participant 3 300 7 08:00:27:54:56:ea 172.0.0.21 8 08:00:27:bd:f8:b2 172.0.0.22
    
    def _do_participant (self, args):        
        if len(args) < 6 or len(args) % 3 != 0:
            raise Exception('usage: participant # ASN switchport MAC IP ...')
        part = args[1]
        ipart = int(part)
        asn = args[2]
        
        i = 3
        
        p = self.participants.get(part, {})
        p['ASN'] = asn
        routers = []
        index = 0
        while i < len(args):
            port = self._checkport(args[i])
            mac = self._checkmac(args[i+1], ipart, index)
            ip = args[i+2]
            i += 3
            #print 'part=' + part + ' asn=' + asn + ' port=' + port + ' mac=' + mac + ' ip=' + ip
    
            router = {}
            router['hostname'] = part_router2host(part, index)
            self.bgprouters.append(part_router2host(part, index))
            router['Id'] = int(port) # switch port
            router['MAC'] = mac
            if len(ip.split('/')) != 2:
                raise Exception('malformed network address ' + ip)
            router['IP'] = ip.split('/')[0]
            router['NET'] = ip
            router['index'] = index
            router['description'] = 'Virtual AS ' + part2as(part)
            if len(args) > 6:
                router['description'] += ' Router ' + router['hostname']
            index += 1
            routers.append(router)
        p['Ports'] = routers
        
        # get the peer group and gen the peer set (less this instance)
        found = False
        for pg in self.peers:
            if found:
                break
            for n in pg:
                if n == ipart:
                    found = True
                    mypeers = []
                    for m in pg:
                        if m != ipart:
                            mypeers.append(m)
                    p['Peers'] = mypeers
                    break
        '''        
        # do inbound and outbound rules exist (participant defs must follow flows)      
        if len(policies[part]['inbound']) != 0:
            p['Inbound Rules'] = True
        else:
            p['Inbound Rules'] = False
        if len(policies[part]['outbound']) != 0:
            p['Outbound Rules'] = True
        else:
            p['Outbound Rules'] = False
        '''        
        self.participants[part] = p

    
    # define formatter for names of hosts.  special macros are:
    # IP first part of network address, i.e., 150 in 150.0.0.0.24
    # ROUTER - router number styarting from 1
    # NET - network number starting from 1
    # AS - AS letter name
    
    hostformer = []
    
    def _do_host (self, args):        
        self.hostformer = []
        if len(args) < 2: 
            raise Exception('usage: host sequence of chars, IP, ROUTER, NET, AS (will be concatenated)')
        for i in range(1, len(args)):
            self.hostformer.append(args[i])
    
    
    # announce participant# name network name network ...
    # if a network starts with a dash, it will be configured but not announced to BGP
    
    def _do_announce (self, args):        
        if len(args) < 3: 
            raise Exception('usage: announce participant# network network ...')      
        
        announcements = []
        networks = []
        announce = True
        
        part = args[1]
        p = self.participants.get(part, {})
        netnumb = 0
        for i in range(2, len(args)):
            net = args[i]
            if net[0] == '-':
                net = net[1:]
                announce = False
            ip_fix = net.split('/')
            if len(ip_fix) != 2:
                raise Exception('Invalid network announcement ' + net)
            ip = ip_fix[0].split('.')
            if len(ip) != 4:
                raise Exception('Invalid ip address ' + ip_fix[0])
            if announce:
                announcements.append(net)
            networks.append(net)
            for r in p['Ports']:  # routers
                n = self.genname(netnumb, net, part2as(part), r['index'])
                #print 'auto gen nodename = ' + n
                # seed with the bind address in case will autogen nodes
                # and empty ports for sanity
                self.listeners[n] = {'bind': ip[0] + '.' + ip[1] + '.' + ip[2] + '.' + '1',
                            'ports': [] }
            netnumb += 1
        p['announcements'] = announcements
        p['networks'] = networks
    
    
    def _do_peers (self, args):        
        if len(args) == 1:
            raise Exception('usage: peers participant_member participant_member ...')
        p = []
        for i in range(1, len(args)):
            n = int(args[i])
            if n < 1 or n > self.number_of_participants:
                raise Exception('bad peer group value')
            p.append(n)
        #print p
        self.peers.append(p)
    
    
    def _do_mode (self, args):        
        if len(args) != 2:
            raise Exception('usage: mode multi-switch | multi-table | multi-hop')
        if self.mode is not None:
            raise Exception('error: mode already set')
        
        self.mode = args[1]
        
        if self.mode == 'multi-switch':
            for i in ['1', '2', '3', '4']:
                self._checkport(i)
        elif self.mode == 'multi-table':
            for i in ['1', '2']:
                self._checkport(i)
        elif self.mode == 'multi-hop':
            for i in ['1', '2', '3', '4']:
                self._checkport(i)
        else:
            raise Exception('unknown mode')
    
    
    def _do_listener (self, args):
        autogen = len(args) > 2 and args[1] == 'AUTOGEN'
        if autogen and len(args) < 3 or not autogen and len(args) < 4:
            raise Exception('usage: node host binding_address port ... OR node AUTOGEN port port ...')
        if autogen:
            for nn in sorted(self.listeners):
                n = self.listeners[nn]
                ports = []
                for i in range(2, len(args)):
                    ports.append(args[i])
                n['ports'] = ports
                #print 'auto gen node = ' + nn + ' ' + n['bind'] + ' ' + str(n['ports'])
            return
        n = self.listeners.get(args[1])
        if n is None:
            raise Exception('Node ' + args[1] + ' is not defined by an earlier network announcement')
        if len(n['ports']) != 0:
            raise Exception('Node ' + args[1] + ' is already defined')
        n['bind'] = args[2]
        ports = []
        for i in range(3, len(args)):
            ports.append(args[i])
        n['ports'] = ports

    
    def _do_test (self, args, gather):
        if len(args) != 3 or args[2] != "{":
            raise Exception('usage: test testname {\n             test commands\n         }\n ')
        testname = args[1]
        testcmds = []
        
        for line in gather:
            line = line.partition('#')[0]
            args = line.split()
            if len(args) == 0:
                continue
            
            testcmds.append(line.strip())
            
            # perform sanity checks on test commands to avoid surprises
            # keep up to date with tmgr
            # todo - tmgr should use tlib to check commands as in verifycheck() 
    
            if args[0] == 'send':
                continue
            
            if args[0] == 'verify':
                if len(args) != 4:
                    raise Exception('usage: verify src dst port')
                self.verifycheck(args[1], args[2], args[3])
                continue
            
            if args[0] == 'exec':
                if len(args) < 3:
                    raise Exception('bad run command: usage: run host cmd args ...')
                host = args[1]
                if host == 'local' or host == 'bgp' or host == 'hosts':
                    continue
                if host in self.listeners or host in self.bgprouters:
                    continue
                raise Exception('bad run command: unknown host: ' + host)
            
            if args[0] == 'dump':
                continue
            
            if args[0] == 'announce' or args[0] == 'withdraw':
                continue
            
            if args[0] == 'delay':
                continue
            
            if args[0] == 'listener':
                continue

            if args[0] == 'local':
                continue
            
            if args[0] == 'test':
                continue
            
            if args[0] == 'bgp':
                continue
            
            raise Exception('unknown test command: ' + args[0])   
        
        self.tests[testname] = testcmds    

    # early checks for test command correctness
    
    def verifycheck (self, src, dst, dport):                
        # validate that the source is a valid node - the binding address also comes from the node description
        try:
            n = self.listeners[src]
            baddr = n['bind']
        except:
            raise Exception('bad source node: ' + src)
    
        # validate the destination - the destination address also comes from the node description
        # there must be a listener for the port
        found = False
        try:
            i = 0
            for p in self.listeners[dst]['ports']:
                if p == dport:
                    daddr = self.listeners[dst]['bind']
                    found = True
                    break
                i += 1
        except:
            raise Exception('bad destination node: ' + dst)
        if found == False:
            raise Exception('bad destination port - no listener defined') 
        return (baddr, daddr)   
     
    # check if commands have appeared in the right order
    # all predecessor commands must be seen before this cmd
    # all successor cmds must not have occurred
    # return True if cmd has already been seen
    
    cmdorder = [ 'mode', 'participants', 'peers', 'participant', 'host', 'announce', 'flow', 'listener', 'test']
    cmdoptional = ['listener', 'test']
    cmdseen = {}
        
    def _seen (self, cmd):
        if cmd not in self.cmdorder:
            raise Exception('unknown command: ' + cmd)
        if cmd in self.cmdseen:
            already = True
        else:
            already = False
        self.cmdseen[cmd] = True
        match = False
        for i in self.cmdorder:
            if i == cmd:
                match = True
                continue
            if not match: # must have been seen
                if i not in self.cmdseen:
                    raise Exception(i + ' must be specified before ' + cmd)
            else:
                if i in self.cmdseen:
                    raise Exception(cmd + ' must be specified before ' + i)
        return already
    
    
    def _seenall (self):
        for i in self.cmdorder:
            if i not in self.cmdseen:
                if i in self.cmdoptional:
                    continue
                raise Exception('specification for ' + i + ' is missing')

    
    checkports = {} 
    
    def _nextport (self):
        for i in range(1, 100):
            if str(i) not in self.checkports:
                return str(i)
        raise Exception('out of ports')
    
    def _checkport (self, i):
        if i == 'PORT':
            i = self._nextport()
            #print 'auto gen port = ' + i
        if i in self.checkports:
            raise Exception('port ' + i + ' is already used')
        try:
            ii = int(i)
        except:
            raise Exception(i + ' is an invalid port number')
        if ii <= 0:
            raise Exception(i + ' is an invalid port number')
        self.checkports[i] = True
        return i
        
    # see if there is a gap in the switch port sequence
    # this was/is a bug with mininext/mininet
    def portgap (self):
        gap = False
        for i in range(1, 50):
            if str(i) not in self.checkports:
                gap = True
            elif gap == True:
                return True
        return False
    
    checkmacs = {} 
    
    # 08:00:27:54:56:ea
    def _checkmac (self, mac, part, router):
        if mac == 'MAC':
            mac = nextmac(part, router)
            #print 'auto gen mac = ' + mac
        if mac in self.checkmacs:
            raise Exception('mac ' + mac + ' is already used')
        if len(mac) != 17:
            raise Exception('mac ' + mac + ' is poorly formatted')
        digits = mac.split(':')
        if len(digits) != 6:
            raise Exception('mac ' + mac + ' is poorly formatted')
        for pair in digits:
            if len(pair) != 2:
                raise Exception('mac ' + mac + ' is poorly formatted')
            try:
                int(pair, 16)
            except ValueError:
                raise Exception('mac ' + mac + ' is not hexadecimal')
        self.checkmacs[mac] = True
        return mac

    
    def genname (self, netnumb, ip, asys, router):
        h = ''
        for i in self.hostformer:
            if i == 'NETNUMB':
                h += str(netnumb + 1)
            elif i == 'IP':
                h += ip.split('.')[0]
            elif i == 'ROUTER':
                h += str(int(router) + 1)
            elif i == 'AS':
                h += asys
            else:
                h += i
        return h
        
# convert participant + index into a1, b1, c1, c2, etc., index starts at 0
def part_router2host(part, router):
    return part2as(part) + str(router + 1)

# names run from a - z, then aa, ab, ac, ... az, ba
nameset = 'abcdefghijklmnopqrstuvwxyz'
routerset = '0123456789'

def as2part (name):
    p = 0
    for c in name:
        p = p * len(nameset)
        n = nameset.find(c)
        if n < 0:
            raise Exception('bad AS name: ' + name)
        p += n + 1
    if p < 1: ############# TODO  or p > number_of_participants:
        raise Exception('Illegal AS name: ' + name)
    return str(p)


def part2as (part):
    part = int(part)    # just in case
    if part < 1: ############## TODO  or part > number_of_participants:
        raise Exception('Illegal participant number: ' + str(part))
    base = len(nameset)
    n = ''
    while part != 0:
        n += nameset[(part-1) % base]
        part = (part - 1) / base
    return n[::-1]


def host2as_router(name):
    asys = ''
    r = ''
    lookforasys = True
    foundasys = False
    for c in name:
        if c in nameset:
            if not lookforasys:
                raise Exception('bad hostname: ' + name)
            asys += c;
            foundasys = True
        elif c in routerset:
            if not foundasys:
                raise Exception('bad hostname: ' + name)
            lookforasys = False
            r += c
    if not foundasys or r == '':
        raise Exception('bad hostname: ' + name)
    n = int(r)
    if n <= 0:
        raise Exception('bad hostname: ' + name)
    n -= 1  # routers run from 0 even though host is called a1, a2
    
    ################# TODO 
    # is this a valid AS and router?
    #p = as2part(asys)   # will raise exception if out of range
    #if n >= len(self.participants[p]['Ports']): # number of edge-routers
        #raise Exception('router does not exist for ' + name)
    return asys, str(n)


# generate a mac address   
def nextmac (part, router):
    a = 0x08
    b = 0x00
    c = 0xBB
    d = 0xBB
    e = part
    f = router
    return '%02x:%02x:%02x:%02x:%02x:%02x' % (a, b, c, d, e, f)
    
if __name__ == "__main__":
    p = parser('specs/test1-ms.spec')
    print 'bgprouters'
    print json.dumps(p.bgprouters, indent=4, sort_keys=True) 
    print 'peers'
    print json.dumps(p.peers, indent=4, sort_keys=True) 
    print 'listeners'
    print json.dumps(p.listeners, indent=4, sort_keys=True) 
    print 'tests'
    print json.dumps(p.tests, indent=4, sort_keys=True) 
    print 'mode'
    print json.dumps(p.mode, indent=4, sort_keys=True) 
    print 'policies'
    print json.dumps(p.policies, indent=4, sort_keys=True) 
    print 'participants'
    print json.dumps(p.participants, indent=4, sort_keys=True) 