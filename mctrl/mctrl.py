#!/usr/bin/env python

import argparse
import os
import sys
import json

# Add iSDX folder to Python's system path
isdx_folder = "iSDX"
home = os.path.expanduser("~/")
isdx_path = home + isdx_folder
# isdx = os.path.dirname("/home/vagrant/iSDX/")
if isdx_path not in sys.path:
    sys.path.append(isdx_path)

import util.log
from monitor import Monitor
# Just in case of need in the future
from xctrl.client import RefMonClient # Socket
from lib import Config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dir', help='the directory of the example')
    args = parser.parse_args()

    # locate config file
    base_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),"..","examples",args.dir,"config"))
    config_file = os.path.join(base_path, "sdx_global.cfg")
    # locate the monitor's flows configuration file
    monitor_flows_file = os.path.join(base_path, "monitor_flows.cfg")
    config = Config(config_file)
    
    with file(monitor_flows_file) as f:
        flows = json.load(f)

    # start umbrella fabric manager
    logger = util.log.getLogger('monitor')
    logger.info('init')

    # Keep it for now just in case we decide to send messages to Refmon
    logger.info('REFMON client: ' + str(config.refmon["IP"]) + ' ' + str(config.refmon["Port"]))
    client = RefMonClient(config.refmon["IP"], config.refmon["Port"], config.refmon["key"])

    controller = Monitor(config, flows, client, logger)
    logger.info('start')
    controller.start()


if __name__ == '__main__':
    main()