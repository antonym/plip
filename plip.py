#!/usr/bin/env python
from flask import Flask, render_template, make_response, request, abort
from flask import jsonify
import json
import logging
import os
import requests
from time import gmtime, strftime


import config


app = Flask(__name__)

# NOTE(major): Change to the directory of plip.py (this script) so that we
# can write to the static_pxe relative path.
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# Set up our logger
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

# Set craton url
craton_url = config.craton_url


def auth_headers():
    """
    Assembles authentication headers for Craton calls.
    """
    headers = {
        'X-Auth-User': config.craton_creds['username'],
        'X-Auth-Token': config.craton_creds['password'],
        'X-Auth-Project': config.craton_creds['project']
    }
    return headers


def indenter(text_to_indent):
    """
    Transforms the indented json.dumps() output into a commented form to go
    into the iPXE script.  This would have been less hackish if the textwrap
    module in Python 2.7 wasn't so awful.
    """
    temp = ""
    for line in json.dumps(text_to_indent, indent=2).split('\n'):
        temp = temp + "#   %s\n" % line
    return temp.strip()


def get_server_by_number(host_id):
    """
    Retrieves information about a server from Craton in json format.

    Return json if successful, False if unsuccessful.
    """

    url = '%s/hosts/%s' % (craton_url, host_id)
    r = requests.get(url, headers=auth_headers())
    if r.status_code == requests.codes.ok:
        return r.json()
    else:
        return r.status_code


def get_server_by_mac(mac_address):
    """
    Retrieves information about a server from Craton in json format.

    Return json if successful, False if unsuccessful.
    """

    url = '%s/hosts?vars=macs[*]:"%s"&details=all' % (craton_url, mac_address)

    r = requests.get(url, headers=auth_headers())
    if r.status_code == requests.codes.ok:
        return r.json()
    else:
        return r.status_code


def get_server_by_switch(switch_name, switch_port):
    """
    Retrieves information about a server from Craton in json format.
      - switch_name: ex. servers-lab-1.sat6
      - switch port: ex. Ethernet1/6 

    Return json if successful, False if unsuccessful.
    """

    url = ('%s/hosts?details=all&vars=lldp.*.chassis.name:"%s",' +
           'lldp.*.port.ifname:"%s"') % (craton_url, switch_name,
                                         switch_port)

    r = requests.get(url, headers=auth_headers())
    if r.status_code == requests.codes.ok:
        return r.json()
    else:
        return r.status_code


def update_boot_status(host_id, boot_status):
    """
    Changes the ecopoiesis_boot_status to another value to change boot
    behavior.

    Returns response from Craton in json format.
    """
    boot_status_string = "%s" % (boot_status)

    payload = {
        'ecopoiesis_boot_status': boot_status
    }

    url = '%s/hosts/%s/variables' % (craton_url, host_id)
    logging.info("Updating ecopoiesis_boot_status: %s" % payload)
    r = requests.put(url, json=payload, headers=auth_headers())
    if r.status_code == requests.codes.ok:
        return r.json()
    else:
        return r.status_code


@app.route("/")
def present_form():
    """
    If no URI is specified, we provide the user with a form that they can use
    to bring up data about a particular server.
    """
    return render_template('base.html')


@app.route("/pxe")
@app.route("/pxe/configs/<config_file>")
def get_pxe_script(config_file=None):
    """
    Takes a request and returns an iPXE script based on data pulled live from
    Craton or a cached script.  The switch_name and switch_port are required
    parameters and should be pulled from LLDP data.

    By default, plip will not display raw data from Craton (debug=no).
    Use debug=yes to force plip to display the raw data in the iPXE script
    in commented lines at the end of the script.
    """
    logging.info("Request to /pxe with params: %s" % dict(request.args))

    if config_file is None:
        template = 'plip.ipxe'
    else:
        template = 'configs/' + config_file

    if 'number' in request.args:
        host_id = request.args.get('number')
        server_data = get_server_by_number(host_id)
    elif 'mac' in request.args:
        mac = request.args.get('mac')
        mac_address = mac.replace("-", ":")
        server_data = get_server_by_mac(mac_address)['hosts'][0]
    else:
        # Get the switch data and strip it
        switch_name = request.args.get('switch_name')
        switch_port = request.args.get('switch_port')

        # Get the Craton data for this switch name/port combo
        server_data = get_server_by_switch(switch_name,
                                           switch_port)

        server_data = server_data['hosts'][0]

    # Create a timestamp for the PXE script output
    timestamp = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

    # If the call to craton failed, server_data should contain the
    # response code from craton as an integer.  If so, let's abort with
    # that response code.
    if isinstance(server_data, int):
        abort(server_data)

    server_data_dump = indenter(server_data)    # For debugging
    ecopoiesis_host_ip = config.ecopoiesis_host_ip

    # Generate PXE script
    pxedata = render_template(template,
                              server_data=server_data,
                              server_data_dump=server_data_dump,
                              request=request,
                              ecopoiesis_host_ip=ecopoiesis_host_ip,
                              timestamp=timestamp)

    r = make_response(pxedata)
    r.mimetype = "text/plain"

    return r


@app.route("/update")
@app.route("/update/status")
def set_boot_status():
    # Get the server number and status from request
    host_id = request.args.get('host_id')
    boot_status = request.args.get('boot_status')

    if host_id is None or boot_status is None:
        abort(412)

    if boot_status not in ("localboot", "netboot"):
        abort(412)

    response = update_boot_status(host_id, boot_status)

    return jsonify(response)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
