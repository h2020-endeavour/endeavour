#!/usr/bin/python

#  Author:
#  Marc Pucci (Vencore Labs)

# tmgr - traffic manager - controls a constellation of traffic nodes
# to gen and recv traffic from / to specific bound interfaces and ports

import sys
import json
import socket
import random
import string
import platform
import os
import subprocess
import traceback
import time
import shlex

import tlib

np = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if np not in sys.path:
    sys.path.append(np)
import util.log

config = None       # parsed spec file
hosts = {}
tests = {}
bgprouters = []

cmdfuncs = {}

# friendly logger - prints to stdout and logs.
# TODO check to see if logging is actually happening and print only if so

class flog ():
    def __init__(self, name):
        self.logger = util.log.getLogger(name)
    def info(self, m):
        print m
        self.logger.info(m)
    def debug(self, m):
        print m
        self.logger.debug(m)
    def error(self, m):
        print m
        self.logger.error(m)

log = flog('TMGR')
log.info("Starting TMGR")

def main (argv):
    global config, bgprouters, hosts, tests, cmdfuncs
    
    if len(argv) < 2:
        log.error('usage: tmgr config.spec [ commands ]')
        exit()
    
    try:
        config = tlib.parser(argv[1])
    except Exception, e:
        log.error('Bad configuration: ' + repr(e))
        exit()
    
    hosts = config.listeners
    tests = config.tests
    bgprouters = config.bgprouters
       
    cmdfuncs = {
        'listener': listener, 'l': listener,
        'test': test, 't': test,
        'verify': verify, 'v': verify,
        'announce': announce, 'a': announce, 
        'withdraw': withdraw, 'w': withdraw,
        'bgp': bgp,
        'delay': delay,
        'exec': remote, 'x': remote, 'remote': remote,
        'local': local, 'll': local,
        'pending': pending, 'p': pending,
        'send': send, 's': send,
        'comment': comment, 'c': comment,
        'reset': reset, 'z': reset,
        'kill': kill, 'k': kill,
        'dump': dump, 'd': dump,
        'config': show, 
        'help': usage, '?': usage,
        'quit': terminate, 'q': terminate,
    }
    
    if len(argv) == 2:
        while True:
            try:
                parse(raw_input("> "))
            except EOFError:
                break
            except KeyboardInterrupt:
                print '****'
                continue
            except Exception, e:
                log.error('MM:00 ERROR: ' + repr(e))
                traceback.print_exc(file=sys.stdout)
                break
    else:
        for i in range(2, len(argv)):
            parse(argv[i])
        
    log.info('MM:00 INFO: BYE')


def parse (line):
    global cmdfuncs
    
    tokens = line.partition('#')[0].split()
    n = len(tokens)
    if n == 0:
        return
    cmd = tokens[0]
    del tokens[0]
    
    if cmd not in cmdfuncs:
        log.error('MM:00 ERROR: unknown command: ' + cmd)
    else:
        cmdfuncs[cmd](tokens)
        
    

# connect to the cmd interface or a host
# the host must be known
# if it defines cmdifc and cmdport, use them; else use defaults

def connect (host, why):    
    # should be either a listener host or a router host (edge-router)
    try:
        hostdata = hosts[host]
    except:
        if host not in bgprouters:
            log.error('MM:' + host + ' ERROR: ' + why + ': Unknown host: ' + host)
            return None    
    try:
        cmdifc = hostdata['cmdifc']
        cmdport = hostdata['cmdport']
    except:
        if platform.system() == 'Windows':
            cmdifc = '127.0.0.1'
            cmdport = base36(host)
        else:
            cmdifc = '/tmp/' + host
            cmdport = 0
    
    #print 'MM:' + host + ' INFO: ' + why + ': Connecting to ' + host + ' at ' + cmdifc + ':' + str(cmdport)

    try:
        if cmdifc.find('/') >= 0:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) # @UndefinedVariable
            s.connect(cmdifc)
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((cmdifc, cmdport))
    except Exception, e:
        log.error('MM:' + host + ' ERROR: ' + why + ': ' + repr(e))
        return None
    return s 
 

# grab any tnode queued data - this is usually just the result of tnode startup
    
def dump (args):
    for host in args:
        log.info('MM:' + host + ' DUMP')
        r = generic(host, 'DUMP', 'dump\n')
        if r is not None:
            if len(r) == 0:
                log.info('MM:' + host + ' output = <None>' + r.strip())
            else:
                log.info('MM:' + host + ' output = \n' + r.strip())


# force tnode to exit

def kill (host):
    log.info('MM:' + host + ' QUIT')
    r = generic(host, 'QUIT', 'quit\n')
    if r is not None:
        log.info('MM:' + host + ' output = ' + r.strip())


# terminate all listeners on a tnode, tnode does not exit

def reset (host):
    log.info('MM:' + host + ' RESET')
    r = generic(host, 'RESET', 'reset\n')
    if r is not None:
        log.info('MM:' + host + ' output = ' + r.strip())

# execute a command locally

def local (args):
    if len(args) < 1:
        log.error('MM:00 EXEC: ERROR usage: local cmd arg ...')
        return
    
    cmd = ''
    for arg in args:
        cmd += arg + ' '
    log.info('MM:00 LOCAL: ' + cmd)
    try:
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
    except Exception, e:
        out = ''
        err = 'Command Failed: ' + repr(e)
    r = out + err
    log.debug('MM:00 LOCAL: output = \n' + r.strip())
    

# execute a command remotely

def remote (args):
    if len(args) < 2:
        log.error('MM:00 EXEC: ERROR: usage: exec cmd arg ...')
        return
    host = args[0]
    del args[0]
    cmd = ''
    for arg in args:
        cmd += arg + ' '
    log.info('MM:' + host + ' REXEC: ' + cmd)
    r = generic(host, 'REXEC', 'exec ' + cmd + '\n')
    if r is not None:
        log.debug('MM:' + host + ' REXEC: output = \n' + r.strip())
        
        
# generic command interface to a tnode - send cmd, capture data
# return None id cannot connect or socket error
# return '' if no data

def generic (host, label, cmd):
    s = connect(host, label)
    if s == None:
        return None
    
    alldata = ''
    try:
        s.send(cmd)
        
        while True:
            data = s.recv(1024)
            if len(data) == 0:
                break
            alldata += data
            #sys.stdout.write(data)
        s.close()
    except Exception, e:
        log.error('MM:' + host + ' ERROR: ' + label + ': '+ repr(e))
        try:
            s.close()
        except:
            pass
        return None
    return alldata

 
# verify a transmission - tell source to send to dst IP addr.
# look for result from appropriate host and interface       
 
def verify (args):
    if len(args) != 3:
        log.error('MM:00 ERROR: VERIFY: usage: verify src dst port')
        return
    src = args[0]
    xdst = args[1]
    dport = args[2]   
    rand = str(random.randint(1000000000, 9999999999)) # must be 10 characters
    try:
        baddr, daddr = config.verifycheck(src, xdst, dport) 
    except Exception, e:                 
        log.error('MM:00 ERROR: VERIFY: ' + repr(e))
        return
            
    r = generic(src, 'VERIFY', 'test ' + rand + ' ' + baddr + ' ' + daddr + ' ' + str(dport) + '\n')
    if r is None:   # connection error
        return
    log.info('MM:' + src + ' VERIFY: ' + r.strip())
    
    if r.find("ERROR") >= 0:
        log.error('MM:' + src + ' ERROR: VERIFY: TEST FAILED ON SOURCE ' + r.strip())
        return
    
    for _ in range(5):
        result = generic(xdst, 'RESULT', 'result ' + rand + '\n')
        tokens = result.split()
        # possible return codes are:
        # COMPLETE - transfer is done
        # FAILURE - transfer is complete but a fault occurred
        # PENDING - transfer is still in progress
        # UNKNOWN - this host has no record of this transfer (misdirected)
        if result.find('COMPLETE') >= 0:
            log.info('MM:' + xdst + ' TEST PASSED ' + rand + ' ' + tokens[3] + ' ' + tokens[4] + ' ' + tokens[5])
            return
        if result.find('PENDING') >= 0:
            log.info('MM:' + xdst + ' TEST TRANSFER STILL IN PROGRESS ' + rand)
            time.sleep(1)
            continue
        if result.find('FAILURE') >= 0:
            log.error('MM:' + xdst + ' TEST FAILED - BAD RESULT (' + result + ')')
            return
        if result.find('UNKNOWN') >= 0:
            log.error('MM:' + xdst + ' TEST FAILED - DATA NOT FOUND ON EXPECTED HOST (' + xdst + ') - checking all hosts')
            for h in sorted(hosts):
                p = generic(h, 'RESULT', 'result ' + rand + '\n')
                if p.find('COMPLETE') >= 0:
                    log.error('MM:' + h + ' TEST MISDIRECTED ' + rand + ' to ' + p.strip())
                    return
            log.error('MM:' + h + ' TEST LOST ' + rand)
            return
    log.error('MM:' + xdst + ' TEST FAILED ' + rand + ' PENDING TOO LONG')

def send (args):
    if len(args) != 4:
        log.error('MM:00 SEND: ERROR usage: send source bind_addr dest_addr dest_port')
        return
    src = args[0]
    baddr = args[1]
    daddr = args[2]
    dport = args[3]
    if src not in hosts:
        log.error('MM:00 SEND: ERROR unknown src ' + src)
        return
    rand = str(random.randint(1000000000, 9999999999)) # must be 10 characters
    r = generic(src, 'TEST', 'test ' + rand + ' ' + baddr + ' ' + daddr + ' ' + str(dport) + '\n')
    if r is None:   # connection error
        return
    log.info('MM:' + src + ' SEND: ' + r.strip())
    
def comment (args):
    c = ''
    for arg in args:
        c += arg + ' '
    log.info('MM:00 COMMENT: ' + c)


# retrieve any pending or completed test results (does not consume result)

def pending (args):
    if len(args) == 0: # all hosts
        for host in hosts:
            r = generic(host, 'RESULT', 'result\n')
            if r is not None and len(r) > 0:
                log.info('MM:' + host + ' PENDING: ' + r.strip())
    else:
        for i in range(len(args)):
            host = args[i]
            r = generic(host, 'RESULT', 'result\n')
            if r is not None and len(r) > 0:
                log.info('MM:' + host + ' PENDING: ' + r.strip())

def test (args):
    if len(args) == 0:
        print json.dumps(tests, indent=4, sort_keys=True)
        # log.error('MM:00 ERROR: TEST: usage: test test_name ...')
        return
    for arg in args:
        if arg not in tests:
            log.error('MM:00 ERROR: TEST: undefined test: ' + arg)
            return
    for arg in args:
        log.info('MM:00 INFO: TEST: ' + arg)
        for l in tests[arg]:
            parse(l)
    
# start listeners on one or more hosts, one or more ports
#listener                         all hosts, all ports
#listener host                    this host, all ports
#listener host bind port port     this host, this bind, these ports  
def listener (args):
    if len(args) == 2:
        log.error('MM:00 ERROR: LISTENER: usage: listener [host [ bind_addr port port ... ] ]')
        return
    log.info('MM:00: LISTENER: Starting listeners')
    if len(args) == 0:
        for h in hosts:
            listener2(h)
        return
            
    if len(args) == 1:
        listener2(args[0])
        return
    
    for i in range(2, len(args)):
        listener3(args[0], args[1], args[i])
        
def listener2(host):
    if host not in hosts:
        log.error('MM:00 ERROR: LISTENER: unknown host: ' + host)
        return
    for p in hosts[host]['ports']:
        listener3(host, hosts[host]['bind'], p)
        
def listener3(host, bind, port):
    if host not in hosts:
        log.error('MM:00 ERROR: LISTENER: unknown host: ' + host)
        return
    #print 'listener ' + host + ' ' + bind + ' ' + port
    r = generic(host, 'LISTENER', 'listener ' + bind + ' ' + port + '\n')
    if r is not None and len(r) > 0:
        log.info('MM:' + host + ' LISTENER: ' + r.strip())
    

def delay (args):
    if len(args) == 1:
        try:
            log.info('MM:00: DELAY ' + args[0])
            time.sleep(float(args[0]))
        except Exception, e:
            log.error('MM:00 ERROR: DELAY: exception: ' + repr(e))
    else:
        log.error('MM:00 ERROR: DELAY: usage: delay seconds')
        
                
def show (args):
    global config
    print 'bgprouters'
    print json.dumps(config.bgprouters, indent=4, sort_keys=True) 
    print 'peers'
    print json.dumps(config.peers, indent=4, sort_keys=True) 
    print 'listeners'
    print json.dumps(config.listeners, indent=4, sort_keys=True) 
    print 'tests'
    print json.dumps(config.tests, indent=4, sort_keys=True) 
    print 'mode'
    print json.dumps(config.mode, indent=4, sort_keys=True) 
    print 'policies'
    print json.dumps(config.policies, indent=4, sort_keys=True) 
    print 'participants'
    print json.dumps(config.participants, indent=4, sort_keys=True)


# announce a route
def announce (args):
    if len(args) < 2:
        log.error('MM:XX' + ' ERROR: usage: announce bgp_router network ...')
        return
    host = args[0]
    del args[0]
    nets = ''
    for arg in args:
        nets += ' ' + arg
    if host not in bgprouters:
        log.error('MM:' + host + ' ERROR: ' + 'ANNOUNCE' + ' ' + host + ' : must be a BGP router')
    log.info('MM:' + host + ' ANNOUNCE: ' + nets)
    r = generic(host, 'ANNOUNCE', 'announce ' + nets + '\n')
    if r is not None and len(r) > 0:
        log.info('MM:' + host + ' ANNOUNCE: ' + r.strip())
    
 
# withdraw a route
def withdraw (args):
    if len(args) < 2:
        log.error('MM:XX' + ' ERROR: usage: withdraw bgp_router network ...')
        return
    host = args[0]
    del args[0]
    nets = ''
    for arg in args:
        nets += ' ' + arg
    if host not in bgprouters:
        log.error('MM:' + host + ' ERROR: ' + 'WITHDRAW' + ' ' + host + ' : must be a BGP router')
    log.info('MM:' + host + ' WITHDRAW: ' + nets)
    r = generic(host, 'WITHDRAW', 'withdraw ' + nets + '\n')
    if r is not None and len(r) > 0:
        log.info('MM:' + host + ' WITHDRAW: ' + r.strip())
        
# display bgp routes
def bgp (args):
    if len(args) != 1:
        log.error('MM:XX' + ' ERROR: usage: bgp bgp_router')
        return
    host = args[0]
    if host not in bgprouters:
        log.error('MM:' + host + ' ERROR: ' + 'BGP' + ' ' + host + ' : must be a BGP router')
    log.info('MM:' + host + ' BGP')
    r = generic(host, 'BGP', 'bgp\n')
    if r is not None and len(r) > 0:
        log.info('MM:' + host + ' BGP: ' + r.strip())
    
               
def terminate (args):
    log.info('MM:00 EXITING')
    os._exit(0)

def usage (args):
    print (
    'Usage:\n'     
    'listener anyhost bind port      # start a listener on the host to receive data\n'
    'test test_name test_name ...    # run the named sequence of commands\n'
    'verify host host port           # send data xmit request to source node and check expected destination\n'
    'announce bgprouter network ...  # advertise BGP route\n'
    'withdraw bgprouter network ...  # withdraw BGP route\n'
    'bgp bgprouter                   # show advertised bgp routes\n'
    'delay seconds                   # pause for things to settle\n'
    'exec anynode cmd arg arg        # execute cmd on node\n'
    'local cmd arg arg               # execute cmd on local machine\n'
    'pending anyhost                 # check if any pending or unclaimed data transfers are on host\n'
    'send host bind daddr port       # send data xmit request to source node\n'
    'comment commentary ...          # log a comment\n'
    'reset anynode                   # reset (close) listeners - takes a few seconds to take effect\n'
    'kill anynode                    # terminate a node, non recoverable\n'
    'dump anynode                    # dump any messages from a node - mainly to see if nodes are on-line\n'
    'config                          # print result of spec file parsing\n'
    'help                            # print this message\n'
    'quit                            # exit this manager; leave nodes intact\n'
    '\nWhere:\n'
    'host = a single specified host or bgprouter\n'
    'bgprouter = only a single bgp router node\n'
    'anynode = host | "hosts" | bgprouter | "bgprouters"\n'
    'anyhost = host | "hosts"\n'
    )

        
def base36(s):
    n = 0
    for c in string.lower(s):
        if c.isdigit():
            n = n * 36 + ord(c) - ord('0')
            continue
        if c.isalpha():
            n = n * 36 + ord(c) - ord('a') + 10
            continue
        n = n * 36 + 35  #treat everything else as a 'z'
    return n

        
if __name__ == "__main__":
    main(sys.argv)
