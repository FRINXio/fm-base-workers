from __future__ import print_function

import json
import logging
import re
import urllib
import requests

from string import Template
from frinx_conductor_workers.frinx_rest import uniconfig_url_base, parse_response, add_uniconfig_tx_cookie, \
    additional_uniconfig_request_params

local_logs = logging.getLogger(__name__)

uniconfig_url_uniconfig_mount = uniconfig_url_base + "/data/network-topology:network-topology/topology=uniconfig/node=$id"
uniconfig_url_uniconfig_commit = uniconfig_url_base + "/operations/uniconfig-manager:commit"
uniconfig_url_uniconfig_dryrun_commit = uniconfig_url_base + "/operations/dryrun-manager:dryrun-commit"
uniconfig_url_uniconfig_calculate_diff = uniconfig_url_base + "/operations/uniconfig-manager:calculate-diff"
uniconfig_url_uniconfig_sync_from_network = uniconfig_url_base + "/operations/uniconfig-manager:sync-from-network"
uniconfig_url_uniconfig_replace_config_with_operational = uniconfig_url_base + "/operations/uniconfig-manager:replace-config-with-operational"
uniconfig_url_show_connection_status = uniconfig_url_base + "/operations/uniconfig-manager:show-connection-status"


def apply_functions(uri):
    if not uri:
        return uri
    escape_regex = r"escape\(([^\)]*)\)"
    uri = re.sub(escape_regex, lambda match: urllib.parse.quote(match.group(1), safe=''), uri)
    return uri


def read_structured_data(task):
    """
    Build an url (id_url) from input parameters for getting configuration of mounted device
    by sending a GET request to Uniconfig. This tasks never fails, even if the data is not present,
    so it can be used as a check if the data is actually there.

    Args:
        task (dict) : input data ["device id", "uri", "uniconfig_tx_id"]
            Device ID and URI are mandatory parameters.

    Returns:
        response_code (int) : HTTP status code of the GET operation
        response_body (dict) : JSON response from UniConfig
    """
    device_id = task["inputData"]["device_id"]
    uri = task["inputData"]["uri"]
    uri = apply_functions(uri)
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""

    id_url = Template(uniconfig_url_uniconfig_mount).substitute(
        {"id": device_id}
    ) + "/frinx-uniconfig-topology:configuration" + (uri if uri else "")

    response = requests.get(id_url, headers=add_uniconfig_tx_cookie(uniconfig_tx_id),
                            **additional_uniconfig_request_params)
    response_code, response_json = parse_response(response)

    if response_code == 500:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to read device with ID %s" % device_id]}
    else:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Node with ID %s read successfully" % device_id]}


def write_structured_data(task):
    """
    Build an url (id_url) from input parameters for writing configuration to a mounted device
    by sending a PUT request to Uniconfig.

    Args:
        task (dict) : input data ["device id", "uri", "template", "params", "uniconfig_tx_id"]
            Device ID, URI and template are mandatory parameters.

    Returns:
        response_code (int) : HTTP status code of the GET operation
        response_body (dict) : JSON response from UniConfig
    """
    device_id = task["inputData"]["device_id"]
    uri = task["inputData"]["uri"]
    uri = apply_functions(uri)
    template = task["inputData"]["template"]
    params = task["inputData"]["params"]
    params = apply_functions(params)
    params = json.loads(params) if isinstance(params, str) else (params if params else {})
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""

    data_json = template if isinstance(template, str) else json.dumps(template if template else {})
    data_json = Template(data_json).substitute(params)

    id_url = Template(uniconfig_url_uniconfig_mount).substitute(
        {"id": device_id}
    ) + "/frinx-uniconfig-topology:configuration" + (uri if uri else "")
    id_url = Template(id_url).substitute(params)

    response = requests.put(id_url, data=data_json, headers=add_uniconfig_tx_cookie(uniconfig_tx_id),
                            **additional_uniconfig_request_params)
    response_code, response_json = parse_response(response)

    if response_code == requests.codes.no_content or response_code == requests.codes.created:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Node with ID %s updated successfully" % device_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to update device with ID %s" % device_id]}


def delete_structured_data(task):
    device_id = task['inputData']['device_id']
    uri = task['inputData']['uri']
    uri = apply_functions(uri)
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task[
        'inputData'] else ""

    id_url = Template(uniconfig_url_uniconfig_mount).substitute(
        {"id": device_id}
    ) + "/frinx-uniconfig-topology:configuration" + (uri if uri else "")

    r = requests.delete(id_url, headers=add_uniconfig_tx_cookie(uniconfig_tx_id),
                        **additional_uniconfig_request_params)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.no_content:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Node with ID %s updated successfully" % device_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to update device with ID %s" % device_id]}


def commit(task):
    """Function for assembling and issuing a commit request,
    even for multiple devices. Percolates the eventual commit
    error on southbound layers into response body."""

    # Parse the input
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""
    r = requests.post(
        uniconfig_url_uniconfig_commit,
        data=json.dumps(create_commit_request(task)),
        headers=add_uniconfig_tx_cookie(uniconfig_tx_id),
        **additional_uniconfig_request_params
    )
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["overall-status"] == "complete":
        return {'status': 'COMPLETED', 'output': {'url': uniconfig_url_uniconfig_commit,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Uniconfig commit successfully"]}
    else:
        return {'status': 'FAILED', 'output': {'url': uniconfig_url_uniconfig_commit,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable commit failed"]}


def dryrun_commit(task):
    """ Function for issuing a Uniconfig dry run commit request."""
    # Parse the input
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""

    r = requests.post(uniconfig_url_uniconfig_dryrun_commit,
                      data=json.dumps(create_commit_request(task)),
                      headers=add_uniconfig_tx_cookie(uniconfig_tx_id),
                      **additional_uniconfig_request_params)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["overall-status"] == "complete":
        return {'status': 'COMPLETED', 'output': {'url': uniconfig_url_uniconfig_dryrun_commit,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Uniconfig dryrun commit successfull"]}
    else:
        return {'status': 'FAILED', 'output': {'url': uniconfig_url_uniconfig_dryrun_commit,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Uniconfig dryrun commit failed"]}


def calc_diff(task):
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""
    r = requests.post(uniconfig_url_uniconfig_calculate_diff,
                      data=json.dumps(create_commit_request(task)),
                      headers=add_uniconfig_tx_cookie(uniconfig_tx_id),
                      **additional_uniconfig_request_params)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["overall-status"] == "complete":
        return {'status': 'COMPLETED', 'output': {'url': uniconfig_url_uniconfig_calculate_diff,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Uniconfig calculate diff successfull"]}
    else:
        return {'status': 'FAILED', 'output': {'url': uniconfig_url_uniconfig_calculate_diff,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Uniconfig calculate diff failed"]}


def sync_from_network(task):
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""
    r = requests.post(uniconfig_url_uniconfig_sync_from_network,
                      data=json.dumps(create_commit_request(task)),
                      headers=add_uniconfig_tx_cookie(uniconfig_tx_id),
                      **additional_uniconfig_request_params)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["overall-status"] == "complete":
        return {'status': 'COMPLETED', 'output': {'url': uniconfig_url_uniconfig_sync_from_network,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Uniconfig sync successfull"]}
    else:
        return {'status': 'FAILED', 'output': {'url': uniconfig_url_uniconfig_sync_from_network,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Uniconfig sync failed"]}


def replace_config_with_oper(task):
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""
    r = requests.post(uniconfig_url_uniconfig_replace_config_with_operational,
                      data=json.dumps(create_commit_request(task)),
                      headers=add_uniconfig_tx_cookie(uniconfig_tx_id),
                      **additional_uniconfig_request_params)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["overall-status"] == "complete":
        return {'status': 'COMPLETED', 'output': {'url': uniconfig_url_uniconfig_replace_config_with_operational,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Uniconfig replace successfull"]}
    else:
        return {'status': 'FAILED', 'output': {'url': uniconfig_url_uniconfig_replace_config_with_operational,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Uniconfig replace failed"]}


def create_commit_request(task):
    commit_body = {
        "input": {
            "target-nodes": {
            }
        }
    }
    device_list = parse_devices(task)
    if device_list:
        commit_body["input"]["target-nodes"]["node"] = device_list

    return commit_body


def parse_devices(task):
    devices = task['inputData'].get('devices', [])
    if type(devices) is list:
        extracted_devices = devices
    else:
        extracted_devices = [x.strip() for x in devices.split(",") if x is not ""] if devices else []

    if len(extracted_devices) is 0:
        raise Exception("For Uniconfig RPCs, a list of devices needs to be specified. "
                        "Global RPCs (involving all devices in topology) are not allowed for your own safety.")
    return extracted_devices


def start(cc):
    local_logs.info("Starting Uniconfig workers")

    cc.register('UNICONFIG_read_structured_device_data', {
        "description": '{"description": "Read device configuration or operational data in structured format e.g. openconfig", "labels": ["BASICS","UNICONFIG","OPENCONFIG"]}',
        "inputKeys": [
            "device_id",
            "uri",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ]
    }, read_structured_data)

    cc.register('UNICONFIG_write_structured_device_data', {
        "description": '{"description": "Write device configuration data in structured format e.g. openconfig", "labels": ["BASICS","UNICONFIG"]}',
        "inputKeys": [
            "device_id",
            "uri",
            "template",
            "params",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ]
    }, write_structured_data)

    cc.register('UNICONFIG_delete_structured_device_data', {
        "description": '{"description": "Delete device configuration data in structured format e.g. openconfig", "labels": ["BASICS","UNICONFIG","OPENCONFIG"]}',
        "inputKeys": [
            "device_id",
            "uri",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ]
    }, delete_structured_data)

    cc.register('UNICONFIG_commit', {
        "description": '{"description": "Commit uniconfig", "labels": ["BASICS","UNICONFIG"]}',
        "inputKeys": [
            "devices",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ],
        "timeoutSeconds": 600,
        "responseTimeoutSeconds": 600,
    }, commit)

    cc.register('UNICONFIG_dryrun_commit', {
        "description": '{"description": "Dryrun Commit uniconfig", "labels": ["BASICS","UNICONFIG"]}',
        "inputKeys": [
            "devices",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ],
        "timeoutSeconds": 600,
        "responseTimeoutSeconds": 600,
    }, dryrun_commit)

    cc.register('UNICONFIG_calculate_diff', {
        "description": '{"description": "Calculate uniconfig diff", "labels": ["BASICS","UNICONFIG"]}',
        "inputKeys": [
            "devices",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ],
        "timeoutSeconds": 600,
        "responseTimeoutSeconds": 600,
    }, calc_diff)

    cc.register('UNICONFIG_sync_from_network', {
        "description": '{"description": "Sync uniconfig from network", "labels": ["BASICS","UNICONFIG"]}',
        "inputKeys": [
            "devices",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "responses",
        ],
        "timeoutSeconds": 600,
        "responseTimeoutSeconds": 600,
    }, sync_from_network)

    cc.register('UNICONFIG_replace_config_with_oper', {
        "description": '{"description": "Replace config with oper in uniconfig", "labels": ["BASICS","UNICONFIG"]}',
        "inputKeys": [
            "devices",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "responses"
        ],
        "timeoutSeconds": 600,
        "responseTimeoutSeconds": 600,
    }, replace_config_with_oper)
