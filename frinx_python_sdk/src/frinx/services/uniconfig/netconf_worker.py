import copy
import json
import logging
from string import Template
from typing import Union

from aiohttp import ClientSession
from frinx.common.frinx_rest import uniconfig_headers
from frinx.common.frinx_rest import uniconfig_url_base

logger = logging.getLogger(__name__)

URL_NETCONF_MOUNT = (
    uniconfig_url_base
    + "/data/network-topology:network-topology/topology=topology-netconf/node=$id"
)


async def read_structured_data(
    device_name: str, uri: str, session: ClientSession, topology_uri: str = URL_NETCONF_MOUNT
) -> Union[dict, bool]:
    if uri:
        uri = uri if uri.startswith("/") else f"/{uri}"
    else:
        uri = ""

    id_url = Template(topology_uri).substitute({"id": device_name}) + "/yang-ext:mount" + uri
    try:
        async with session.get(id_url, ssl=False, headers=uniconfig_headers) as request:
            response = await request.json()
            logger.info("LLDP raw data: %s", response["output"]["output"])
            return response["output"]["output"]
    except Exception:
        logger.error("Reading structured data from Uniconfig has failed")
        raise


# ###############################################################################

from frinx.services.uniconfig import templates
from frinx.services.uniconfig import utils as uniconfig_utils
from frinx.services.uniconfig.models import NetconfInputBody
from frinx.services.uniconfig.models import UniconfigContext
from frinx.services.uniconfig.models import UniconfigOutput

sync_mount_template = {
    "input": {
        "node-id": "",
        "netconf": {
            "netconf-node-topology:host": "",
            "netconf-node-topology:port": 2022,
            "netconf-node-topology:keepalive-delay": 5,
            "netconf-node-topology:max-connection-attempts": 1,
            "netconf-node-topology:connection-timeout-millis": 60000,
            "netconf-node-topology:default-request-timeout-millis": 60000,
            "netconf-node-topology:tcp-only": False,
            "netconf-node-topology:username": "",
            "netconf-node-topology:password": "",
            "netconf-node-topology:sleep-factor": 1.0,
            "uniconfig-config:uniconfig-native-enabled": True,
            "netconf-node-topology:edit-config-test-option": "set",
            "uniconfig-config:blacklist": {"extension": ["tailf:display-when false"]},
        },
    }
}


def execute_mount_netconf(
    device_id: str,
    host: str,
    port: str,
    keepalive_delay: str,
    tcp_only: str,
    username: str,
    password: str,
    uniconfig_native: str = None,
    blacklist: str = None,
    dry_run_journal_size: str = None,
    sleep_factor: str = None,
    between_attempts_timeout_millis: str = None,
    connection_timeout_millis: str = None,
    reconcile: str = None,
    schema_cache_directory: str = None,
    enabled_notifications: str = None,
    capability: str = None,
):
    device_id = device_id

    mount_body = copy.deepcopy(sync_mount_template)
    mount_body["input"]["node-id"] = device_id
    mount_body["input"]["netconf"]["netconf-node-topology:host"] = host
    mount_body["input"]["netconf"]["netconf-node-topology:port"] = port
    mount_body["input"]["netconf"]["netconf-node-topology:keepalive-delay"] = keepalive_delay

    mount_body["input"]["netconf"]["netconf-node-topology:tcp-only"] = tcp_only
    mount_body["input"]["netconf"]["netconf-node-topology:username"] = username
    mount_body["input"]["netconf"]["netconf-node-topology:password"] = password

    if reconcile is not None and reconcile is not "":
        mount_body["input"]["netconf"]["node-extension:reconcile"] = reconcile

    if schema_cache_directory is not None and schema_cache_directory is not "":
        mount_body["input"]["netconf"][
            "netconf-node-topology:schema-cache-directory"
        ] = schema_cache_directory

    if sleep_factor is not None and sleep_factor is not "":
        mount_body["input"]["netconf"]["netconf-node-topology:sleep-factor"] = sleep_factor

    if between_attempts_timeout_millis is not None and between_attempts_timeout_millis is not "":
        mount_body["input"]["netconf"][
            "netconf-node-topology:between-attempts-timeout-millis"
        ] = between_attempts_timeout_millis

    if connection_timeout_millis is not None and connection_timeout_millis is not "":
        mount_body["input"]["netconf"][
            "netconf-node-topology:connection-timeout-millis"
        ] = connection_timeout_millis

    if uniconfig_native is not None and uniconfig_native is not "":
        mount_body["input"]["netconf"][
            "uniconfig-config:uniconfig-native-enabled"
        ] = uniconfig_native

    if blacklist is not None:
        mount_body["input"]["netconf"]["uniconfig-config:blacklist"] = {"uniconfig-config:path": []}
        model_array = [model.strip() for model in blacklist.split(",")]
        for model in model_array:
            mount_body["input"]["netconf"]["uniconfig-config:blacklist"][
                "uniconfig-config:path"
            ].append(model)

    if dry_run_journal_size is not None:
        mount_body["input"]["netconf"][
            "netconf-node-topology:dry-run-journal-size"
        ] = dry_run_journal_size

    if enabled_notifications is not None:
        mount_body["input"]["netconf"][
            "netconf-node-topology:enabled-notifications"
        ] = enabled_notifications

    if capability is not None:
        mount_body["input"]["netconf"]["netconf-node-topology:yang-module-capabilities"] = {
            "capability": [capability]
        }

    id_url = templates.uniconfig_url_netconf_mount_sync.substitute(
        {"base_url": uniconfig_utils.get_uniconfig_cluster_from_task()}
    )

    response = uniconfig_utils.request("POST", url=id_url, data=json.dumps(mount_body), timeout=600)

    error_message_for_already_installed = "Node has already been installed using NETCONF protocol"

    match response.code:
        case 200:
            failed = response.data.get("output", {}).get("status") == "fail"
            already_installed = (
                response.data.get("output", {}).get("error-message")
                == error_message_for_already_installed
            )

            if not failed or already_installed:
                return UniconfigOutput(
                    code=response.code,
                    data=response.data,
                    url=id_url,
                    logs=f"Mount point with ID {device_id} registered",
                )

            else:
                return UniconfigOutput(
                    code=404,
                    data=response.data,
                    url=id_url,
                    logs=f"Unable to register device with ID {device_id} ",
                )
        case _:
            return UniconfigOutput(
                code=response.code,
                data=response.data,
                url=id_url,
                logs=f"Mount point with ID ${device_id} failed",
            )


def execute_unmount_netconf(device_id: str) -> UniconfigOutput:
    id_url = templates.uniconfig_url_netconf_unmount_sync.substitute(
        {"base_url": uniconfig_utils.get_uniconfig_cluster_from_task()}
    )
    unmount_body = {"input": {"node-id": device_id, "connection-type": "netconf"}}
    response = uniconfig_utils.request("POST", id_url, data=json.dumps(unmount_body))

    return UniconfigOutput(
        code=response.code,
        data=response.data,
        url=id_url,
        logs=f"Mount point with ID ${device_id} removed",
    )


def execute_check_connected_netconf(device_id: str, uniconfig_context: UniconfigContext):
    uniconfig_cookies = uniconfig_utils.extract_uniconfig_cookies(uniconfig_context)

    id_url = templates.uniconfig_url_netconf_mount_oper.substitute(
        {"id": device_id, "base_url": uniconfig_utils.get_uniconfig_cluster_from_task()}
    )

    response = uniconfig_utils.request("GET", id_url, cookies=uniconfig_cookies)

    logs = f"Mount point with ID {device_id} not yet connected"
    if (
        response.code == 200
        and response.data["node"][0]["netconf-node-topology:connection-status"] == "connected"
    ):
        logs = f"Mount point with ID {device_id} connected"

    return UniconfigOutput(code=response.code, data=response.data, url=id_url, logs=logs)


def read_structured_data_sync(
    device_id: str, uri: str, uniconfig_context: UniconfigContext
) -> UniconfigOutput:
    uniconfig_cookies = uniconfig_utils.extract_uniconfig_cookies(uniconfig_context)

    id_url = (
        templates.uniconfig_url_netconf_mount.substitute(
            {"id": device_id, "base_url": uniconfig_utils.get_uniconfig_cluster_from_task()}
        )
        + "/yang-ext:mount"
        + (uri if uri else "")
    )

    response = uniconfig_utils.request("GET", id_url, cookies=uniconfig_cookies)

    logs = f"Unable to read device with ID {device_id}"
    if (
        response.code == 200
        and response.data["node"][0]["netconf-node-topology:connection-status"] == "connected"
    ):
        logs = f"Node with ID {device_id} read successfully"

    return UniconfigOutput(code=response.code, data=response.data, url=id_url, logs=logs)


def execute_mount_any(mount_body: NetconfInputBody):
    id_url = templates.uniconfig_url_netconf_mount_sync.substitute(
        {"base_url": uniconfig_utils.get_uniconfig_cluster_from_task()}
    )

    response = uniconfig_utils.request(
        "POST", url=id_url, data=json.dumps(mount_body.json(exclude_none=True)), timeout=600
    )

    error_message_for_already_installed = "Node has already been installed using NETCONF protocol"

    match response.code:
        case 200:
            failed = response.data.get("output", {}).get("status") == "fail"
            already_installed = (
                response.data.get("output", {}).get("error-message")
                == error_message_for_already_installed
            )

            if not failed or already_installed:
                return UniconfigOutput(
                    code=response.code,
                    data=response.data,
                    url=id_url,
                    logs=f"Mount point with ID {mount_body.node_id} registered",
                )

            else:
                return UniconfigOutput(
                    code=404,
                    data=response.data,
                    url=id_url,
                    logs=f"Unable to register device with ID {mount_body.node_id}",
                )
        case _:
            return UniconfigOutput(
                code=response.code,
                data=response.data,
                url=id_url,
                logs=f"Mount point with ID {mount_body.node_id} failed",
            )
