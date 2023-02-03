from __future__ import print_function

import json
import logging
import re
import urllib
from collections import namedtuple
from string import Template

import requests
from frinx_conductor_workers import util
from frinx_conductor_workers.frinx_rest import additional_uniconfig_request_params
from frinx_conductor_workers.frinx_rest import conductor_headers
from frinx_conductor_workers.frinx_rest import conductor_url_base
from frinx_conductor_workers.frinx_rest import extract_uniconfig_cookies
from frinx_conductor_workers.frinx_rest import extract_uniconfig_cookies_multizone
from frinx_conductor_workers.frinx_rest import get_devices_by_uniconfig
from frinx_conductor_workers.frinx_rest import get_uniconfig_cluster_from_task
from frinx_conductor_workers.frinx_rest import parse_response

local_logs = logging.getLogger(__name__)

uniconfig_url_uniconfig_mount = (
    "$base_url/data/network-topology:network-topology/topology=uniconfig/node=$id"
)
uniconfig_url_uniconfig_commit = "$base_url/operations/uniconfig-manager:commit"
uniconfig_url_uniconfig_dryrun_commit = "$base_url/operations/dryrun-manager:dryrun-commit"
uniconfig_url_uniconfig_calculate_diff = "$base_url/operations/uniconfig-manager:calculate-diff"
uniconfig_url_uniconfig_sync_from_network = (
    "$base_url/operations/uniconfig-manager:sync-from-network"
)
uniconfig_url_uniconfig_replace_config_with_operational = (
    "$base_url/operations/uniconfig-manager:replace-config-with-operational"
)

uniconfig_url_uniconfig_tx_create = "$base_url/operations/uniconfig-manager:create-transaction"
uniconfig_url_uniconfig_tx_close = "$base_url/operations/uniconfig-manager:close-transaction"
uniconfig_url_uniconfig_tx_revert = "$base_url/operations/transaction-log:revert-changes"
uniconfig_url_uniconfig_tx_metadata = (
    "$base_url/data/transaction-log:transactions-metadata/transaction-metadata=$tx_id"
)


def apply_functions(uri):
    if not uri:
        return uri
    escape_regex = r"escape\(([^\)]*)\)"
    uri = re.sub(escape_regex, lambda match: urllib.parse.quote(match.group(1), safe=""), uri)
    return uri


def read_structured_data(task):
    """
    Build an url (id_url) from input parameters for getting configuration of mounted device
    by sending a GET request to Uniconfig. This tasks never fails, even if the data is not present,
    so it can be used as a check if the data is actually there.

    Args:
        task (dict) : input data ["device id", "uri", "uniconfig_context"]
            Device ID and URI are mandatory parameters.

    Returns:
        response_code (int) : HTTP status code of the GET operation
        response_body (dict) : JSON response from UniConfig
    """
    device_id = task["inputData"]["device_id"]
    uri = task["inputData"]["uri"]
    uri = apply_functions(uri)

    uniconfig_cookies = extract_uniconfig_cookies(task)

    id_url = (
        Template(uniconfig_url_uniconfig_mount).substitute(
            {"id": device_id, "base_url": get_uniconfig_cluster_from_task(task)}
        )
        + "/frinx-uniconfig-topology:configuration"
        + (uri if uri else "")
    )

    response = requests.get(
        id_url, cookies=uniconfig_cookies, **additional_uniconfig_request_params
    )
    response_code, response_json = parse_response(response)

    if response_code == 500:
        return {
            "status": "FAILED",
            "output": {
                "url": id_url,
                "response_code": response_code,
                "response_body": response_json,
            },
            "logs": ["Unable to read device with ID %s" % device_id],
        }
    else:
        return {
            "status": "COMPLETED",
            "output": {
                "url": id_url,
                "response_code": response_code,
                "response_body": response_json,
            },
            "logs": ["Node with ID %s read successfully" % device_id],
        }


def write_structured_data(task):
    """
    Build an url (id_url) from input parameters for writing configuration to a mounted device
    by sending a PUT request to Uniconfig.

    Args:
        task (dict) : input data ["device id", "uri", "template", "params", "uniconfig_context"]
            Device ID, URI and template are mandatory parameters.

    Returns:
        response_code (int) : HTTP status code of the GET operation
        response_body (dict) : JSON response from UniConfig
    """
    device_id = task["inputData"]["device_id"]
    method = task["inputData"].get("method", "PUT")
    uri = task["inputData"]["uri"]
    uri = apply_functions(uri)
    template = task["inputData"]["template"]
    params = task["inputData"]["params"]
    params = apply_functions(params)
    params = json.loads(params) if isinstance(params, str) else (params if params else {})

    uniconfig_cookies = extract_uniconfig_cookies(task)

    data_json = template if isinstance(template, str) else json.dumps(template if template else {})
    data_json = Template(data_json).substitute(params)

    id_url = (
        Template(uniconfig_url_uniconfig_mount).substitute(
            {"id": device_id, "base_url": get_uniconfig_cluster_from_task(task)}
        )
        + "/frinx-uniconfig-topology:configuration"
        + (uri if uri else "")
    )
    id_url = Template(id_url).substitute(params)

    response = requests.request(
        url=id_url,
        method=method,
        data=data_json,
        cookies=uniconfig_cookies,
        **additional_uniconfig_request_params,
    )

    response_code, response_json = parse_response(response)

    if response_code in [requests.codes.no_content, requests.codes.created, requests.codes.ok]:
        return {
            "status": "COMPLETED",
            "output": {
                "url": id_url,
                "response_code": response_code,
                "response_body": response_json,
            },
            "logs": ["Node with ID %s updated successfully" % device_id],
        }
    else:
        return {
            "status": "FAILED",
            "output": {
                "url": id_url,
                "response_code": response_code,
                "response_body": response_json,
            },
            "logs": ["Unable to update device with ID %s" % device_id],
        }


def delete_structured_data(task):
    device_id = task["inputData"]["device_id"]
    uri = task["inputData"]["uri"]
    uri = apply_functions(uri)

    uniconfig_cookies = extract_uniconfig_cookies(task)

    id_url = (
        Template(uniconfig_url_uniconfig_mount).substitute(
            {"id": device_id, "base_url": get_uniconfig_cluster_from_task(task)}
        )
        + "/frinx-uniconfig-topology:configuration"
        + (uri if uri else "")
    )

    r = requests.delete(id_url, cookies=uniconfig_cookies, **additional_uniconfig_request_params)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.no_content:
        return {
            "status": "COMPLETED",
            "output": {
                "url": id_url,
                "response_code": response_code,
                "response_body": response_json,
            },
            "logs": ["Node with ID %s updated successfully" % device_id],
        }
    else:
        return {
            "status": "FAILED",
            "output": {
                "url": id_url,
                "response_code": response_code,
                "response_body": response_json,
            },
            "logs": ["Unable to update device with ID %s" % device_id],
        }


def commit(task):
    """Function for assembling and issuing a commit request,
    even for multiple devices. Percolates the eventual commit
    error on southbound layers into response body."""
    uniconfig_cookies = extract_uniconfig_cookies_multizone(task)
    devices = parse_devices(task)
    devices_by_uniconfig = get_devices_by_uniconfig(devices, task, uniconfig_cookies)

    return commit_uniconfig(devices_by_uniconfig, uniconfig_url_uniconfig_commit, uniconfig_cookies)


def dryrun_commit(task):
    """Function for issuing a Uniconfig dry run commit request."""
    # Parse the input
    uniconfig_cookies = extract_uniconfig_cookies_multizone(task)
    devices = parse_devices(task)
    devices_by_uniconfig = get_devices_by_uniconfig(devices, task, uniconfig_cookies)

    return commit_uniconfig(
        devices_by_uniconfig, uniconfig_url_uniconfig_dryrun_commit, uniconfig_cookies
    )


def calc_diff(task):
    uniconfig_cookies = extract_uniconfig_cookies_multizone(task)
    devices = parse_devices(task)
    devices_by_uniconfig = get_devices_by_uniconfig(devices, task, uniconfig_cookies)

    return request_uniconfig(
        devices_by_uniconfig, uniconfig_url_uniconfig_calculate_diff, uniconfig_cookies
    )


def sync_from_network(task):
    uniconfig_cookies = extract_uniconfig_cookies_multizone(task)
    devices = parse_devices(task)
    devices_by_uniconfig = get_devices_by_uniconfig(devices, task, uniconfig_cookies)

    return request_uniconfig(
        devices_by_uniconfig, uniconfig_url_uniconfig_sync_from_network, uniconfig_cookies
    )


def replace_config_with_oper(task):
    uniconfig_cookies = extract_uniconfig_cookies_multizone(task)
    devices = parse_devices(task)
    devices_by_uniconfig = get_devices_by_uniconfig(devices, task, uniconfig_cookies)

    return request_uniconfig(
        devices_by_uniconfig,
        uniconfig_url_uniconfig_replace_config_with_operational,
        uniconfig_cookies,
    )


def create_commit_request(device_list):
    commit_body = {"input": {"target-nodes": {}}}
    commit_body["input"]["target-nodes"]["node"] = device_list
    return commit_body


def parse_devices(task, fail_on_empty=True):
    devices = task["inputData"].get("devices", [])
    if type(devices) is list:
        extracted_devices = []

        for dev in devices:
            if isinstance(dev, str):
                extracted_devices.append(dev)
            else:
                if "name" in dev:
                    extracted_devices.append(dev.get("name"))
    else:
        extracted_devices = (
            [x.strip() for x in devices.split(",") if x is not ""] if devices else []
        )

    if fail_on_empty and len(extracted_devices) is 0:
        raise Exception(
            "For Uniconfig RPCs, a list of devices needs to be specified. "
            "Global RPCs (involving all devices in topology) are not allowed for your own safety."
        )
    return extracted_devices


def request_uniconfig(devices, url, uniconfig_cookies_multizone={}):
    responses = []

    original_url = url
    for device in devices:
        url = Template(original_url).substitute({"base_url": device.uc_cluster})
        uniconfig_cookies = uniconfig_cookies_multizone.get(device.uc_cluster, {})
        tx_id = uniconfig_cookies.get("UNICONFIGTXID", "")

        r = requests.post(
            url,
            data=json.dumps(create_commit_request(device.device_names)),
            cookies=uniconfig_cookies,
            **additional_uniconfig_request_params,
        )

        response_code, response_json = parse_response(r)
        response = {
            "url": url,
            "UNICONFIGTXID": tx_id,
            "response_code": response_code,
            "response_body": response_json,
        }
        if (
            response_code == requests.codes.ok
            and response_json["output"]["overall-status"] == "complete"
        ):
            responses.append(response)
        else:
            return util.failed_response(response)

    return util.completed_response({"responses": responses})


def commit_uniconfig(devices, url, uniconfig_cookies_multizone={}):
    responses = []

    original_url = url
    for device in devices:
        url = Template(original_url).substitute({"base_url": device.uc_cluster})
        uniconfig_cookies = uniconfig_cookies_multizone.get(device.uc_cluster, {})
        tx_id = uniconfig_cookies.get("UNICONFIGTXID", "")

        r = requests.post(
            url,
            data=json.dumps(create_commit_request(device.device_names)),
            cookies=uniconfig_cookies,
            **additional_uniconfig_request_params,
        )
        response_code, response_body = parse_response(r)

        response = {
            "url": url,
            "UNICONFIGTXID": tx_id,
            "response_code": response_code,
            "response_body": response_body,
        }

        if (
            response_code == requests.codes.ok
            and response_body["output"]["overall-status"] == "complete"
        ):
            responses.append(response)

        else:
            # If there's error-message key in the the response body,
            # pass it to the user.
            error_messages = {}
            try:
                nodes = response_body["output"]["node-results"]["node-result"]

                for node in nodes:
                    if node.get("error-message"):
                        error_messages.update({node["node-id"]: node["error-message"]})

            except KeyError:
                error_messages["uncaught_error"] = response

            return util.failed_response(error_messages)

    return util.completed_response({"responses": responses})


def create_tx_multizone(task):
    devices = parse_devices(task, fail_on_empty=False)
    devices_by_uniconfig = get_devices_by_uniconfig(devices, task)

    uniconfig_cookies_multizone = {}

    for d in devices_by_uniconfig:
        response = create_tx_internal(uniconfig_cluster=d.uc_cluster)
        if response["status"] != util.COMPLETED_STATUS:
            # Failed to create some transaction, close already opened transactions
            for already_opened_tx_uc_cluster in uniconfig_cookies_multizone:
                # Best effort closing opened transactions
                # If unsuccessful, UC should clean them up eventually
                close_tx_internal(
                    uniconfig_cookies_multizone[already_opened_tx_uc_cluster],
                    already_opened_tx_uc_cluster,
                )

            # ... and return failed response
            return {
                "status": "FAILED",
                "output": {"failed_zone": d.uc_cluster, "response": response},
                "logs": [
                    f"""Unable to create multizone transactions. Failed for: '{d.uc_cluster}'. 
                                 Close sent to already opened transactions: '{uniconfig_cookies_multizone}'"""
                ],
            }
        else:
            uniconfig_cookies_multizone[d.uc_cluster] = response["output"]["uniconfig_cookies"]

    return {
        "status": "COMPLETED",
        "output": {"uniconfig_cookies_multizone": uniconfig_cookies_multizone},
        "logs": [
            f"""Transactions created successfully for: '{devices_by_uniconfig}' with context: '{uniconfig_cookies_multizone}'"""
        ],
    }


def create_tx_internal(uniconfig_cluster):
    id_url = Template(uniconfig_url_uniconfig_tx_create).substitute({"base_url": uniconfig_cluster})

    response = requests.post(id_url, **additional_uniconfig_request_params)

    if response.status_code == 201:
        tx_id = response.cookies.get("UNICONFIGTXID")
        server_id = response.cookies.get("uniconfig_server_id", "")

        context = {"uniconfig_cookies": {"UNICONFIGTXID": tx_id, "uniconfig_server_id": server_id}}

        return {"status": "COMPLETED", "output": context}

    response_body = response.content.decode("utf8")
    response_code = response.status_code

    return {
        "status": "FAILED",
        "output": {"response_body": response_body, "response_code": response_code},
    }


def close_tx_internal(uniconfig_cookies, uniconfig_cluster):
    tx_id = uniconfig_cookies["UNICONFIGTXID"]

    id_url = Template(uniconfig_url_uniconfig_tx_close).substitute({"base_url": uniconfig_cluster})
    response = requests.post(
        id_url, cookies=uniconfig_cookies, **additional_uniconfig_request_params
    )

    if response.status_code == 200:
        return {"status": "COMPLETED", "output": {"UNICONFIGTXID": tx_id}}

    response_body = response.content.decode("utf8")
    response_code = response.status_code

    return {
        "status": "FAILED",
        "output": {
            "UNICONFIGTXID": tx_id,
            "response_body": response_body,
            "response_code": response_code,
        },
    }


def close_tx_multizone(task):
    uniconfig_cookies_multizone = extract_uniconfig_cookies_multizone(task)
    close_tx_response = close_tx_multizone_internal(uniconfig_cookies_multizone)
    return {"status": "COMPLETED", "output": {"UNICONFIGTXID_multizone": close_tx_response}}


def close_tx_multizone_internal(uniconfig_cookies_multizone):
    close_tx_response = {}
    for uc_cluster in uniconfig_cookies_multizone:
        uniconfig_cookies = uniconfig_cookies_multizone[uc_cluster]
        tx_id = uniconfig_cookies["UNICONFIGTXID"]
        response = close_tx_internal(uniconfig_cookies, uc_cluster)

        close_tx_response[uc_cluster] = {"UNICONFIGTXID": tx_id, "status": response["status"]}
        if response["status"] != util.COMPLETED_STATUS:
            pass  # todo:?

    return close_tx_response


def find_started_tx(task):
    failed_wf = task["inputData"]["failed_wf_id"]

    r = requests.get(conductor_url_base + "/workflow/" + failed_wf, headers=conductor_headers)
    response_code, response_json = parse_response(r)

    if response_code != requests.codes.ok:
        return util.failed_response(
            {"failed_wf_id": failed_wf, "message": "Unable to get workflow"}
        )

    opened_contexts, committed_contexts = find_opened_contexts_in_wf(failed_wf, response_json)

    return util.completed_response(
        {"uniconfig_contexts": opened_contexts, "committed_contexts": committed_contexts}
    )


def find_opened_contexts_in_wf(failed_wf, response_json):
    opened_contexts = []
    committed_contexts = []
    for task in response_json.get("tasks", []):
        # If is a subworkflow task executing UC_TX_start
        if not task.get("inputData", {}).get("subWorkflowName", "") in ["UC_TX_start"]:
            continue
        # And contains started_by_wf equal to failed_wf
        if (
            task.get("outputData", {}).get("uniconfig_context", {}).get("started_by_wf")
            != failed_wf
        ):
            continue

        opened_contexts.append(task["outputData"]["uniconfig_context"])

    for task in response_json.get("tasks", []):
        # If is a subworkflow task executing UC_TX_commit
        if not task.get("inputData", {}).get("subWorkflowName", "") in [
            "UC_TX_commit",
            "Commit_w_decision",
        ]:
            continue
        # And contains started_by_wf equal to failed_wf
        if (
            task.get("outputData", {}).get("committed_current_context", {}).get("started_by_wf")
            != failed_wf
        ):
            continue

        committed_contexts.append(task["outputData"]["committed_current_context"])

    return opened_contexts, committed_contexts


def rollback_all_tx(task):
    ctxs = task["inputData"].get("uniconfig_contexts", [])
    committed_ctxs = task["inputData"].get("committed_contexts", [])

    # Reverse, in order to close / revert transactions in reverse order
    ctxs.reverse()

    for ctx_multizone in ctxs:
        if ctx_multizone in committed_ctxs:
            # Reverting committed
            # return_logs.info("Reverting committed transactions in context: %s", ctx_multizone)
            response = revert_tx_multizone(ctx_multizone["uniconfig_cookies_multizone"])
            if response["status"] != util.COMPLETED_STATUS:
                # Revert failed, stop and return error
                # return_logs.error(
                #     "Reverting transactions in context: '%s' FAILED. Stopping reverts. Response: '%s'",
                #     ctx_multizone,
                #     response,
                # )
                ctx_multizone["rollback_status"] = "revert " + util.FAILED_STATUS
                return util.failed_response(
                    {"failed_context": ctx_multizone, "uniconfig_contexts": ctxs}
                )
            else:
                ctx_multizone["rollback_status"] = "revert " + util.COMPLETED_STATUS
        else:
            # Closing uncommitted, consider all closes a success
            # return_logs.info("Closing transactions in context: '%s'", ctx_multizone)
            close_tx_multizone_internal(ctx_multizone["uniconfig_cookies_multizone"])
            ctx_multizone["rollback_status"] = "close " + util.COMPLETED_STATUS

    return util.completed_response({"uniconfig_contexts": ctxs})


def revert_tx_multizone(uniconfig_cookies_multizone):
    # return_logs.info("Reverting transactions in UCs on context: '%s'", uniconfig_cookies_multizone)

    close_tx_response = {}

    for uc_cluster in uniconfig_cookies_multizone:
        uniconfig_cookies = uniconfig_cookies_multizone[uc_cluster]
        tx_id = uniconfig_cookies["UNICONFIGTXID"]
        response = check_and_revert_tx(uniconfig_cookies, uc_cluster)

        close_tx_response[uc_cluster] = {"UNICONFIGTXID": tx_id, "status": response["status"]}

        if response["status"] != util.COMPLETED_STATUS:
            # Failing to revert is an error
            # return_logs.error(
            #     "Unable to revert multizone transactions for : '%s'. Response: '%s'",
            #     uc_cluster,
            #     response,
            # )
            return util.failed_response({"UNICONFIGTXID_multizone": close_tx_response})

    # return_logs.info(
    #     "Multizone transactions reverted successfully for: '%s'",
    #     [zone for zone in uniconfig_cookies_multizone],
    # )
    return util.completed_response({"UNICONFIGTXID_multizone": close_tx_response})


def check_and_revert_tx(uniconfig_cookies, uniconfig_cluster):
    tx_id_to_revert = uniconfig_cookies["UNICONFIGTXID"]
    # return_logs.info(
    #     "Reverting transaction in UC: '%s' on a single context: '%s'",
    #     uniconfig_cluster,
    #     uniconfig_cookies,
    # )

    # 1. Create transaction to do the revert
    response = create_tx_internal(uniconfig_cluster)
    if response["status"] != util.COMPLETED_STATUS:
        # If we cannot create a dedicated transaction to perform rollback, we need to return error
        # return_logs.error(
        #     "Unable to revert transaction: '%s', Cannot create a revert transaction, response '%s'",
        #     tx_id_to_revert,
        #     response,
        # )
        return util.failed_response(
            {"UNICONFIGTXID": tx_id_to_revert, "create_tx_response": response}
        )

    uniconfig_cookies_for_revert = response["output"]["uniconfig_cookies"]
    # return_logs.info(
    #     "Reverting '%s', step 1: Using a dedicated transaction to perform revert: '%s'",
    #     tx_id_to_revert,
    #     uniconfig_cookies_for_revert,
    # )

    # Check transaction log for failed transaction
    id_url = Template(uniconfig_url_uniconfig_tx_metadata).substitute(
        {"base_url": uniconfig_cluster, "tx_id": tx_id_to_revert}
    )
    response = requests.get(
        id_url, cookies=uniconfig_cookies_for_revert, **additional_uniconfig_request_params
    )

    if response.status_code == requests.codes.not_found:
        # Transaction rollback can be skipped, there are no changes in that TX
        # return_logs.info(
        #     "Reverting '%s', step 2: Cannot found in transacton log. It was probably canceled or committed empty. Skipping.",
        #     tx_id_to_revert,
        # )
        # Close the new tx where rollback should be performed
        # return_logs.info(
        #     "Closing dedicated transaction to perform revert. Not needed: '%s'",
        #     uniconfig_cookies_for_revert,
        # )
        close_tx_internal(uniconfig_cookies_for_revert, uniconfig_cluster)

        return util.completed_response({"UNICONFIGTXID": tx_id_to_revert})
    elif response.status_code == requests.codes.ok:
        # return_logs.info("Reverting '%s', step 2: Transaction log found", tx_id_to_revert)
        pass  # todo:?
    else:
        # Transaction will still be attempted, even though we cannot find its log due to unexpected error
        # return_logs.warning(
        #     "Reverting '%s', step 2: cannot found in transaction log. Unexpected error retrieving log,"
        #     " status code: '%s', response body '%s'. Will attempt revert anyway.",
        #     tx_id_to_revert,
        #     response.content.decode("utf8"),
        #     response.status_code,
        # )
        pass  # todo:?

    # 2. Do the revert
    response = revert_tx_internal(uniconfig_cluster, tx_id_to_revert, uniconfig_cookies_for_revert)
    if response["status"] != util.COMPLETED_STATUS:
        # If we cannot revert the transaction, we need to return error
        # return_logs.error(
        #     "Unable to revert transaction: '%s', Revert RPC failed, response '%s'",
        #     tx_id_to_revert,
        #     response,
        # )
        return util.failed_response(
            {"UNICONFIGTXID": tx_id_to_revert, "create_tx_response": response}
        )

    # return_logs.info("Reverting '%s', step 3: Revert RPC successful.", tx_id_to_revert)

    # 3. Commit reverted changes
    device_with_cluster = namedtuple("devices", ["uc_cluster", "device_names"])
    response = commit_uniconfig(
        [device_with_cluster(uc_cluster=uniconfig_cluster, device_names=[])],
        uniconfig_url_uniconfig_commit,
        {uniconfig_cluster: uniconfig_cookies_for_revert},
    )

    if response["status"] != util.COMPLETED_STATUS:
        # If we cannot commit the revert, we need to return error
        # return_logs.error(
        #     "Unable to revert transaction: '%s', Cannot commit transaction with revert, response '%s'",
        #     tx_id_to_revert,
        #     response,
        # )
        return util.failed_response({"UNICONFIGTXID": tx_id_to_revert, "commit_response": response})

    # return_logs.info("Reverting '%s', step 4: Commit RPC successful.", tx_id_to_revert)

    # return_logs.info("Transaction '%s' reverted successfully", tx_id_to_revert)
    return util.completed_response({"UNICONFIGTXID": tx_id_to_revert})


def revert_tx_internal(uniconfig_cluster, tx_id, uniconfig_cookies):
    id_url = Template(uniconfig_url_uniconfig_tx_revert).substitute({"base_url": uniconfig_cluster})
    # return_logs.info("Reverting URL %s", id_url)
    response = requests.post(
        id_url,
        cookies=uniconfig_cookies,
        data=json.dumps(
            {
                "input": {
                    "ignore-non-existing-nodes": True,
                    "target-transactions": {"transaction": [tx_id]},
                }
            }
        ),
        **additional_uniconfig_request_params,
    )

    if response.status_code != requests.codes.ok:
        response_body = response.content.decode("utf8")
        response_code = response.status_code
        # return_logs.error(
        #     "Unable to revert transaction: '%s', response code: '%s' and response: '%s'",
        #     tx_id,
        #     response_code,
        #     response_body,
        # )
        return util.failed_response(
            {"UNICONFIGTXID": tx_id, "response_body": response_body, "response_code": response_code}
        )

    # return_logs.info("Revert RPC called successfully for transaction: '%s'", tx_id)
    return util.completed_response({"UNICONFIGTXID": tx_id})


def start(cc):
    local_logs.info("Starting Uniconfig workers")

    cc.register(
        "UNICONFIG_read_structured_device_data",
        {
            "description": '{"description": "Read device configuration or operational data in structured format e.g. openconfig", "labels": ["BASICS","UNICONFIG","OPENCONFIG"]}',
            "inputKeys": ["device_id", "uri", "uniconfig_context"],
            "outputKeys": ["url", "response_code", "response_body"],
        },
        read_structured_data,
    )

    cc.register(
        "UNICONFIG_write_structured_device_data",
        {
            "description": '{"description": "Write device configuration data in structured format e.g. openconfig", "labels": ["BASICS","UNICONFIG"]}',
            "inputKeys": ["device_id", "uri", "template", "params", "uniconfig_context"],
            "outputKeys": ["url", "response_code", "response_body"],
        },
        write_structured_data,
    )

    cc.register(
        "UNICONFIG_delete_structured_device_data",
        {
            "description": '{"description": "Delete device configuration data in structured format e.g. openconfig", "labels": ["BASICS","UNICONFIG","OPENCONFIG"]}',
            "inputKeys": ["device_id", "uri", "uniconfig_context"],
            "outputKeys": ["url", "response_code", "response_body"],
        },
        delete_structured_data,
    )

    cc.register(
        "UNICONFIG_commit",
        {
            "description": '{"description": "Commit uniconfig", "labels": ["BASICS","UNICONFIG"]}',
            "inputKeys": ["devices", "uniconfig_context"],
            "outputKeys": ["url", "response_code", "response_body"],
            "timeoutSeconds": 600,
            "responseTimeoutSeconds": 600,
        },
        commit,
    )

    cc.register(
        "UNICONFIG_dryrun_commit",
        {
            "description": '{"description": "Dryrun Commit uniconfig", "labels": ["BASICS","UNICONFIG"]}',
            "inputKeys": ["devices", "uniconfig_context"],
            "outputKeys": ["url", "response_code", "response_body"],
            "timeoutSeconds": 600,
            "responseTimeoutSeconds": 600,
        },
        dryrun_commit,
    )

    cc.register(
        "UNICONFIG_calculate_diff",
        {
            "description": '{"description": "Calculate uniconfig diff", "labels": ["BASICS","UNICONFIG"]}',
            "inputKeys": ["devices", "uniconfig_context"],
            "outputKeys": ["url", "response_code", "response_body"],
            "timeoutSeconds": 600,
            "responseTimeoutSeconds": 600,
        },
        calc_diff,
    )

    cc.register(
        "UNICONFIG_sync_from_network",
        {
            "description": '{"description": "Sync uniconfig from network", "labels": ["BASICS","UNICONFIG"]}',
            "inputKeys": ["devices", "uniconfig_context"],
            "outputKeys": ["responses"],
            "timeoutSeconds": 600,
            "responseTimeoutSeconds": 600,
        },
        sync_from_network,
    )

    cc.register(
        "UNICONFIG_replace_config_with_oper",
        {
            "description": '{"description": "Replace config with oper in uniconfig", "labels": ["BASICS","UNICONFIG"]}',
            "inputKeys": ["devices", "uniconfig_context"],
            "outputKeys": ["responses"],
            "timeoutSeconds": 600,
            "responseTimeoutSeconds": 600,
        },
        replace_config_with_oper,
    )

    cc.register(
        "UNICONFIG_tx_find_started",
        {
            "description": '{"description": "Find all started UC transaction in a failed workflow", "labels": ["BASICS","UNICONFIG", "TX"]}',
            "inputKeys": ["failed_wf_id"],
            "outputKeys": ["uniconfig_contexts"],
        },
        find_started_tx,
    )

    cc.register(
        "UNICONFIG_tx_rollback",
        {
            "description": '{"description": "Rollback all tx from uniconfig_contexts", "labels": ["BASICS","UNICONFIG", "TX"]}',
            "inputKeys": ["uniconfig_contexts"],
            "outputKeys": [],
        },
        rollback_all_tx,
    )

    cc.register(
        "UNICONFIG_tx_create_multizone",
        {
            "description": '{"description": "Create a dedicated multizone transaction(s)", "labels": ["BASICS","UNICONFIG", "TX"]}',
            "inputKeys": ["devices"],
            "outputKeys": ["uniconfig_cookies_multizone"],
        },
        create_tx_multizone,
    )

    cc.register(
        "UNICONFIG_tx_close_multizone",
        {
            "description": '{"description": "Close a dedicated multizone transaction(s)", "labels": ["BASICS","UNICONFIG", "TX"]}',
            "inputKeys": ["uniconfig_context"],
            "outputKeys": ["UNICONFIGTXID_multizone"],
        },
        close_tx_multizone,
    )
