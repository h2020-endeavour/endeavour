#!/usr/bin/env python

import os
import sys


isdx_folder = "iSDX"
home = os.path.expanduser("~/")
isdx_path = home + isdx_folder
if isdx_path not in sys.path:
    sys.path.append(isdx_path)
import util.log

from flowpusher import FlowPusher
from rest import MonitorApp 

class Monitor(object):
    
    def __init__(self, config, flows, sender, logger, **kwargs):
        self.logger = logger
        self.sender = sender
        self.config = config
        table_id = None
        try:
            table_id =  config.tables['monitor']
        except KeyError, e:
            print "Monitoring table does not exists in the sdx_global.cfg file! - Add a table named %s." % str(e) 
        # refmon IP is the address of the controller
        # For now, port is static 8080
        controller = config.refmon["IP"] + ":8080"
        self.flow_pusher = FlowPusher(flows, table_id, controller)

    def start(self):
        # Push initial monitoring flows
        self.flow_pusher.push_flows()
        # Start REST 
        mon = MonitorApp(self)
        mon.app.run()


