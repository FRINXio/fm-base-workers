import copy
import dataclasses
import json
import logging
from enum import Enum
from typing import Any

from frinx.services.frinx_rest import inventory_url_base
from frinx.services.frinx_rest import x_tenant_id
from frinx.services.inventory import templates
from python_graphql_client import GraphqlClient

# graphql client settings
inventory_headers = {
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Connection": "keep-alive",
    "x-tenant-id": x_tenant_id,
    "DNT": "1",
    "Keep-Alive": "timeout=5",
}

# client = GraphqlClient(endpoint="inventory_url_base", headers=inventory_headers)
client = GraphqlClient(endpoint="http://localhost/api/inventory", headers=inventory_headers)


class ServiceState(str, Enum):
    PLANNING = "PLANNING"
    IN_SERVICE = "IN_SERVICE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


@dataclasses.dataclass
class InventoryOutput:
    status: str
    code: int
    data: Any


def execute_inventory(body: str, variables: Any) -> InventoryOutput:
    print("Inventory worker", body, variables)

    match variables:
        case None:
            pass
        case dict():
            variables = json.dumps(variables)
        case _:
            variables = json.loads(str(variables))

    response = client.execute(query=body, variables=variables)

    if response.get("errors") is not None:
        return InventoryOutput(data=response["errors"], status="errors", code=404)
    elif response.get("data") is not None:
        return InventoryOutput(data=response["data"], status="data", code=200)
    else:
        return InventoryOutput(data="Request failed", status="failed", code=500)


def get_zone_id(zone_name: str) -> str:
    zone_id_device = "query { zones { edges { node {  id name } } } }"

    body = execute_inventory(zone_id_device, {})

    for node in body.data["zones"]["edges"]:
        if node["node"]["name"] == zone_name:
            return node["node"]["id"]


def get_all_devices(labels: str) -> dict:
    device_id_name = copy.deepcopy(templates.device_by_label_template)

    variables = {"labels": str(str(labels))}

    body = execute_inventory(device_id_name, variables)
    return body.data["devices"]["edges"]


def get_label_id() -> dict:
    label_id_device = "query { labels { edges { node {  id name } } } }"
    body = execute_inventory(label_id_device, {})

    label_id = {}
    for node in body.data["labels"]["edges"]:
        label_id[node["node"]["name"]] = node["node"]["id"]

    return label_id


def label_name_id(data: dict) -> dict:
    label_dict = {}
    for node in data["labels"]["edges"]:
        label_dict[node["node"]["name"]] = node["node"]["id"]
    return label_dict
