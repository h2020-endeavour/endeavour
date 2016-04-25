#!/usr/bin/env python

import argparse
import os
import sys

# Add iSDX folder to Python's system path
isdx_folder = "iSDX"
home = os.path.expanduser("~/")
isdx_path = home + isdx_folder
# isdx = os.path.dirname("/home/vagrant/iSDX/")
if isdx_path not in sys.path:
    sys.path.append(isdx_path)

import util.log
from xctrl.flowmodmsg import FlowModMsgBuilder
from xctrl.client import RefMonClient # Socket
from umbrella import Umbrella
from lib import Config
from load_balancer import Dummy_LBalancer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='path of config file')
    args = parser.parse_args()

    # locate config file
    config_file = os.path.abspath(args.config)

    config = Config(config_file)

    # start umbrella fabric manager
    logger = util.log.getLogger('uctrl')
    logger.info('init')

    logger.info('REFMON client: ' + str(config.refmon["IP"]) + ' ' + str(config.refmon["Port"]))
    client = RefMonClient(config.refmon["IP"], config.refmon["Port"], config.refmon["key"])

    controller = Umbrella(config, client, logger, Dummy_LBalancer())
    logger.info('start')
    controller.start()

if __name__ == '__main__':
    main()