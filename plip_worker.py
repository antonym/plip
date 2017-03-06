#!/usr/bin/env python
from hotqueue import HotQueue
import requests


import config


queue = HotQueue('ecopoiesis')

auth_headers = {
    'X-Auth-User': config.craton_creds['username'],
    'X-Auth-Token': config.craton_creds['password'],
    'X-Auth-Project': config.craton_creds['project']
}


@queue.worker
def consume_queue(message):
    print "Consumed message: %s" % message
    r = requests.put(message['url'],
                     params=message['payload'],
                     headers=auth_headers)
    print(r.text)


consume_queue()
