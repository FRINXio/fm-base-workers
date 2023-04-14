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


ADD_DEVICE_TEMPLATE = """
mutation AddDevice($input: AddDeviceInput!) {
  addDevice(input: $input) {
    device {
      id
      name
    }
  }
} """

INSTALL_DEVICE_TEMPLATE = """
mutation InstallDevice($id: String!){
  installDevice(id:$id){
    device{
      id
      name
    }
  }
} """

INSTALL_DEVICE_VARIABLES = {"id": None}

UNINSTALL_DEVICE_TEMPLATE = """
mutation UninstallDevice($id: String!){
  uninstallDevice(id:$id){
    device{
      id
      name
    }
  }
} """

CREATE_LABEL_TEMPLATE = """
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

CLI_DEVICE_TEMPLATE = {
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

NETCONF_DEVICE_TEMPLATE = {
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

TASK_BODY_TEMPLATE = {
    "name": "sub_task",
    "taskReferenceName": "",
    "type": "SUB_WORKFLOW",
    "subWorkflowParam": {"name": "", "version": 1},
}

LABEL_IDS_TEMPLATE = """
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

DEVICE_PAGE_TEMPLATE = """
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

DEVICE_PAGE_ID_TEMPLATE = """
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

DEVICE_INFO_TEMPLATE = """
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

DEVICE_BY_LABEL_TEMPLATE = """
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
