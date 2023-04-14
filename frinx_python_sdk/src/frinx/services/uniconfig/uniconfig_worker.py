import json
from string import Template

import requests
from frinx.common.frinx_rest import conductor_headers
from frinx.common.frinx_rest import conductor_url_base
from frinx.services.uniconfig import templates
from frinx.services.uniconfig import utils as uniconfig_utils
from frinx.services.uniconfig.models import UniconfigContext
from frinx.services.uniconfig.models import UniconfigCookiesMultizone
from frinx.services.uniconfig.models import UniconfigOutput
from frinx.services.uniconfig.models import UniconfigTransactionList
from frinx.services.uniconfig.utils import request as uniconfig_request


def read_structured_data(
    device_id: str, uri: str, uniconfig_context: UniconfigContext
) -> UniconfigOutput:
    """
    Build an url (id_url) from input parameters for getting configuration of mounted device
    by sending a GET request to Uniconfig. This tasks never fails, even if the data is not present,
    so it can be used as a check if the data is actually there.

    Args:
        device_id: str
        uri: str
        uniconfig_context: UniconfigContext

        Device ID and URI are mandatory parameters.

    Returns:
        UniconfigOutput:
            code (int) : HTTP status code of the GET operation
            data (dict) : JSON response from UniConfig
            url (str): Request URL
    """
    # try:
    if len(device_id) == 0:
        raise Exception("Missing input device_id")
    if not isinstance(device_id, str):
        raise Exception("Bad input device_id")
    if uri is None:
        raise Exception("Missing input uri")
    if not isinstance(uri, str):
        raise Exception("Bad input uri")

    if uniconfig_context is None or uniconfig_context == "":
        uniconfig_context = UniconfigContext()
    if isinstance(uniconfig_context, str):
        uniconfig_context = UniconfigContext(**json.loads(uniconfig_context))
    if isinstance(uniconfig_context, dict):
        uniconfig_context = UniconfigContext(**uniconfig_context)
    if not isinstance(uniconfig_context, UniconfigContext):
        raise Exception("Bad input uniconfig_context")

    print(type(uniconfig_context), uniconfig_context.dict())
    uri = uniconfig_utils.apply_functions(uri)
    uniconfig_cookies = uniconfig_utils.extract_uniconfig_cookies(uniconfig_context)

    id_url = (
        templates.uniconfig_url_uniconfig_mount.substitute(
            {"id": device_id, "base_url": uniconfig_utils.get_uniconfig_cluster_from_task()}
        )
        + "/frinx-uniconfig-topology:configuration"
        + (uri if uri else "")
    )
    response = uniconfig_utils.request(method="GET", url=id_url, cookies=uniconfig_cookies)
    return UniconfigOutput(code=response.code, data=response.data, url=id_url)
    # except Exception as e:
    #     # TODO status code check
    #     return UniconfigOutput(
    #         data={ "error":e }, logs="Unable to read device with ID %s" % device_id, code=500
    #     )


def write_structured_data(
    device_id: str,
    uri: str,
    template: str | dict,
    params,
    uniconfig_context: UniconfigContext,
    method="PUT",
) -> UniconfigOutput:
    """
    Build an url (id_url) from input parameters for writing configuration to a mounted device
    by sending a PUT request to Uniconfig.

    Args:
        device_id: str
        uri: str
        template: str|dict
        params: dict
        uniconfig_context: UniconfigContext
        method: str

    Returns:
        UniconfigOutput:
            code (int) : HTTP status code of the GET operation
            data (dict) : JSON response from UniConfig
            url (str): Request URL
    """
    # TODO valid method input?
    try:
        if len(device_id) == 0:
            raise Exception("Missing input device_id")
        if not isinstance(device_id, str):
            raise Exception("Bad input device_id")
        if uri is None:
            raise Exception("Missing input uri")
        if not isinstance(uri, str):
            raise Exception("Bad input uri")
        if len(template) == 0:
            raise Exception("Missing input template")
        if not isinstance(template, dict | str):
            raise Exception("Bad input template")

        if uniconfig_context is None or uniconfig_context == "":
            uniconfig_context = UniconfigContext()
        if isinstance(uniconfig_context, str):
            uniconfig_context = UniconfigContext(**json.loads(uniconfig_context))
        if isinstance(uniconfig_context, dict):
            uniconfig_context = UniconfigContext(**uniconfig_context)
        if not isinstance(uniconfig_context, UniconfigContext):
            raise Exception("Bad input uniconfig_context")

        uri = uniconfig_utils.apply_functions(uri)
        params = uniconfig_utils.apply_functions(params)
        params = json.loads(params) if isinstance(params, str) else (params if params else {})
        uniconfig_cookies = uniconfig_utils.extract_uniconfig_cookies(uniconfig_context)
        data_json = (
            template if isinstance(template, str) else json.dumps(template if template else {})
        )
        data_json = Template(data_json).substitute(params)

        id_url = (
            templates.uniconfig_url_uniconfig_mount.substitute(
                {"id": device_id, "base_url": uniconfig_utils.get_uniconfig_cluster_from_task()}
            )
            + "/frinx-uniconfig-topology:configuration"
            + (uri if uri else "")
        )

        id_url = Template(id_url).substitute(params)
        response = uniconfig_utils.request(
            method=method, url=id_url, data=data_json, cookies=uniconfig_cookies
        )
        return UniconfigOutput(code=response.code, data=response.data, url=id_url)
    except Exception as error:
        # TODO status code check
        return UniconfigOutput(
            data={"error": error}, logs=f"Unable to update device with ID {device_id}", code=500
        )


def delete_structured_data(
    device_id: str, uri: str, uniconfig_context: UniconfigContext
) -> UniconfigOutput:
    """
    Build an url (id_url) from input parameters for removing configuration of mounted device
    by sending a DELETE request to Uniconfig.

    Args:
        device_id: str
        uri: str
        uniconfig_context: UniconfigContext

        Device ID and URI are mandatory parameters.

    Returns:
        UniconfigOutput:
            code (int) : HTTP status code of the GET operation
            data (dict) : JSON response from UniConfig
            url (str): Request URL
    """
    try:
        if len(device_id) == 0:
            raise Exception("Missing input device_id")
        if not isinstance(device_id, str):
            raise Exception("Bad input device_id")
        if uri is None:
            raise Exception("Missing input uri")
        if not isinstance(uri, str):
            raise Exception("Bad input uri")

        uri = uniconfig_utils.apply_functions(uri)
        uniconfig_cookies = uniconfig_utils.extract_uniconfig_cookies(uniconfig_context)

        id_url = (
            templates.uniconfig_url_uniconfig_mount.substitute(
                {"id": device_id, "base_url": uniconfig_utils.get_uniconfig_cluster_from_task()}
            )
            + "/frinx-uniconfig-topology:configuration"
            + (uri if uri else "")
        )
        response = uniconfig_utils.request(method="DELETE", url=id_url, cookies=uniconfig_cookies)
        return UniconfigOutput(code=response.code, data=response.data, url=id_url)
    except Exception as error:
        # TODO status code check
        return UniconfigOutput(
            data={"error": error}, logs=f"Unable to update device with ID {device_id}", code=500
        )


def commit(devices: list[object], uniconfig_context: UniconfigContext) -> UniconfigOutput:
    """Function for assembling and issuing a commit request, even for multiple devices.
    Percolates the eventual commit error on southbound layers into response body.

    Args:
        devices: list[object]
        uniconfig_context: UniconfigContext

        Device ID and URI are mandatory parameters.

    Returns:
        UniconfigOutput:
            code (int) : HTTP status code of the GET operation
            data (dict) : JSON response from UniConfig
            url (str): Request URL
    """

    if isinstance(uniconfig_context, str):
        uniconfig_context = json.loads(uniconfig_context)
    uniconfig_cookies = uniconfig_utils.extract_uniconfig_cookies_multizone(uniconfig_context)
    devices = uniconfig_utils.parse_devices(devices)
    devices_by_uniconfig = uniconfig_utils.get_devices_by_uniconfig(devices)

    return uniconfig_utils.commit_uniconfig(
        devices_by_uniconfig, templates.uniconfig_url_uniconfig_commit, uniconfig_cookies
    )


def dryrun_commit(devices: list[object], uniconfig_context: UniconfigContext) -> UniconfigOutput:
    """Function for issuing an Uniconfig dry run commit request, even for multiple devices.
    Percolates the eventual commit error on southbound layers into response body.

    Args:
        devices: list[object]
        uniconfig_context: UniconfigContext

        Device ID and URI are mandatory parameters.

    Returns:
        UniconfigOutput:
            code (int) : HTTP status code of the GET operation
            data (dict) : JSON response from UniConfig
            url (str): Request URL
    """

    if isinstance(uniconfig_context, str):
        uniconfig_context = json.loads(uniconfig_context)
    uniconfig_cookies = uniconfig_utils.extract_uniconfig_cookies(uniconfig_context)
    devices = uniconfig_utils.parse_devices(devices)
    devices_by_uniconfig = uniconfig_utils.get_devices_by_uniconfig(devices)

    return uniconfig_utils.commit_uniconfig(
        devices_by_uniconfig, templates.uniconfig_url_uniconfig_dryrun_commit, uniconfig_cookies
    )


def calc_diff(devices: list, uniconfig_context: UniconfigTransactionList) -> UniconfigOutput:
    """Function for calculating diff, even for multiple devices.

    Args:
        devices: list
        uniconfig_context: UniconfigTransactionList

        Device ID and URI are mandatory parameters.

    Returns:
        UniconfigOutput:
            code (int) : HTTP status code of the GET operation
            data (dict) : JSON response from UniConfig
            url (str): Request URL
    """

    if uniconfig_context is None or uniconfig_context == "":
        uniconfig_context = UniconfigTransactionList()
    if isinstance(uniconfig_context, str):
        uniconfig_context = UniconfigTransactionList(uniconfig_context=uniconfig_context)
    if not isinstance(uniconfig_context, UniconfigTransactionList):
        raise Exception("Bad input uniconfig_context")

    print(uniconfig_context)

    uniconfig_cookies = uniconfig_utils.extract_uniconfig_cookies(uniconfig_context)
    devices = uniconfig_utils.parse_devices(devices)
    devices_by_uniconfig = uniconfig_utils.get_devices_by_uniconfig(devices)

    return uniconfig_utils.request_uniconfig(
        devices_by_uniconfig, templates.uniconfig_url_uniconfig_calculate_diff, uniconfig_cookies
    )


def sync_from_network(
    devices: list[object], uniconfig_context: UniconfigTransactionList
) -> UniconfigOutput:
    """Function for sync from network, even for multiple devices.

    Args:
        devices: list[object]
        uniconfig_context: UniconfigTransactionList

        Device ID and URI are mandatory parameters.

    Returns:
        UniconfigOutput:
            code (int) : HTTP status code of the GET operation
            data (dict) : JSON response from UniConfig
            url (str): Request URL
    """

    if uniconfig_context is None or uniconfig_context == "":
        uniconfig_context = UniconfigTransactionList()
    if isinstance(uniconfig_context, str):
        uniconfig_context = UniconfigTransactionList(uniconfig_context=uniconfig_context)
    if not isinstance(uniconfig_context, UniconfigTransactionList):
        raise Exception("Bad input uniconfig_context")

    uniconfig_cookies = uniconfig_utils.extract_uniconfig_cookies(uniconfig_context)
    devices = uniconfig_utils.parse_devices(devices)
    devices_by_uniconfig = uniconfig_utils.get_devices_by_uniconfig(devices)

    return uniconfig_utils.request_uniconfig(
        devices_by_uniconfig, templates.uniconfig_url_uniconfig_sync_from_network, uniconfig_cookies
    )


def replace_config_with_oper(
    devices: list[object], uniconfig_context: UniconfigTransactionList
) -> UniconfigOutput:
    """Function for replace config data with operational data, even for multiple devices.

    Args:
        devices: list[object]
        uniconfig_context: UniconfigTransactionList

        Device ID and URI are mandatory parameters.

    Returns:
        UniconfigOutput:
            code (int) : HTTP status code of the GET operation
            data (dict) : JSON response from UniConfig
            url (str): Request URL
    """

    if uniconfig_context is None or uniconfig_context == "":
        uniconfig_context = UniconfigTransactionList()
    if isinstance(uniconfig_context, str):
        uniconfig_context = UniconfigTransactionList(uniconfig_context=uniconfig_context)
    if not isinstance(uniconfig_context, UniconfigTransactionList):
        raise Exception("Bad input uniconfig_context")

    uniconfig_cookies = uniconfig_utils.extract_uniconfig_cookies(uniconfig_context)
    devices = uniconfig_utils.parse_devices(devices)
    devices_by_uniconfig = uniconfig_utils.get_devices_by_uniconfig(devices)

    return uniconfig_utils.request_uniconfig(
        devices_by_uniconfig,
        templates.uniconfig_url_uniconfig_replace_config_with_operational,
        uniconfig_cookies,
    )


def create_tx_multizone(devices: list[str], oam_domain=None) -> UniconfigOutput:
    """
    Args:
        devices:
        oam_domain:

    Expected output:
    {
        "uniconfig_cookies_multizone": {
            "http://unistore:8181/rests": {
                "UNICONFIGTXID": "a1cbb742-3108-4170-8a71-6f8590c7bee0",
                "uniconfig_server_id": "a857f8b8af540aa4"
            }
        }
    }

    Task input example:
    {
        "oam_domain": "",
        "devices": "IOS01"
    }
    """

    devices = uniconfig_utils.parse_devices(devices, fail_on_empty=False)
    devices_by_uniconfig = uniconfig_utils.get_devices_by_uniconfig(devices)

    uniconfig_cookies_multizone = {}
    response = UniconfigOutput(code=500, data={})

    for device in devices_by_uniconfig:
        response = uniconfig_utils.create_tx_internal(uniconfig_cluster=device.uc_cluster)
        match response.code:
            case requests.codes.created:
                uniconfig_cookies_multizone[device.uc_cluster] = response.data["uniconfig_cookies"]
            case _:
                for already_opened_tx_uc_cluster in uniconfig_cookies_multizone:
                    uniconfig_utils.close_tx_internal(
                        uniconfig_cookies_multizone[already_opened_tx_uc_cluster],
                        already_opened_tx_uc_cluster,
                    )
                return UniconfigOutput(
                    code=response.code,
                    data={"failed_zone": device.uc_cluster, "response": response.data},
                    logs=[
                        f'Unable to create multizone transactions. Failed for: "{device.uc_cluster}".Close sent to already opened transactions: "{uniconfig_cookies_multizone}"'
                    ],
                )
    return UniconfigOutput(
        code=response.code,
        data={"uniconfig_cookies_multizone": uniconfig_cookies_multizone},
        logs=[
            f'Transactions created successfully for: "{devices_by_uniconfig}" with context: "{uniconfig_cookies_multizone}"'
        ],
    )


def close_tx_multizone(uniconfig_context: UniconfigCookiesMultizone) -> UniconfigOutput:
    """
    Args:
        uniconfig_context:

    Expected output:
    {
        "uniconfig_cookies_multizone": {
            "http://unistore:8181/rests": {
                "UNICONFIGTXID": "a1cbb742-3108-4170-8a71-6f8590c7bee0",
                "uniconfig_server_id": "a857f8b8af540aa4"
            }
        }
    }

    Task input example:
    {
    "uniconfig_context": {     "started_by_wf": None,     "uniconfig_cookies_multizone": {       "http://localhost/api/uniconfig": {         "UNICONFIGTXID": "cd622f8d-6aab-4b80-98d0-23c948741336",         "uniconfig_server_id": "b7d7962365dd2422"       }     }   }
    """

    uniconfig_cookies_multizone = uniconfig_utils.extract_uniconfig_cookies_multizone(
        uniconfig_context
    )
    response = uniconfig_utils.close_tx_multizone_internal(uniconfig_cookies_multizone)
    return UniconfigOutput(code=response.code, data={"UNICONFIGTXID_multizone": response.data})


def find_started_tx(failed_wf_id: str):
    if failed_wf_id is not str or failed_wf_id == "":
        raise Exception("Bad input failed_wf_id")

    response = requests.get(
        conductor_url_base + "/workflow/" + failed_wf_id, headers=conductor_headers
    )
    response_code, response_json = uniconfig_utils.parse_response(response)

    if response_code != requests.codes.ok:
        return UniconfigOutput(
            code=response_code,
            data={"failed_wf_id": failed_wf_id, "message": "Unable to get workflow"},
        )

    opened_contexts, committed_contexts = uniconfig_utils.find_opened_contexts_in_wf(
        failed_wf_id, response_json
    )

    return UniconfigOutput(
        code=200,
        data={"uniconfig_contexts": opened_contexts, "committed_contexts": committed_contexts},
    )


# TODO finalize
# def rollback_all_tx(uniconfig_contexts: UniconfigTransactionList, committed_contexts: list ):
#
#     # TODO validate inputs?

# committed_ctxs = task["inputData"].get("committed_contexts", [])

# Reverse, in order to close / revert transactions in reverse order
# uniconfig_contexts.reverse()

# for ctx_multizone in uniconfig_contexts:
#
#     if ctx_multizone in committed_contexts:
#         # Reverting committed
#         # return_logs.info("Reverting committed transactions in context: %s", ctx_multizone)
#         response = revert_tx_multizone(ctx_multizone["uniconfig_cookies_multizone"])
#         if response["status"] != util.COMPLETED_STATUS:
#             # Revert failed, stop and return error
#             # return_logs.error(
#             #     "Reverting transactions in context: '%s' FAILED. Stopping reverts. Response: '%s'",
#             #     ctx_multizone,
#             #     response,
#             # )
#             ctx_multizone["rollback_status"] = "revert " + util.FAILED_STATUS
#             return util.failed_response(
#                 {"failed_context": ctx_multizone, "uniconfig_contexts": ctxs}
#             )
#         else:
#             ctx_multizone["rollback_status"] = "revert " + util.COMPLETED_STATUS
#     else:
#         # Closing uncommitted, consider all closes a success
#         # return_logs.info("Closing transactions in context: '%s'", ctx_multizone)
#         close_tx_multizone_internal(ctx_multizone["uniconfig_cookies_multizone"])
#         ctx_multizone["rollback_status"] = "close " + util.COMPLETED_STATUS
#
# return util.completed_response({"uniconfig_contexts": ctxs})
