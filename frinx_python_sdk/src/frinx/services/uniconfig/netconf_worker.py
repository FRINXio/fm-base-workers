import logging
from string import Template
from typing import Union
from aiohttp import ClientSession
from frinx_python_sdk.src.frinx.services.frinx_rest import uniconfig_headers, uniconfig_url_base

logger = logging.getLogger(__name__)

URL_NETCONF_MOUNT = (
    uniconfig_url_base + "/data/network-topology:network-topology/topology=topology-netconf/node=$id"
)


async def read_structured_data(
    device_name: str, uri: str, session: ClientSession, topology_uri: str = URL_NETCONF_MOUNT
) -> Union[dict, bool]:
    if uri:
        uri = uri if uri.startswith("/") else f"/{uri}"
    else:
        uri = ""

    id_url = (
            Template(topology_uri).substitute({"id": device_name})
            + "/yang-ext:mount" + uri
    )
    try:
        async with session.get(
                id_url, ssl=False, headers=uniconfig_headers
        ) as r:
            res = await r.json()
            logger.info("LLDP raw data: %s", res["output"]["output"])
            return res["output"]["output"]
    except Exception:
        logger.error("Reading structured data from Uniconfig has failed")
        raise
