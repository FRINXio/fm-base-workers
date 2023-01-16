from __future__ import print_function

import json
import logging
from distutils import util as util
from string import Template

import requests
from frinx_conductor_workers.frinx_rest import additional_uniconfig_request_params
from frinx_conductor_workers.frinx_rest import get_uniconfig_cluster_from_task
from frinx_conductor_workers.frinx_rest import parse_response

local_logs = logging.getLogger(__name__)

uniconfig_url_install_nodes = "$base_url/operations/connection-manager:install-multiple-nodes"
uniconfig_url_uninstall_nodes = "$base_url/operations/connection-manager:uninstall-multiple-nodes"


def execute_install_nodes(task):
    install_body = (
        task["inputData"]["install_body"]
        if type(task["inputData"]["install_body"]) is str
        else json.dumps(task["inputData"]["install_body"])
    )

    try:
        status_condition = bool(util.strtobool(task["inputData"]["fail_if_not_installed"]))
    except Exception as e:
        local_logs.error(e)
        status_condition = True

    id_url = Template(uniconfig_url_install_nodes).substitute(
        {"base_url": get_uniconfig_cluster_from_task(task)}
    )

    r = requests.post(
        id_url,
        data=install_body,
        timeout=task["responseTimeoutSeconds"],
        **additional_uniconfig_request_params,
    )

    response_code, response_json = parse_response(r)

    if response_code is 200:
        status = "COMPLETED"

        for node in response_json["output"]["node-results"]:
            if status_condition and node["status"] == "fail":
                status = "FAILED"
                break

        return {
            "status": status,
            "output": {
                "url": uniconfig_url_install_nodes,
                "response_code": response_code,
                "response_body": response_json,
            },
            "logs": [],
        }
    else:
        return {
            "status": "FAILED",
            "output": {
                "url": uniconfig_url_install_nodes,
                "response_code": response_code,
                "response_body": response_json,
            },
            "logs": [],
        }


def execute_uninstall_nodes(task):
    uninstall_body = (
        task["inputData"]["uninstall_body"]
        if type(task["inputData"]["uninstall_body"]) is str
        else json.dumps(task["inputData"]["uninstall_body"])
    )

    try:
        status_condition = bool(util.strtobool(task["inputData"]["fail_if_not_uninstalled"]))
    except Exception as e:
        local_logs.error(e)
        status_condition = True

    id_url = Template(uniconfig_url_uninstall_nodes).substitute(
        {"base_url": get_uniconfig_cluster_from_task(task)}
    )

    r = requests.post(
        id_url,
        data=uninstall_body,
        timeout=task["responseTimeoutSeconds"],
        **additional_uniconfig_request_params,
    )

    response_code, response_json = parse_response(r)

    if response_code is 200:
        status = "COMPLETED"

        for node in response_json["output"]["node-results"]:
            if status_condition and node["status"] == "fail":
                status = "FAILED"
                break

        return {
            "status": status,
            "output": {
                "url": uniconfig_url_uninstall_nodes,
                "response_code": response_code,
                "response_body": response_json,
            },
            "logs": [],
        }
    else:
        return {
            "status": "FAILED",
            "output": {
                "url": uniconfig_url_uninstall_nodes,
                "response_code": response_code,
                "response_body": response_json,
            },
            "logs": [],
        }


def start(cc):
    local_logs.info("Starting Connection-Manager workers")

    cc.register(
        "CONNECTION_install_node",
        {
            "description": '{"description": "Install multiple devices in parallel", "labels": ["BASICS","UNICONFIG"]}',
            "timeoutSeconds": 3600,
            "responseTimeoutSeconds": 3600,
            "inputKeys": ["install_body", "fail_if_not_installed"],
            "outputKeys": ["url", "response_code", "response_body"],
        },
        execute_install_nodes,
    )

    cc.register(
        "CONNECTION_uninstall_node",
        {
            "description": '{"description": "Uninstall multiple devices in parallel", "labels": ["BASICS","UNICONFIG"]}',
            "timeoutSeconds": 3600,
            "responseTimeoutSeconds": 3600,
            "inputKeys": ["uninstall_body", "fail_if_not_uninstalled"],
            "outputKeys": ["url", "response_code", "response_body"],
        },
        execute_uninstall_nodes,
    )
