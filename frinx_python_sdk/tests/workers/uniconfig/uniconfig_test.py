import unittest
from unittest.mock import patch

from frinx.common.frinx_rest import uniconfig_url_base
from frinx.common.worker.task import Task
from frinx.common.worker.task_result import TaskResult
from frinx.common.worker.task_result import TaskResultStatus

# from frinx.services.uniconfig import uniconfig_worker
from frinx.services.uniconfig.models import UniconfigContext
from frinx.services.uniconfig.models import UniconfigRpcResponse
from frinx.workers.uniconfig import uniconfig_worker

xr5_response = {
    "topology": [
        {
            "node": [{"node-id": "xr5"}],
            "topology-id": "uniconfig",
            "topology-types": {"frinx-uniconfig-topology:uniconfig": {}},
        }
    ]
}
interface_response = {
    "frinx-openconfig-interfaces:interfaces": {
        "interface": [
            {
                "config": {
                    "enabled": "false",
                    "type": "iana-if-type:ethernetCsmacd",
                    "name": "GigabitEthernet0/0/0/0",
                },
                "name": "GigabitEthernet0/0/0/0",
            },
            {
                "config": {
                    "enabled": "false",
                    "type": "iana-if-type:ethernetCsmacd",
                    "name": "GigabitEthernet0/0/0/1",
                },
                "name": "GigabitEthernet0/0/0/1",
            },
            {
                "config": {
                    "enabled": "false",
                    "type": "iana-if-type:ethernetCsmacd",
                    "name": "GigabitEthernet0/0/0/2",
                },
                "name": "GigabitEthernet0/0/0/2",
            },
        ]
    }
}
bad_request_response = {
    "errors": {
        "error": [
            {
                "error-type": "protocol",
                "error-tag": "data-missing",
                "error-message": "Request could not be completed because the relevant data model content does not exist",
            }
        ]
    }
}
bad_input_response = {
    "errors": {
        "error": [
            {
                "error-type": "protocol",
                "error-message": "Error parsing input: com.google.common.util.concurrent.UncheckedExecutionException: java.lang.IllegalStateException: Schema node with name prefix was not found under (http://frinx.openconfig.net/yang/interfaces?revision=2016-12-22)config.",
                "error-tag": "malformed-message",
                "error-info": "com.google.common.util.concurrent.UncheckedExecutionException: java.lang.IllegalStateException: Schema node with name prefix was not found under (http://frinx.openconfig.net/yang/interfaces?revision=2016-12-22)config.",
            }
        ]
    }
}
commit_output = {
    "output": {
        "overall-status": "complete",
        "node-results": {
            "node-result": [
                {"node-id": "xr5", "configuration-status": "complete"},
                {"node-id": "xr6", "configuration-status": "complete"},
            ]
        },
    }
}
dry_run_output = {
    "output": {
        "overall-status": "complete",
        "node-results": {
            "node-result": [
                {
                    "node-id": "xr5",
                    "configuration": "2019-09-13T08:37:28.331: configure terminal\n2019-09-13T08:37:28.536: interface GigabitEthernet0/0/0/1\nshutdown\nroot\n\n2019-09-13T08:37:28.536: commit\n2019-09-13T08:37:28.536: end\n",
                    "configuration-status": "complete",
                }
            ]
        },
    }
}
calculate_diff_output = {
    "output": {
        "overall-status": "complete",
        "node-results": {
            "node-result": [
                {
                    "node-id": "xr5",
                    "updated-data": [
                        {
                            "path": "network-topology:network-topology/topology=uniconfig/node=xr5/frinx-uniconfig-topology:configuration/frinx-openconfig-interfaces:interfaces/interface=GigabitEthernet0%2F0%2F0%2F0/config",
                            "data-actual": '{\n  "frinx-openconfig-interfaces:config": {\n    "type": "iana-if-type:ethernetCsmacd",\n    "enabled": false,\n    "name": "GigabitEthernet0/0/0/0"\n  }\n}',
                            "data-intended": '{\n  "frinx-openconfig-interfaces:config": {\n    "type": "iana-if-type:ethernetCsmacd",\n    "enabled": false,\n    "name": "GigabitEthernet0/0/0/0dfhdfghd"\n  }\n}',
                        }
                    ],
                    "status": "complete",
                }
            ]
        },
    }
}


class TestReadStructuredData(unittest.TestCase):
    def test_read_structured_data_with_device(self):
        with patch("frinx.services.uniconfig.utils.request") as mock:
            mock.return_value = UniconfigRpcResponse(
                code=200, data=interface_response, cookies=None
            )

            task = Task(
                input_data={
                    "device_id": "xr5",
                    "uri": "/frinx-openconfig-interfaces:interfaces",
                    "uniconfig_context": None,
                }
            )

            worker = uniconfig_worker.Uniconfig.UniconfigReadStructuredDeviceData()

            response = worker.execute(task=task)

            self.assertEqual(response.status, TaskResultStatus.COMPLETED)

            self.assertEqual(response.output["response_code"], 200)

            self.assertEqual(
                response.output["url"],
                uniconfig_url_base
                + "/data/network-topology:network-topology/topology=uniconfig/node=xr5"
                "/frinx-uniconfig-topology:configuration"
                "/frinx-openconfig-interfaces:interfaces",
            )

            self.assertEqual(
                response.output["response_body"]["frinx-openconfig-interfaces:interfaces"][
                    "interface"
                ][0]["config"]["name"],
                "GigabitEthernet0/0/0/0",
            )
            self.assertEqual(
                response.output["response_body"]["frinx-openconfig-interfaces:interfaces"][
                    "interface"
                ][1]["config"]["name"],
                "GigabitEthernet0/0/0/1",
            )
            self.assertEqual(
                response.output["response_body"]["frinx-openconfig-interfaces:interfaces"][
                    "interface"
                ][2]["config"]["name"],
                "GigabitEthernet0/0/0/2",
            )

    def test_read_structured_data_no_device(self):
        exception_message: str = ""

        try:
            with patch("frinx.services.uniconfig.utils.request") as mock:
                mock.return_value = UniconfigRpcResponse(
                    code=500, data=bad_request_response, cookies=None
                )

                task = Task(
                    input_data={
                        "device_id": "",
                        "uri": "/frinx-openconfig-interfaces:interfaces",
                        "uniconfig_context": None,
                    }
                )

                worker = uniconfig_worker.Uniconfig.UniconfigReadStructuredDeviceData()

                response = worker.execute(task=task)
                self.assertEqual(response.status, TaskResultStatus.FAILED)

        except Exception as e:
            exception_message = str(e)

        self.assertEqual("Missing input device_id", exception_message)


class TestWriteStructuredData(unittest.TestCase):
    def test_write_structured_data(self):
        with patch("frinx.services.uniconfig.utils.request") as mock:
            mock.return_value = UniconfigRpcResponse(code=201, data={}, cookies=None)

            task = Task(
                input_data={
                    "device_id": "xr5",
                    "uri": "/frinx-openconfig-interfaces:interfaces/interface=Loopback01",
                    "template": '{"interface":[{"name":"Loopback01",'
                    '"config":{'
                    '"type":"iana-if-type:softwareLoopback",'
                    '"enabled":false,'
                    '"name":"Loopback01",'
                    '"prefix": "aaa"}}]}',
                    "params": {},
                    "uniconfig_context": None,
                }
            )

            worker = uniconfig_worker.Uniconfig.UniconfigWriteStructuredDeviceData()

            response = worker.execute(task=task)

            self.assertEqual(response.status, TaskResultStatus.COMPLETED)
            self.assertEqual(
                response.output["url"],
                uniconfig_url_base
                + "/data/network-topology:network-topology/topology=uniconfig/node=xr5/"
                "frinx-uniconfig-topology:configuration/"
                "frinx-openconfig-interfaces:interfaces/interface=Loopback01",
            )
            self.assertEqual(response.output["response_code"], 201)

    def test_write_structured_data_with_template_dict(self):
        with patch("frinx.services.uniconfig.utils.request") as mock:
            mock.return_value = UniconfigRpcResponse(code=404, data={}, cookies=None)

            task = Task(
                input_data={
                    "device_id": "xr5",
                    "uri": "/frinx-openconfig-interfaces:interfaces/interface=Loopback01",
                    "template": {
                        "interface": [
                            {
                                "name": "Loopback01",
                                "config": {
                                    "type": "iana-if-type:softwareLoopback",
                                    "enabled": False,
                                    "name": "Loopback01",
                                    "prefix": "aaa",
                                },
                            }
                        ]
                    },
                    "params": None,
                    "uniconfig_context": None,
                }
            )

            worker = uniconfig_worker.Uniconfig.UniconfigWriteStructuredDeviceData()

            response = worker.execute(task=task)

            self.assertEqual(response.status, TaskResultStatus.FAILED)
            self.assertEqual(response.output["response_code"], 404)

            self.assertEqual(
                response.output["url"],
                uniconfig_url_base
                + "/data/network-topology:network-topology/topology=uniconfig/node=xr5/"
                "frinx-uniconfig-topology:configuration/"
                "frinx-openconfig-interfaces:interfaces/interface=Loopback01",
            )

    def test_write_structured_data_with_template_str(self):
        with patch("frinx.services.uniconfig.utils.request") as mock:
            mock.return_value = UniconfigRpcResponse(code=404, data={}, cookies=None)

            task = Task(
                input_data={
                    "device_id": "xr5",
                    "uri": "/frinx-openconfig-interfaces:interfaces/interface=Loopback01",
                    "template": '{"interface":[{"name":"Loopback01",'
                    '"config":{'
                    '"type":"iana-if-type:softwareLoopback",'
                    '"enabled":false,'
                    '"name":"Loopback01",'
                    '"prefix": "aaa"}}]}',
                    "params": {},
                    "uniconfig_context": None,
                }
            )

            worker = uniconfig_worker.Uniconfig.UniconfigWriteStructuredDeviceData()

            response = worker.execute(task=task)

            self.assertEqual(response.status, TaskResultStatus.FAILED)
            self.assertEqual(response.output["response_code"], 404)

            self.assertEqual(
                response.output["url"],
                uniconfig_url_base
                + "/data/network-topology:network-topology/topology=uniconfig/node=xr5/"
                "frinx-uniconfig-topology:configuration/"
                "frinx-openconfig-interfaces:interfaces/interface=Loopback01",
            )


class TestDeleteStructuredData(unittest.TestCase):
    def test_delete_structured_data_with_device(self):
        with patch("frinx.services.uniconfig.utils.request") as mock:
            mock.return_value = UniconfigRpcResponse(code=204, data={}, cookies=None)

            task = Task(
                input_data={
                    "device_id": "xr5",
                    "uri": "/frinx-openconfig-interfaces:interfaces/interface=Loopback01",
                    "uniconfig_context": None,
                }
            )

            worker = uniconfig_worker.Uniconfig.UniconfigDeleteStructuredDeviceData()

            response = worker.execute(task=task)

            self.assertEqual(response.status, TaskResultStatus.COMPLETED)
            self.assertEqual(response.output["response_code"], 204)
            self.assertEqual(response.output.get("response_body", {}), {})

    def test_delete_structured_data_with_bad_template(self):
        with patch("frinx.services.uniconfig.utils.request") as mock:
            mock.return_value = UniconfigRpcResponse(
                code=404, data=bad_request_response, cookies=None
            )

            task = Task(
                input_data={
                    "device_id": "xr5",
                    "uri": "/frinx-openconfig-interfaces:interfaces/interface=Loopback01",
                    "uniconfig_context": None,
                }
            )

            worker = uniconfig_worker.Uniconfig.UniconfigDeleteStructuredDeviceData()

            response = worker.execute(task=task)

            self.assertEqual(response.status, TaskResultStatus.FAILED)
            self.assertEqual(response.output["response_code"], 404)

            self.assertEqual(
                response.output["response_body"]["errors"]["error"][0]["error-type"], "protocol"
            )
            self.assertEqual(
                response.output["response_body"]["errors"]["error"][0]["error-message"],
                "Request could not be completed because the relevant data model content does not exist",
            )
            self.assertEqual(
                response.output["response_body"]["errors"]["error"][0]["error-tag"], "data-missing"
            )


class TestCommit(unittest.TestCase):
    def test_commit_with_existing_devices(self):
        with patch("frinx.services.uniconfig.utils.request") as mock:
            mock.return_value = UniconfigRpcResponse(code=200, data=commit_output, cookies=None)

            task = Task(input_data={"devices": "xr5, xr6", "uniconfig_context": None})

            worker = uniconfig_worker.Uniconfig.UniconfigCommit()

            response = worker.execute(task=task)

            self.assertEqual(response.status, TaskResultStatus.COMPLETED)

            self.assertEqual(response.output["response_code"], 200)

            self.assertEqual(
                response.output["response_body"]["responses"][0]["response_body"]["output"][
                    "overall-status"
                ],
                "complete",
            )
            self.assertEqual(
                response.output["response_body"]["responses"][0]["response_body"]["output"][
                    "node-results"
                ]["node-result"][0]["node-id"],
                "xr5",
            )
            self.assertEqual(
                response.output["response_body"]["responses"][0]["response_body"]["output"][
                    "node-results"
                ]["node-result"][0]["configuration-status"],
                "complete",
            )
            self.assertEqual(
                response.output["response_body"]["responses"][0]["response_body"]["output"][
                    "node-results"
                ]["node-result"][1]["node-id"],
                "xr6",
            )
            self.assertEqual(
                response.output["response_body"]["responses"][0]["response_body"]["output"][
                    "node-results"
                ]["node-result"][1]["configuration-status"],
                "complete",
            )
