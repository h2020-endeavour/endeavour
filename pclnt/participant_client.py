#!/usr/bin/env python
#  Author:
#  Florian Kaufmann (DE-CIX)

import argparse
import atexit
import json
import os
from multiprocessing.connection import Client
from signal import signal, SIGTERM
from sys import exit
from threading import Thread
# location pctrl/lib.py
import sys
sys.path.append('/home/vagrant/iSDX/pctrl')
from lib import PConfig
import util.log

''' client for participants to send policy updates '''
class ParticipantClient(object):
    
    def __init__(self, id, config_file, logger):
        # participant id
        self.id = id

        # used to signal termination
        self.run = True

        # Initialize participant params and logger
        self.cfg = PConfig(config_file, self.id)
        self.logger = logger

    def file_handler(self, policy_file, id_list):    
        add_policy = []
        # Open File and Parse
        with open(policy_file, 'r') as f:
            policies=json.load(f)
            
            for policy in policies['inbound']:
                if policy['cookie'] in id_list:
                    add_policy.append(policy)


        data = {}
        data['inbound'] = add_policy
        return [data]

        

    def process_handler(self, policy_file, action, id_list):
        # Connect to participant client
        self.client = self.cfg.get_participant_client(self.id, self.logger)
        # Get data from file
        data = {}
        policies = {}
        policies[action] = self.file_handler(policy_file,id_list)
        data['policy'] = [policies]
        
        # Send data
        self.logger.debug("participant_client(%s): send: %s" % (self.id, data))
        self.client.send(data)


    def stop(self):
        # Stop participant client
        self.logger.debug("participant_client(%s): close connection"  % self.id)
        self.run = False


''' participant client useage: participant_client.py policy_file participant_id insert/remove '''
def main():
    # Set valid actions
    valid_actions = {"remove", "insert"}

    # Parse arugments
    parser = argparse.ArgumentParser()
    parser.add_argument('policy_file', help='the policy change file')
    parser.add_argument('id', type=int, help='participant id (integer)')
    parser.add_argument('action', type=str, choices=valid_actions, help='use remove or insert')
    parser.add_argument('id_list', type=str, nargs='?', help='list of rule ids/cookies')
    args = parser.parse_args()

    # locate policy changefile
    base_path = os.path.abspath(os.path.join(os.path.realpath(args.policy_file), ".."))
    policy_file = os.path.join(base_path, args.policy_file)

    # locate config file
    base_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(args.policy_file)), "..", "config"))
    config_file = os.path.join(base_path, "sdx_global.cfg")

    # logger
    logger = util.log.getLogger("P_" + str(args.id))
    logger.debug ("Starting participant_client(%s) with config file: %s" % (args.id, config_file))

    # start controller
    prtclnt = ParticipantClient(args.id, config_file, logger)
    prtclnt_thread = Thread(target=prtclnt.process_handler(policy_file, args.action, args.id_list.split(',')))
    prtclnt_thread.daemon = True
    prtclnt_thread.start()

    atexit.register(prtclnt.stop)
    signal(SIGTERM, lambda signum, stack_frame: exit(1))

    while prtclnt_thread.is_alive():
        try:
            prtclnt_thread.join(1)
        except KeyboardInterrupt:
            prtclnt.stop()

    logger.debug ("participant_client(%s): extiting" % args.id)
    print ("done")


if __name__ == '__main__':
    main()