import copy
import json
import logging
from string import Template
from typing import Any

from aiohttp import ClientSession
from frinx.common.frinx_rest import uniconfig_headers
from frinx.common.frinx_rest import uniconfig_url_base

logger = logging.getLogger(__name__)

URL_CLI_MOUNT_RPC = (
    uniconfig_url_base + "/operations/network-topology:network-topology/topology=cli/node=$id"
)


async def execute_and_read_rpc_cli(
    device_name: str, command: str, session: ClientSession, output_timer=None
):
    execute_and_read_template = {"input": {"command": ""}}
    exec_body = copy.deepcopy(execute_and_read_template)
    exec_body["input"]["command"] = command

    if output_timer:
        exec_body["input"]["wait-for-output-timer"] = output_timer

    id_url = (
        Template(URL_CLI_MOUNT_RPC).substitute({"id": device_name})
        + "/yang-ext:mount/cli-unit-generic:execute-and-read"
    )
    try:
        async with session.post(
            id_url, data=json.dumps(exec_body), ssl=False, headers=uniconfig_headers
        ) as r:
            res = await r.json()
            logger.info("LLDP raw data: %s", res["output"]["output"])
            return res["output"]["output"]
    except Exception:
        logger.error("Reading rpc from Uniconfig has failed")
        raise


# ###############################################################################

from frinx.services.uniconfig import templates
from frinx.services.uniconfig import utils as uniconfig_utils
from frinx.services.uniconfig.models import UniconfigContext
from frinx.services.uniconfig.models import UniconfigOutput

sync_mount_template = {
    "input": {
        "node-id": "",
        "cli": {
            "cli-topology:host": "",
            "cli-topology:port": "",
            "cli-topology:transport-type": "ssh",
            "cli-topology:device-type": "",
            "cli-topology:device-version": "",
            "cli-topology:username": "",
            "cli-topology:password": "",
            "cli-topology:journal-size": 500,
            "cli-topology:dry-run-journal-size": 180,
        },
    }
}


def execute_mount_cli(
    device_id: str,
    host: str,
    port: str,
    protocol: str,
    type: str,
    version: str,
    username: str,
    password: str,
    parsing_engine: str,
):
    """
    Build a template for CLI mounting body (mount_body) from input device
    parameters and issue a PUT request to Uniconfig to mount it. These requests
    can also be viewed and tested in postman collections for each device.

    Args:
        parsing_engine:
        password:
        username:
        version:
        type:
        protocol:
        port:
        host:
        device_id:
    Returns:
        response: dict, e.g. {"status": "COMPLETED", "output": {"url": id_url,
                                                  "request_body": mount_body,
                                                  "response_code": 200,
                                                  "response_body": response_json},
                }}
    """

    if parsing_engine is None:
        parsing_engine = "tree-parser"

    mount_body = copy.deepcopy(sync_mount_template)

    mount_body["input"]["node-id"] = device_id
    mount_body["input"]["cli"]["cli-topology:host"] = host
    mount_body["input"]["cli"]["cli-topology:port"] = port
    mount_body["input"]["cli"]["cli-topology:transport-type"] = protocol
    mount_body["input"]["cli"]["cli-topology:device-type"] = type
    mount_body["input"]["cli"]["cli-topology:device-version"] = version
    mount_body["input"]["cli"]["cli-topology:username"] = username
    mount_body["input"]["cli"]["cli-topology:password"] = password
    mount_body["input"]["cli"]["cli-topology:parsing-engine"] = parsing_engine

    # mount_body["input"]["cli"]["uniconfig-config:install-uniconfig-node-enabled"] = task[
    #     "inputData"
    # ].get("install-uniconfig-node-enabled", True)

    id_url = templates.uniconfig_url_cli_mount_sync.substitute(
        {"base_url": uniconfig_utils.get_uniconfig_cluster_from_task()}
    )

    # TODO finish

    # response = uniconfig_utils.request("POST", id_url, data=json.dumps(mount_body), timeout=600)
    # match response.code:
    #     case 200:
    #         logs = f"Mount point with ID {device_id} configured"
    #     case _:
    #         logs = f"Unable to configure device with ID {device_id}"
    #
    # return UniconfigOutput(code=response.code, data=response.data, url=id_url, logs=logs)
    #
    # error_message_for_already_installed = "Node has already been installed using CLI protocol"
    #
    # failed = response_json.get("output", {}).get("status") == "fail"
    # already_installed = (
    #     response_json.get("output", {}).get("error-message") == error_message_for_already_installed
    # )
    #
    # if not failed or already_installed:
    #     return {
    #         "status": "COMPLETED",
    #         "output": {
    #             "url": id_url,
    #             "request_body": mount_body,
    #             "response_code": response_code,
    #             "response_body": response_json,
    #         },
    #         "logs": ["Mountpoint with ID %s registered" % device_id],
    #     }
    # else:
    #     return {
    #         "status": "FAILED",
    #         "output": {
    #             "url": id_url,
    #             "request_body": mount_body,
    #             "response_code": response_code,
    #             "response_body": response_json,
    #         },
    #         "logs": ["Unable to register device with ID %s" % device_id],
    #     }
    #


def execute_unmount_cli(device_id: str) -> UniconfigOutput:
    try:
        id_url = templates.uniconfig_url_cli_unmount_sync.substitute(
            {"base_url": uniconfig_utils.get_uniconfig_cluster_from_task()}
        )

        unmount_body = {"input": {"node-id": device_id, "connection-type": "cli"}}
        response = uniconfig_utils.request("POST", id_url, data=json.dumps(unmount_body))

        return UniconfigOutput(
            code=response.code,
            data=response.data,
            url=id_url,
            logs=f"Mount point with ID ${device_id} removed",
        )

    except Exception as e:
        # TODO status code check
        return UniconfigOutput(
            data={"output": e}, logs="Unable to read device with ID %s" % device_id, code=500
        )


def execute_and_read_rpc_cli(
    device_id: str,
    template: str,
    params: dict[Any, Any],
    uniconfig_context: UniconfigContext,
    output_timer: str,
) -> UniconfigOutput:
    params = params if params else {}
    # params = params if isinstance(params, dict) else eval(params) ???
    params = params if isinstance(params, dict) else eval(str(params))

    uniconfig_cookies = uniconfig_utils.extract_uniconfig_cookies(uniconfig_context)

    commands = Template(template).substitute(params)
    execute_and_read_template = {"input": {"ios-cli:command": ""}}
    exec_body = copy.deepcopy(execute_and_read_template)
    exec_body["input"]["ios-cli:command"] = commands

    if output_timer:
        exec_body["input"]["wait-for-output-timer"] = output_timer

    id_url = (
        templates.uniconfig_url_cli_mount_rpc.substitute(
            {"id": device_id, "base_url": uniconfig_utils.get_uniconfig_cluster_from_task()}
        )
        + "/yang-ext:mount/cli-unit-generic:execute-and-read"
    )

    response = uniconfig_utils.request(
        "POST", id_url, data=json.dumps(exec_body), cookies=uniconfig_cookies
    )
    match response.code:
        case 200:
            logs = f"Mount point with ID {device_id} configured"
        case _:
            logs = f"Unable to configure device with ID {device_id}"

    return UniconfigOutput(code=response.code, data=response.data, url=id_url, logs=logs)


def execute_get_cli_journal(device_id: str, uniconfig_context: UniconfigContext) -> UniconfigOutput:
    uniconfig_cookies = uniconfig_utils.extract_uniconfig_cookies(uniconfig_context)

    id_url = templates.uniconfig_url_cli_read_journal.substitute(
        {"id": device_id, "base_url": uniconfig_utils.get_uniconfig_cluster_from_task()}
    )

    response = uniconfig_utils.request("POST", id_url, data=None, cookies=uniconfig_cookies)

    match response.code:
        case 200:
            logs = ""
        case _:
            logs = f"Mount point with ID {device_id}, cannot read journal"

    return UniconfigOutput(code=response.code, data=response.data, url=id_url, logs=logs)


execute_template = {"input": {"command": "", "wait-for-output-timer": "5"}}


def execute_cli(
    device_id: str, template: str, params: dict[Any, Any], uniconfig_context: UniconfigContext
) -> UniconfigOutput:
    params = params if params else {}
    # params = params if isinstance(params, dict) else eval(params) ???
    params = params if isinstance(params, dict) else eval(str(params))

    uniconfig_cookies = uniconfig_utils.extract_uniconfig_cookies(uniconfig_context)

    commands = Template(template).substitute(params)
    exec_body = copy.deepcopy(execute_template)

    exec_body["input"]["command"] = commands

    id_url = (
        templates.uniconfig_url_cli_mount_rpc.substitute(
            {"id": device_id, "base_url": uniconfig_utils.get_uniconfig_cluster_from_task()}
        )
        + "/yang-ext:mount/cli-unit-generic:execute"
    )

    response = uniconfig_utils.request(
        "POST", id_url, data=json.dumps(exec_body), cookies=uniconfig_cookies
    )

    match response.code:
        case 200:
            logs = f"Mount point with ID {device_id} configured"
        case _:
            logs = f"Unable to configure device with ID {device_id}"

    return UniconfigOutput(code=response.code, data=response.data, url=id_url, logs=logs)


def execute_and_expect_cli(
    device_id: str, template: str, params: dict[Any, Any], uniconfig_context: UniconfigContext
) -> UniconfigOutput:
    params = params if params else {}
    # params = params if isinstance(params, dict) else eval(params) ???
    params = params if isinstance(params, dict) else eval(str(params))

    uniconfig_cookies = uniconfig_utils.extract_uniconfig_cookies(uniconfig_context)

    commands = Template(template).substitute(params)
    exec_body = copy.deepcopy(execute_template)

    exec_body["input"]["command"] = commands

    id_url = (
        templates.uniconfig_url_cli_mount_rpc.substitute(
            {"id": device_id, "base_url": uniconfig_utils.get_uniconfig_cluster_from_task()}
        )
        + "/yang-ext:mount/cli-unit-generic:execute-and-expect"
    )

    response = uniconfig_utils.request(
        "POST", id_url, data=json.dumps(exec_body), cookies=uniconfig_cookies
    )

    match response.code:
        case 200:
            logs = f"Mount point with ID {device_id} configured"
        case _:
            logs = f"Unable to configure device with ID {device_id}"

    return UniconfigOutput(code=response.code, data=response.data, url=id_url, logs=logs)
