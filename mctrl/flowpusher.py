import logging
import json
import urllib2
import argparse
import os
import sys

# For the Ryu API to add a flow entry:
# http://ryu.readthedocs.io/en/latest/app/ofctl_rest.html#add-a-flow-entry

CONTROLLER = 'localhost:8080'

class FlowPusher(object):
    def __init__(self, flows, table_id, controller):
        self.flows = flows
        self.table_id = table_id
        url = 'http://' + controller + '/stats/flowentry/add'
        self.req = urllib2.Request(url)
        self.req.add_header('Content-Type', 'application/json')

    def set_table_id(self, flow):
        flow["table_id"] = self.table_id

    def set_goto_action(self, flow):
        # Send to the next table of the pipeline
        flow["actions"] = [{"type":"GOTO_TABLE", "table_id":self.table_id + 1}]
    def push_flows(self):
        for f in self.flows["flows"]:
            self.set_table_id(f)
            self.set_goto_action(f)
            print f
            try:
                urllib2.urlopen(self.req, str(f))
            except urllib2.HTTPError as err:
                #TODO handle error codes
                print err.code