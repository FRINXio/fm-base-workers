import json
from dataclasses import asdict
from dataclasses import dataclass
from typing import Any
from typing import Optional


class InventoryVariable:
    def __repr__(self) -> dict:
        print(type(json.dumps(asdict(self))))
        return json.dumps(asdict(self))

    def __str__(self) -> dict:
        print(type(json.dumps(asdict(self))))
        return json.dumps(asdict(self))


@dataclass
class InputVariable(InventoryVariable):
    input: Any


@dataclass
class AddDeviceVariable(InventoryVariable):
    name: str
    zoneId: str
    serviceState: str
    mountParameters: str
    vendor: Optional[str] = None
    model: Optional[str] = None
    deviceSize: Optional[str] = None
    labelIds: Optional[str] = None


@dataclass
class CreateLabelInput(InventoryVariable):
    name: str


@dataclass
class DevicePageCursorInput(InventoryVariable):
    first: int
    after: str
    labels: Optional[list[str]]


@dataclass
class InstallDeviceInput(InventoryVariable):
    id: str


add_device_template = """
mutation AddDevice($input: AddDeviceInput!) {
  addDevice(input: $input) {
    device {
      id
      name
    }
  }
} """

install_device_template = """
mutation InstallDevice($id: String!){
  installDevice(id:$id){
    device{
      id
      name
    }
  }
} """

install_device_variables = {"id": None}

uninstall_device_template = """
mutation UninstallDevice($id: String!){
  uninstallDevice(id:$id){
    device{
      id
      name
    }
  }
} """

create_label_template = """
mutation CreateLabel($input: CreateLabelInput!) {
  createLabel(input: $input){
    label {
        id
        name
        createdAt
        updatedAt
    }
  }
} """

cli_device_template = {
    "cli": {
        "cli-topology:host": "",
        "cli-topology:port": "",
        "cli-topology:transport-type": "ssh",
        "cli-topology:device-type": "",
        "cli-topology:device-version": "",
        "cli-topology:password": "",
        "cli-topology:username": "",
        "cli-topology:journal-size": "",
        "cli-topology:parsing-engine": "",
    }
}

netconf_device_template = {
    "netconf": {
        "netconf-node-topology:host": "",
        "netconf-node-topology:port": "",
        "netconf-node-topology:keepalive-delay": "",
        "netconf-node-topology:tcp-only": "",
        "netconf-node-topology:username": "",
        "netconf-node-topology:password": "",
        "uniconfig-config:uniconfig-native-enabled": "",
        "uniconfig-config:blacklist": {"uniconfig-config:path": []},
    }
}

task_body_template = {
    "name": "sub_task",
    "taskReferenceName": "",
    "type": "SUB_WORKFLOW",
    "subWorkflowParam": {"name": "", "version": 1},
}

label_ids_template = """
query {
  labels {
    edges {
      node {
        id
        name
        createdAt
        updatedAt
      }
    }
  }
}
"""

device_page_template = """
query GetDevices(
  $first: Int!, 
  $after: String!,
  $labels: [String!]
) {
  devices(first: $first, after: $after, filter: { labels: $labels } ) {
    pageInfo {
      startCursor
      endCursor
      hasPreviousPage
      hasNextPage
    }
  }
} """

device_page_id_template = """
query GetDevices($labels: [String!], $first: Int!, $after: String!) {
  devices( filter: { labels: $labels}, first:$first, after:$after) {
    pageInfo {
      startCursor
      endCursor
      hasPreviousPage
      hasNextPage
    }
    edges {
      node {
        name
        id
      }
    }
  }
} """

device_info_template = """
query Devices(
  $labels: [String!]
  $deviceName: String
) {
  devices(
    filter: { labels: $labels, deviceName: $deviceName }
  ) {
    edges {
      node {
        id
        name
        createdAt
        isInstalled
        serviceState
        zone {
          id
          name
        }
      }
    }
  }
} """

device_by_label_template = """
query Devices(
  $labels: [String!]
) {
  devices(
    filter: { labels: $labels }
  ) {
    edges {
      node {
        name
      }
    }
  }
} """
