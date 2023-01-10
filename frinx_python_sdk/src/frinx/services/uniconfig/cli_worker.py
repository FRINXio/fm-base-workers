import copy
import json
import logging
from string import Template
from aiohttp import ClientSession
from frinx_python_sdk.src.frinx.services.frinx_rest import uniconfig_headers, uniconfig_url_base

logger = logging.getLogger(__name__)

URL_CLI_MOUNT_RPC = uniconfig_url_base + "operations/network-topology:network-topology/topology=cli/node=$id"


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
