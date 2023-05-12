import json
import re
import urllib
from collections import namedtuple
from string import Template

import frinx.common.frinx_rest
import requests
from frinx.common.frinx_rest import uniconfig_headers
from frinx.common.frinx_rest import uniconfig_url_base
from frinx.common.util import parse_response
from frinx.services.uniconfig.models import *
from frinx.services.uniconfig.templates import UNICONFIGTXID
from frinx.services.uniconfig.templates import uniconfig_url_uniconfig_tx_close
from frinx.services.uniconfig.templates import uniconfig_url_uniconfig_tx_create


def request(method, url, cookies=None, data=None, timeout=60) -> UniconfigRpcResponse:
    print(method, url, cookies)
    response = requests.request(
        method=method, url=url, cookies=cookies, data=data, timeout=timeout, headers=uniconfig_headers
    )

    code, data = parse_response(response)
    response_cookies = parse_response_cookies(response)

    return UniconfigRpcResponse(code=code, data=data, cookies=response_cookies)


def parse_response_cookies(response: requests.Response) -> TransactionMeta | None:
    uniconfig_cookies = None

    if response.cookies is not None:
        tx_id = response.cookies.get(UNICONFIGTXID) or None
        server_id = response.cookies.get("uniconfig_server_id", "") or None

        uniconfig_cookies = TransactionMeta(uniconfig_server_id=server_id, UNICONFIGTXID=tx_id)
    return uniconfig_cookies


def apply_functions(uri: str) -> str:
    if not uri:
        return uri
    escape_regex = r"escape\(([^\)]*)\)"
    uri = re.sub(escape_regex, lambda match: urllib.parse.quote(match.group(1), safe=""), uri)
    return uri


def extract_uniconfig_cookies(
    uniconfig_context: UniconfigContext | UniconfigTransactionList,
) -> UniconfigCookies:
    uniconfig_cookies_multizone = extract_uniconfig_cookies_multizone(uniconfig_context)
    cluster_for_device = get_uniconfig_cluster_from_task()
    return uniconfig_cookies_multizone.get(cluster_for_device, {}) or {}


def extract_uniconfig_cookies_multizone(
    uniconfig_context: UniconfigContext | dict | str,
) -> UniconfigCookiesMultizone:
    """

    Returns:
        object:
    """
    match uniconfig_context:
        case dict():
            return UniconfigCookiesMultizone(
                uniconfig_context.get("uniconfig_cookies_multizone", {}) or {}
            )
        case UniconfigContext():
            return uniconfig_context.dict().get("uniconfig_cookies_multizone", {}) or {}
        case str():
            return json.loads(uniconfig_context).dict().get("uniconfig_cookies_multizone", {}) or {}
        case _:
            return UniconfigCookiesMultizone()


def get_uniconfig_cluster_from_task() -> str:
    # TODO Is that single node???
    return uniconfig_url_base


def get_devices_by_uniconfig(devices):
    device_with_cluster = namedtuple("devices", ["uc_cluster", "device_names"])

    return [device_with_cluster(uc_cluster=uniconfig_url_base, device_names=devices)]


def parse_devices(devices=None, fail_on_empty=True) -> list[object]:
    if devices is None:
        devices = []
    if type(devices) is list:
        extracted_devices = []

        for dev in devices:
            if isinstance(dev, str):
                extracted_devices.append(dev)
            else:
                if "name" in dev:
                    extracted_devices.append(dev.get("name"))
    else:
        extracted_devices = [x.strip() for x in devices.split(",") if x != ""] if devices else []

    if fail_on_empty and len(extracted_devices) == 0:
        raise Exception(
            "For Uniconfig RPCs, a list of devices needs to be specified. "
            "Global RPCs (involving all devices in topology) are not allowed for your own safety."
        )
    return extracted_devices


def create_request(device_list: list) -> dict:
    commit_body = {"input": {"target-nodes": {}}}
    commit_body["input"]["target-nodes"]["node"] = device_list
    return commit_body


def create_commit_request(device_list: list) -> dict:
    commit_body = {"input": {"target-nodes": {}}}
    commit_body["input"]["target-nodes"]["node"] = device_list
    return commit_body


def commit_uniconfig(
    devices: list[ClusterWithDevices],
    url: Template,
    uniconfig_cookies_multizone: UniconfigCookies | UniconfigCookiesMultizone,
) -> UniconfigOutput:
    responses = []
    original_url = url

    for device in devices:
        url = original_url.substitute({"base_url": device.uc_cluster})
        uniconfig_cookies = uniconfig_cookies_multizone.get(device.uc_cluster, {})
        tx_id = uniconfig_cookies.get(UNICONFIGTXID, "")
        data = create_request(device.device_names)

        response = request("POST", url, data=data, cookies=uniconfig_cookies)

        match response.code:
            case requests.codes.ok:
                if response.data["output"]["overall-status"] == "complete":
                    responses.append(
                        {
                            "url": str(url),
                            "UNICONFIGTXID": tx_id,
                            "response_code": response.code,
                            "response_body": response.data,
                        }
                    )
            case _:
                error_messages = {}
                try:
                    nodes = response.data["output"]["node-results"]["node-result"]

                    for node in nodes:
                        if node.get("error-message"):
                            error_messages.update({node["node-id"]: node["error-message"]})

                except KeyError:
                    error_messages["uncaught_error"] = response

                return response

    return UniconfigOutput(code=requests.codes.ok, data={"responses": responses})


def request_uniconfig(
    devices: list[ClusterWithDevices], url: Template, uniconfig_cookies_multizone: UniconfigCookies
) -> UniconfigOutput:
    responses = []

    original_url = url
    for device in devices:
        url = original_url.substitute({"base_url": device.uc_cluster})
        uniconfig_cookies = uniconfig_cookies_multizone.get(device.uc_cluster, {})
        tx_id = uniconfig_cookies.get("UNICONFIGTXID", "")
        data = create_commit_request(device.device_names)

        response = request("POST", url, data=json.dumps(data), cookies=uniconfig_cookies)

        match response.code:
            case requests.codes.ok:
                if response.data["output"]["overall-status"] == "complete":
                    responses.append(
                        {
                            "url": str(url),
                            "UNICONFIGTXID": tx_id,
                            "response_code": response.code,
                            "response_body": response.data,
                        }
                    )
            case _:
                return response

    return UniconfigOutput(code=requests.codes.ok, data={"responses": responses})


def create_tx_internal(uniconfig_cluster: str) -> UniconfigOutput:
    id_url = uniconfig_url_uniconfig_tx_create.substitute({"base_url": uniconfig_cluster})

    response = request("POST", id_url, cookies=None)
    match response.code:
        case requests.codes.created:
            return UniconfigOutput(
                code=response.code, data=UniconfigCookies(uniconfig_cookies=response.cookies).dict()
            )

    return UniconfigOutput(code=response.code, data=response.data)


def close_tx_internal(uniconfig_cookies: TransactionMeta, uniconfig_cluster) -> UniconfigOutput:
    tx_id = uniconfig_cookies.transaction_id

    id_url = uniconfig_url_uniconfig_tx_close.substitute({"base_url": uniconfig_cluster})
    response = request("POST", id_url, cookies=uniconfig_cookies.dict())
    match response.code:
        case requests.codes.ok:
            return UniconfigOutput(code=response.code, data={"UNICONFIGTXID": tx_id})

    return UniconfigOutput(
        code=response.code,
        data={
            "UNICONFIGTXID": tx_id,
            "response_body": response.data,
            "response_code": response.code,
        },
    )


def close_tx_multizone_internal(uniconfig_cookies_multizone: UniconfigCookiesMultizone):
    close_tx_response = {}
    response_code = 200
    for uc_cluster in uniconfig_cookies_multizone:
        uniconfig_cookies = TransactionMeta(**dict(uniconfig_cookies_multizone.get(uc_cluster)))
        tx_id = uniconfig_cookies.transaction_id
        response = close_tx_internal(uniconfig_cookies, uc_cluster)

        close_tx_response[uc_cluster] = {"UNICONFIGTXID": tx_id, "status": response.code}

        match response.code:
            case 404 | 500 | 400:
                response_code = response.code  # todo:?

    return UniconfigOutput(code=response_code, data=close_tx_response)


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


# TODO finalize
# def revert_tx_multizone(uniconfig_cookies_multizone):
#     # return_logs.info("Reverting transactions in UCs on context: '%s'", uniconfig_cookies_multizone)
#
#     close_tx_response = {}
#
#     for uc_cluster in uniconfig_cookies_multizone:
#         uniconfig_cookies = uniconfig_cookies_multizone[uc_cluster]
#         tx_id = uniconfig_cookies["UNICONFIGTXID"]
#         response = check_and_revert_tx(uniconfig_cookies, uc_cluster)
#
#         close_tx_response[uc_cluster] = {"UNICONFIGTXID": tx_id, "status": response["status"]}
#
#         if response["status"] != util.COMPLETED_STATUS:
#             # Failing to revert is an error
#             # return_logs.error(
#             #     "Unable to revert multizone transactions for : '%s'. Response: '%s'",
#             #     uc_cluster,
#             #     response,
#             # )
#             return util.failed_response({"UNICONFIGTXID_multizone": close_tx_response})
#
#     # return_logs.info(
#     #     "Multizone transactions reverted successfully for: '%s'",
#     #     [zone for zone in uniconfig_cookies_multizone],
#     # )
#     return util.completed_response({"UNICONFIGTXID_multizone": close_tx_response})
