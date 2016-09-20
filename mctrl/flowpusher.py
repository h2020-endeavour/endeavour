import logging
import json
import urllib2
import argparse
import os
import sys
import time

# For the Ryu API to add a flow entry:
# http://ryu.readthedocs.io/en/latest/app/ofctl_rest.html#add-a-flow-entry

class FlowPusher(object):
    def __init__(self, flows, table_id, controller):
        self.flows = flows
        self.table_id = table_id
        self.url = 'http://' + controller + '/stats/flowentry/add'

    def set_table_id(self, flow):
        flow["table_id"] = self.table_id

    def set_goto_action(self, flow):
        # Send to the next table of the pipeline
        flow["actions"] = [{"type":"GOTO_TABLE", "table_id":self.table_id + 1}]
    def push_flows(self):
        for flow in self.flows["flows"]:
            dps = flow["dpids"]
            flow["dpid"] = flow.pop("dpids")
            self.set_table_id(flow)
            self.set_goto_action(flow)
            for dp in dps:
                flow["dpid"] = dp
                try:
                    req = urllib2.Request(self.url)
                    req.add_header('Content-Type', 'application/json')
                    urllib2.urlopen(req, str(flow))
                except urllib2.HTTPError as err:
                    #TODO handle error codes
                    print err.code