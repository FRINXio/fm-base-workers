#!/usr/bin/env/python3
import json
import unittest
from http.cookies import SimpleCookie
from unittest.mock import patch

import frinx_conductor_workers.uniconfig_worker
from frinx_conductor_workers.frinx_rest import uniconfig_url_base

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
RPC_output_multiple_devices = {
    "output": {
        "node-results": {
            "node-result": [
                {"node-id": "xr5", "status": "complete"},
                {"node-id": "xr6", "status": "complete"},
            ]
        },
        "overall-status": "complete",
    }
}
RPC_output_one_device = {
    "output": {
        "node-results": {"node-result": [{"node-id": "xr5", "status": "complete"}]},
        "overall-status": "complete",
    }
}


class MockResponse:
    def __init__(self, content, status_code, cookies):
        self.content = content
        self.status_code = status_code
        self.cookies = cookies

    def json(self):
        return self.content


class TestReadStructuredData(unittest.TestCase):
    def test_read_structured_data_with_device(self):
        with patch("frinx_conductor_workers.uniconfig_worker.requests.get") as mock:
            mock.return_value = MockResponse(
                bytes(json.dumps(interface_response), encoding="utf-8"), 200, ""
            )
            request = frinx_conductor_workers.uniconfig_worker.read_structured_data(
                {
                    "inputData": {
                        "device_id": "xr5",
                        "uri": "/frinx-openconfig-interfaces:interfaces",
                    }
                }
            )
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(
                request["output"]["url"],
                uniconfig_url_base
                + "/data/network-topology:network-topology/topology=uniconfig/node=xr5"
                "/frinx-uniconfig-topology:configuration"
                "/frinx-openconfig-interfaces:interfaces",
            )
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(
                request["output"]["response_body"]["frinx-openconfig-interfaces:interfaces"][
                    "interface"
                ][0]["config"]["name"],
                "GigabitEthernet0/0/0/0",
            )
            self.assertEqual(
                request["output"]["response_body"]["frinx-openconfig-interfaces:interfaces"][
                    "interface"
                ][1]["config"]["name"],
                "GigabitEthernet0/0/0/1",
            )
            self.assertEqual(
                request["output"]["response_body"]["frinx-openconfig-interfaces:interfaces"][
                    "interface"
                ][2]["config"]["name"],
                "GigabitEthernet0/0/0/2",
            )

    def test_read_structured_data_no_device(self):
        with patch("frinx_conductor_workers.uniconfig_worker.requests.get") as mock:
            mock.return_value = MockResponse(
                bytes(json.dumps(bad_request_response), encoding="utf-8"), 500, ""
            )
            request = frinx_conductor_workers.uniconfig_worker.read_structured_data(
                {"inputData": {"device_id": "", "uri": "/frinx-openconfig-interfaces:interfaces"}}
            )
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["response_code"], 500)
            self.assertEqual(
                request["output"]["response_body"]["errors"]["error"][0]["error-type"], "protocol"
            )
            self.assertEqual(
                request["output"]["response_body"]["errors"]["error"][0]["error-message"],
                "Request could not be completed because the relevant data model content does not exist",
            )


class TestWriteStructuredData(unittest.TestCase):
    def test_write_structured_data_with_device(self):
        with patch("frinx_conductor_workers.uniconfig_worker.requests.request") as mock:
            mock.return_value = MockResponse(bytes(json.dumps({}), encoding="utf-8"), 201, "")
            request = frinx_conductor_workers.uniconfig_worker.write_structured_data(
                {
                    "inputData": {
                        "device_id": "xr5",
                        "uri": "/frinx-openconfig-interfaces:interfaces/interface=Loopback01",
                        "template": '{"interface":[{"name":"Loopback01",'
                        '"config":{'
                        '"type":"iana-if-type:softwareLoopback",'
                        '"enabled":false,'
                        '"name":"Loopback01",'
                        '"prefix": "aaa"}}]}',
                        "params": {},
                    }
                }
            )
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(
                request["output"]["url"],
                uniconfig_url_base
                + "/data/network-topology:network-topology/topology=uniconfig/node=xr5/"
                "frinx-uniconfig-topology:configuration/"
                "frinx-openconfig-interfaces:interfaces/interface=Loopback01",
            )
            self.assertEqual(request["output"]["response_code"], 201)

    def test_write_structured_data_with_no_device(self):
        with patch("frinx_conductor_workers.uniconfig_worker.requests.request") as mock:
            mock.return_value = mock.return_value = MockResponse(
                bytes(json.dumps({}), encoding="utf-8"), 404, ""
            )
            request = frinx_conductor_workers.uniconfig_worker.write_structured_data(
                {
                    "inputData": {
                        "device_id": "",
                        "uri": "/frinx-openconfig-interfaces:interfaces/interface=Loopback01",
                        "template": '{"interface":[{"name":"Loopback01",'
                        '"config":{'
                        '"type":"iana-if-type:softwareLoopback",'
                        '"enabled":false,'
                        '"name":"Loopback01",'
                        '"prefix": "aaa"}}]}',
                        "params": {},
                    }
                }
            )
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(
                request["output"]["url"],
                uniconfig_url_base
                + "/data/network-topology:network-topology/topology=uniconfig/node=/"
                "frinx-uniconfig-topology:configuration/"
                "frinx-openconfig-interfaces:interfaces/interface=Loopback01",
            )
            self.assertEqual(request["output"]["response_code"], 404)

    def test_write_structured_data_with_bad_template(self):
        with patch("frinx_conductor_workers.uniconfig_worker.requests.request") as mock:
            mock.return_value = MockResponse(
                bytes(json.dumps(bad_input_response), encoding="utf-8"), 400, ""
            )
            request = frinx_conductor_workers.uniconfig_worker.write_structured_data(
                {
                    "inputData": {
                        "device_id": "xr5",
                        "uri": "/frinx-openconfig-interfaces:interfaces/interface=Loopback01",
                        "template": '{"interface":[{"name":"Loopback01",'
                        '"config":{'
                        '"type":"iana-if-type:softwareLoopback",'
                        '"enabled":false,'
                        '"name":"Loopback01",'
                        '"prefix": "aaa"}}]}',
                        "params": {},
                    }
                }
            )
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(
                request["output"]["url"],
                uniconfig_url_base
                + "/data/network-topology:network-topology/topology=uniconfig/node=xr5/"
                "frinx-uniconfig-topology:configuration/"
                "frinx-openconfig-interfaces:interfaces/interface=Loopback01",
            )
            self.assertEqual(request["output"]["response_code"], 400)
            self.assertEqual(
                request["output"]["response_body"]["errors"]["error"][0]["error-type"], "protocol"
            )
            self.assertEqual(
                request["output"]["response_body"]["errors"]["error"][0]["error-message"],
                "Error parsing input: com.google.common.util.concurrent.UncheckedExecutionException: "
                "java.lang.IllegalStateException: Schema node with name prefix was not found under "
                "(http://frinx.openconfig.net/yang/interfaces?revision=2016-12-22)config.",
            )
            self.assertEqual(
                request["output"]["response_body"]["errors"]["error"][0]["error-tag"],
                "malformed-message",
            )


class TestDeleteStructuredData(unittest.TestCase):
    def test_delete_structured_data_with_device(self):
        with patch("frinx_conductor_workers.uniconfig_worker.requests.delete") as mock:
            mock.return_value = MockResponse(bytes(json.dumps({}), encoding="utf-8"), 204, "")
            request = frinx_conductor_workers.uniconfig_worker.delete_structured_data(
                {
                    "inputData": {
                        "device_id": "xr5",
                        "uri": "/frinx-openconfig-interfaces:interfaces/interface=Loopback01",
                    }
                }
            )
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["response_code"], 204)
            self.assertEqual(request["output"]["response_body"], {})

    def test_delete_structured_data_with_bad_template(self):
        with patch("frinx_conductor_workers.uniconfig_worker.requests.delete") as mock:
            mock.return_value = MockResponse(
                bytes(json.dumps(bad_request_response), encoding="utf-8"), 404, ""
            )
            request = frinx_conductor_workers.uniconfig_worker.delete_structured_data(
                {
                    "inputData": {
                        "device_id": "xr5",
                        "uri": "/frinx-openconfig-interfaces:interfaces/interface=Loopback01",
                    }
                }
            )

            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["response_code"], 404)
            self.assertEqual(
                request["output"]["response_body"]["errors"]["error"][0]["error-type"], "protocol"
            )
            self.assertEqual(
                request["output"]["response_body"]["errors"]["error"][0]["error-message"],
                "Request could not be completed because the relevant data model content does not exist",
            )
            self.assertEqual(
                request["output"]["response_body"]["errors"]["error"][0]["error-tag"],
                "data-missing",
            )


class TestCommit(unittest.TestCase):
    def test_commit_with_existing_devices(self):
        with patch("frinx_conductor_workers.uniconfig_worker.requests.post") as mock:
            mock.return_value = MockResponse(
                bytes(json.dumps(commit_output), encoding="utf-8"), 200, ""
            )
            request = frinx_conductor_workers.uniconfig_worker.commit(
                {"inputData": {"devices": "xr5, xr6"}}
            )
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["responses"][0]["response_code"], 200)
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["overall-status"],
                "complete",
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][0]["node-id"],
                "xr5",
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][0]["configuration-status"],
                "complete",
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][1]["node-id"],
                "xr6",
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][1]["configuration-status"],
                "complete",
            )

    def test_commit_with_non_existing_device(self):
        try:
            frinx_conductor_workers.uniconfig_worker.commit({"inputData": {"devices": ""}})
        except Exception:
            return
        self.assertFalse("Calling RPC with empty device list is not allowed")


class TestDryRun(unittest.TestCase):
    def test_dry_run_with_existing_devices(self):
        with patch("frinx_conductor_workers.uniconfig_worker.requests.post") as mock:
            mock.return_value = MockResponse(
                bytes(json.dumps(dry_run_output), encoding="utf-8"), 200, ""
            )
            request = frinx_conductor_workers.uniconfig_worker.dryrun_commit(
                {"inputData": {"devices": "xr5"}}
            )
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["responses"][0]["response_code"], 200)
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["overall-status"],
                "complete",
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][0]["node-id"],
                "xr5",
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][0]["configuration-status"],
                "complete",
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][0]["configuration"],
                "2019-09-13T08:37:28.331: configure terminal\n"
                "2019-09-13T08:37:28.536: interface GigabitEthernet0/0/0/1\n"
                "shutdown\nroot\n\n"
                "2019-09-13T08:37:28.536: commit\n2019-09-13T08:37:28.536: end\n",
            )

    def test_dry_run_with_non_existing_device(self):
        try:
            frinx_conductor_workers.uniconfig_worker.dryrun_commit({"inputData": {"devices": ""}})
        except Exception:
            return
        self.assertFalse("Calling RPC with empty device list is not allowed")


class TestCalculateDiff(unittest.TestCase):
    def test_calculate_diff_with_existing_devices(self):
        with patch("frinx_conductor_workers.uniconfig_worker.requests.post") as mock:
            mock.return_value = MockResponse(
                bytes(json.dumps(calculate_diff_output), encoding="utf-8"), 200, ""
            )
            request = frinx_conductor_workers.uniconfig_worker.calc_diff(
                {"inputData": {"devices": "xr5"}}
            )
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["responses"][0]["response_code"], 200)
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["overall-status"],
                "complete",
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][0]["node-id"],
                "xr5",
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][0]["updated-data"][0]["path"],
                "network-topology:network-topology/topology=uniconfig/"
                "node=xr5/frinx-uniconfig-topology:configuration/"
                "frinx-openconfig-interfaces:interfaces/"
                "interface=GigabitEthernet0%2F0%2F0%2F0/config",
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][0]["updated-data"][0]["data-actual"],
                '{\n  "frinx-openconfig-interfaces:config": {\n'
                '    "type": "iana-if-type:ethernetCsmacd",\n'
                '    "enabled": false,\n'
                '    "name": "GigabitEthernet0/0/0/0"\n  }\n}',
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][0]["updated-data"][0]["data-intended"],
                '{\n  "frinx-openconfig-interfaces:config": {\n'
                '    "type": "iana-if-type:ethernetCsmacd",\n'
                '    "enabled": false,\n'
                '    "name": "GigabitEthernet0/0/0/0dfhdfghd"\n  }\n}',
            )

    def test_calculate_diff_with_non_existing_device(self):
        try:
            frinx_conductor_workers.uniconfig_worker.calc_diff({"inputData": {"devices": ""}})
        except Exception:
            return
        self.assertFalse("Calling RPC with empty device list is not allowed")


class TestSyncFromNetwork(unittest.TestCase):
    def test_sync_from_network_with_existing_devices(self):
        with patch("frinx_conductor_workers.uniconfig_worker.requests.post") as mock:
            mock.return_value = MockResponse(
                bytes(json.dumps(RPC_output_multiple_devices), encoding="utf-8"), 200, ""
            )
            request = frinx_conductor_workers.uniconfig_worker.sync_from_network(
                {"inputData": {"devices": "xr5, xr6"}}
            )
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["responses"][0]["response_code"], 200)
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["overall-status"],
                "complete",
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][0]["node-id"],
                "xr5",
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][0]["status"],
                "complete",
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][1]["node-id"],
                "xr6",
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][1]["status"],
                "complete",
            )

    def test_sync_from_network_with_non_existing_device(self):
        try:
            frinx_conductor_workers.uniconfig_worker.sync_from_network(
                {"inputData": {"devices": ""}}
            )
        except Exception:
            return
        self.assertFalse("Calling RPC with empty device list is not allowed")


class TestReplaceConfigWithOper(unittest.TestCase):
    def test_replace_config_with_oper_with_existing_devices(self):
        with patch("frinx_conductor_workers.uniconfig_worker.requests.post") as mock:
            mock.return_value = MockResponse(
                bytes(json.dumps(RPC_output_multiple_devices), encoding="utf-8"), 200, ""
            )
            request = frinx_conductor_workers.uniconfig_worker.replace_config_with_oper(
                {"inputData": {"devices": "xr5, xr6"}}
            )
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["responses"][0]["response_code"], 200)
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["overall-status"],
                "complete",
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][0]["node-id"],
                "xr5",
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][0]["status"],
                "complete",
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][1]["node-id"],
                "xr6",
            )
            self.assertEqual(
                request["output"]["responses"][0]["response_body"]["output"]["node-results"][
                    "node-result"
                ][1]["status"],
                "complete",
            )

    def test_replace_config_with_oper_with_non_existing_device(self):
        try:
            frinx_conductor_workers.uniconfig_worker.replace_config_with_oper(
                {"inputData": {"devices": ""}}
            )
        except Exception:
            return
        self.assertFalse("Calling RPC with empty device list is not allowed")


class TestUtilityFunction(unittest.TestCase):
    def test_escape(self):
        uri = frinx_conductor_workers.uniconfig_worker.apply_functions(
            "interfaces/interface=escape(GigabitEthernet0/0/0/0)/abcd/escape(a/b)"
        )
        assert uri == "interfaces/interface=GigabitEthernet0%2F0%2F0%2F0/abcd/a%2Fb"
        uri = frinx_conductor_workers.uniconfig_worker.apply_functions(None)
        assert uri is None
        uri = frinx_conductor_workers.uniconfig_worker.apply_functions("")
        assert uri is ""


if __name__ == "__main__":
    unittest.main()
