import unittest

from frinx.common.workflow import task
from frinx.workers.inventory.inventory_worker import Inventory
from frinx.workflows.inventory.inventory_workflows import InventoryWorkflows


class TestTaskGenerator(unittest.TestCase):
    def test_decision_task(self):
        test_task = task.DecisionTask(
            name="decision",
            task_reference_name="decision",
            decision_cases={"true": [task.HumanTask(name="human", task_reference_name="human")]},
            default_case=[
                task.TerminateTask(
                    name="terminate",
                    task_reference_name="terminate",
                    input_parameters=task.TerminateTaskInputParameters(
                        termination_status=task.WorkflowStatus.FAILED
                    ),
                )
            ],
            input_parameters=task.DecisionTaskInputParameters(status="${workflow.input.status}"),
            case_expression="$.status === 'true' ? 'true' : 'False'",
        ).dict(exclude_none=True)

        test_mock = {
            "name": "decision",
            "task_reference_name": "decision",
            "type": "DECISION",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [
                {
                    "name": "terminate",
                    "task_reference_name": "terminate",
                    "type": "TERMINATE",
                    "start_delay": 0,
                    "optional": False,
                    "async_complete": False,
                    "default_case": [],
                    "input_parameters": {"termination_status": "FAILED"},
                }
            ],
            "input_parameters": {"status": "${workflow.input.status}"},
            "case_expression": "$.status === 'true' ? 'true' : 'False'",
            "decision_cases": {
                "true": [
                    {
                        "name": "human",
                        "task_reference_name": "human",
                        "type": "HUMAN",
                        "start_delay": 0,
                        "optional": False,
                        "async_complete": False,
                        "default_case": [],
                        "input_parameters": {},
                    }
                ]
            },
        }
        self.assertDictEqual(test_task, test_mock)

    def test_decision_case_value_task(self):
        test_task = task.DecisionCaseValueTask(
            name="decision",
            task_reference_name="decision",
            decision_cases={"true": [task.HumanTask(name="human", task_reference_name="human")]},
            default_case=[
                task.TerminateTask(
                    name="terminate",
                    task_reference_name="terminate",
                    input_parameters=task.TerminateTaskInputParameters(
                        termination_status=task.WorkflowStatus.FAILED
                    ),
                )
            ],
            input_parameters=task.DecisionCaseValueTaskInputParameters(
                case_value_param="${workflow.input.status}"
            ),
        ).dict(exclude_none=True)

        test_mock = {
            "name": "decision",
            "task_reference_name": "decision",
            "type": "DECISION",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [
                {
                    "name": "terminate",
                    "task_reference_name": "terminate",
                    "type": "TERMINATE",
                    "start_delay": 0,
                    "optional": False,
                    "async_complete": False,
                    "default_case": [],
                    "input_parameters": {"termination_status": "FAILED"},
                }
            ],
            "input_parameters": {"case_value_param": "${workflow.input.status}"},
            "case_value_param": "case_value_param",
            "decision_cases": {
                "true": [
                    {
                        "name": "human",
                        "task_reference_name": "human",
                        "type": "HUMAN",
                        "start_delay": 0,
                        "optional": False,
                        "async_complete": False,
                        "default_case": [],
                        "input_parameters": {},
                    }
                ]
            },
        }

        self.assertDictEqual(test_task, test_mock)

    def test_do_while_task(self):
        loop_tasks = task.WaitDurationTask(
            name="wait",
            task_reference_name="wait",
            input_parameters=task.WaitDurationTaskInputParameters(duration="1 seconds"),
        )

        test_task = task.DoWhileTask(
            name="do_while",
            task_reference_name="LoopTask",
            loop_condition="if ( $.LoopTask['iteration'] < $.value ) { true; } else { false; }",
            loop_over=[loop_tasks],
            input_parameters={"value": "value"},
        ).dict(exclude_none=True)

        test_mock = {
            "name": "do_while",
            "task_reference_name": "LoopTask",
            "type": "DO_WHILE",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {"value": "value"},
            "loop_condition": "if ( $.LoopTask['iteration'] < $.value ) { true; } else { false; }",
            "loop_over": [
                {
                    "name": "wait",
                    "task_reference_name": "wait",
                    "type": "WAIT",
                    "start_delay": 0,
                    "optional": False,
                    "async_complete": False,
                    "default_case": [],
                    "input_parameters": {"duration": "1 seconds"},
                }
            ],
            "evaluator_type": "DoWhileEvaluatorType.JAVASCRIPT",
        }

        self.assertDictEqual(test_task, test_mock)

    def test_dyn_fork_arrays_def_task(self):
        task_inputs = InventoryWorkflows.InstallDeviceByName.WorkflowInput()

        fork_inputs = [
            {task_inputs.device_name.name: "IOS01"},
            {task_inputs.device_name.name: "IOS02"},
            {task_inputs.device_name.name: "IOS02"},
        ]

        test_task = task.DynamicForkTask(
            name="dyn_fork",
            task_reference_name="dyn_fork",
            input_parameters=task.DynamicForkArraysTaskFromDefInputParameters(
                fork_task_name=InventoryWorkflows.InstallDeviceByName, fork_task_inputs=fork_inputs
            ),
        ).dict(exclude_none=True)

        test_mock = {
            "name": "dyn_fork",
            "task_reference_name": "dyn_fork",
            "type": "FORK_JOIN_DYNAMIC",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {
                "fork_task_name": "Install_device_by_name",
                "fork_task_inputs": [
                    {"device_name": "IOS01"},
                    {"device_name": "IOS02"},
                    {"device_name": "IOS02"},
                ],
            },
            "dynamic_fork_tasks_param": "dynamicTasks",
            "dynamic_fork_tasks_input_param_name": "dynamicTasksInput",
        }

        self.assertDictEqual(test_task, test_mock)

    def test_dyn_fork_arrays_task(self):
        task_inputs = InventoryWorkflows.InstallDeviceByName.WorkflowInput()

        fork_inputs = [
            {task_inputs.device_name.name: "IOS01"},
            {task_inputs.device_name.name: "IOS02"},
            {task_inputs.device_name.name: "IOS02"},
        ]

        input_parameters = task.DynamicForkArraysTaskInputParameters(
            fork_task_name="Install_device_by_name", fork_task_inputs=fork_inputs
        )

        test_task = task.DynamicForkTask(
            name="dyn_fork", task_reference_name="dyn_fork", input_parameters=input_parameters
        ).dict(exclude_none=True)

        test_mock = {
            "name": "dyn_fork",
            "task_reference_name": "dyn_fork",
            "type": "FORK_JOIN_DYNAMIC",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {
                "fork_task_name": "Install_device_by_name",
                "fork_task_inputs": [
                    {"device_name": "IOS01"},
                    {"device_name": "IOS02"},
                    {"device_name": "IOS02"},
                ],
            },
            "dynamic_fork_tasks_param": "dynamicTasks",
            "dynamic_fork_tasks_input_param_name": "dynamicTasksInput",
        }

        self.assertDictEqual(test_task, test_mock)

    def test_dyn_fork_def_task(self):
        input_parameters = task.DynamicForkTaskFromDefInputParameters(
            dynamic_tasks=InventoryWorkflows.InstallDeviceByName,
            dynamic_tasks_input="${workflow.input.device_name}",
        )

        test_task = task.DynamicForkTask(
            name="dyn_fork", task_reference_name="dyn_fork", input_parameters=input_parameters
        ).dict(exclude_none=True)

        test_mock = {
            "name": "dyn_fork",
            "task_reference_name": "dyn_fork",
            "type": "FORK_JOIN_DYNAMIC",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {
                "dynamic_tasks": "Install_device_by_name",
                "dynamic_tasks_input": "${workflow.input.device_name}",
            },
            "dynamic_fork_tasks_param": "dynamicTasks",
            "dynamic_fork_tasks_input_param_name": "dynamicTasksInput",
        }

        self.assertDictEqual(test_task, test_mock)

    def test_dyn_fork_task(self):
        input_parameters = task.DynamicForkTaskInputParameters(
            dynamic_tasks="Install_device_by_name",
            dynamic_tasks_input="${workflow.input.device_name}",
        )

        test_task = task.DynamicForkTask(
            name="dyn_fork", task_reference_name="dyn_fork", input_parameters=input_parameters
        ).dict(exclude_none=True)

        test_mock = {
            "name": "dyn_fork",
            "task_reference_name": "dyn_fork",
            "type": "FORK_JOIN_DYNAMIC",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {
                "dynamic_tasks": "Install_device_by_name",
                "dynamic_tasks_input": "${workflow.input.device_name}",
            },
            "dynamic_fork_tasks_param": "dynamicTasks",
            "dynamic_fork_tasks_input_param_name": "dynamicTasksInput",
        }

        self.assertDictEqual(test_task, test_mock)

    def test_event_task(self):
        test_task = task.EventTask(
            name="Event",
            task_reference_name="event_a",
            sink="conductor:Wait_task",
            async_complete=False,
        ).dict(exclude_none=True)

        test_mock = {
            "name": "Event",
            "task_reference_name": "event_a",
            "type": "EVENT",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {},
            "sink": "conductor:Wait_task",
        }

        self.assertDictEqual(test_task, test_mock)

    def test_exclusive_join_task(self):
        test_task = task.ExclusiveJoinTask(
            name="exclusive_join",
            task_reference_name="exclusive_join",
            join_on=["wf1", "wf2"],
            optional=True,
            start_delay=30,
        ).dict(exclude_none=True)

        test_mock = {
            "name": "exclusive_join",
            "task_reference_name": "exclusive_join",
            "type": "EXCLUSIVE_JOIN",
            "start_delay": 30,
            "optional": True,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {},
            "join_on": ["wf1", "wf2"],
        }

        self.assertDictEqual(test_task, test_mock)

    def test_fork_task(self):
        fork_tasks_a = []
        fork_tasks_b = []

        fork_tasks_a.append(task.SimpleTask(
            name=Inventory.InventoryAddDevice,
            task_reference_name="add_device_cli",
            input_parameters=task.SimpleTaskInputParameters(
                device_name="IOS01", zone="uniconfig", service_state="IN_SERVICE", mount_body="body"
            ),
        ))

        fork_tasks_a.append(task.SimpleTask(
            name=Inventory.InventoryInstallDeviceByName,
            task_reference_name="install_device_cli",
            input_parameters=task.SimpleTaskInputParameters(
                device_name="IOS01"
            ),
        ))

        fork_tasks_b.append(task.SimpleTask(
            name=Inventory.InventoryAddDevice,
            task_reference_name="add_device",
            input_parameters=task.SimpleTaskInputParameters(
                device_name="NTF01", zone="uniconfig", service_state="IN_SERVICE", mount_body="body"
            ),
        ))

        fork_tasks_b.append(task.SimpleTask(
            name=Inventory.InventoryInstallDeviceByName,
            task_reference_name="install_device_netconf",
            input_parameters=task.SimpleTaskInputParameters(
                device_name="NTF01"
            ),
        ))

        test_task = task.ForkTask(
            name="fork",
            task_reference_name="fork",
            fork_tasks=[
                fork_tasks_a,
                fork_tasks_b
            ]
        ).dict(exclude_none=True)

        test_mock = {
            'name': 'fork',
            'task_reference_name': 'fork',
            'type': 'FORK_JOIN',
            'start_delay': 0,
            'optional': False,
            'async_complete': False,
            'default_case': [],
            'input_parameters': {},
            'fork_tasks': [
                [
                    {
                        'name': 'INVENTORY_add_device',
                        'task_reference_name': 'add_device_cli',
                        'type': "SIMPLE",
                        'start_delay': 0,
                        'optional': False,
                        'async_complete': False,
                        'default_case': [],
                        'input_parameters': {
                            'zone': 'uniconfig',
                            'device_name': 'IOS01',
                            'mount_body': 'body',
                            'service_state': 'IN_SERVICE'
                        }
                    },
                    {
                        'name': 'INVENTORY_install_device_by_name',
                        'task_reference_name': 'install_device_cli',
                        'type': "SIMPLE",
                        'start_delay': 0,
                        'optional': False,
                        'async_complete': False,
                        'default_case': [],
                        'input_parameters': {
                            'device_name': 'IOS01'
                        }
                    }
                ],
                [
                    {
                        'name': 'INVENTORY_add_device',
                        'task_reference_name': 'add_device',
                        'type': "SIMPLE",
                        'start_delay': 0,
                        'optional': False,
                        'async_complete': False,
                        'default_case': [],
                        'input_parameters': {
                            'zone': 'uniconfig',
                            'device_name': 'NTF01',
                            'mount_body': 'body',
                            'service_state': 'IN_SERVICE'
                        }
                    },
                    {
                        'name': 'INVENTORY_install_device_by_name',
                        'task_reference_name': 'install_device_netconf',
                        'type': "SIMPLE",
                        'start_delay': 0,
                        'optional': False,
                        'async_complete': False,
                        'default_case': [],
                        'input_parameters': {
                            'device_name': 'NTF01'
                        }
                    }
                ]
            ]
        }

        self.assertDictEqual(test_task, test_mock)

    def test_human_task(self):
        test_task = task.HumanTask(name="human", task_reference_name="human").dict(
            exclude_none=True
        )

        test_mock = {
            "name": "human",
            "task_reference_name": "human",
            "type": "HUMAN",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {},
        }

        self.assertDictEqual(test_task, test_mock)

    def test_inline_task(self):
        test_task = task.InlineTask(
            name="inline",
            task_reference_name="inline",
            input_parameters=task.InlineTaskInputParameters(
                expression='if ($.value){return {"result": true}} else { return {"result": false}}',
                value="${workflow.variables.test}",
            ),
        ).dict(exclude_none=True)

        test_mock = {
            "name": "inline",
            "task_reference_name": "inline",
            "type": "INLINE",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {
                "evaluator_type": "javascript",
                "expression": 'function e() { if ($.value){return {"result": true}} else { return {"result": false}} } e();',
                "value": "${workflow.variables.test}",
            },
        }

        self.assertDictEqual(test_task, test_mock)

    def test_inline_func_task(self):
        test_task = task.InlineTask(
            name="inline",
            task_reference_name="inline",
            input_parameters=task.InlineTaskInputParameters(
                expression='function e() { if ($.value){return {"result": true}} else { return {"result": false}} } e();',
                value="${workflow.variables.test}",
            ),
        ).dict(exclude_none=True)

        test_mock = {
            "name": "inline",
            "task_reference_name": "inline",
            "type": "INLINE",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {
                "evaluator_type": "javascript",
                "expression": 'function e() { if ($.value){return {"result": true}} else { return {"result": false}} } e();',
                "value": "${workflow.variables.test}",
            },
        }

        self.assertDictEqual(test_task, test_mock)

    def test_join_task(self):
        test_task = task.JoinTask(name="join", task_reference_name="join").dict(exclude_none=True)

        test_mock = {
            "name": "join",
            "task_reference_name": "join",
            "type": "JOIN",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {},
            "join_on": [],
        }

        self.assertDictEqual(test_task, test_mock)

    def test_json_jq_task(self):
        test_task = task.JsonJqTask(
            name="json_jq",
            task_reference_name="json_jq",
            input_parameters=task.JsonJqTaskInputParameters(
                query_expression="{ key3: (.key1.value1) }", key_1={"value1": ["a", "b"]}
            ),
        ).dict(exclude_none=True)

        test_mock = {
            "name": "json_jq",
            "task_reference_name": "json_jq",
            "type": "JSON_JQ_TRANSFORM",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {
                "query_expression": "{ key3: (.key1.value1) }",
                "key_1": {"value1": ["a", "b"]},
            },
        }

        self.assertDictEqual(test_task, test_mock)

    def test_set_variable_task(self):
        test_task = task.SetVariableTask(
            name="var",
            task_reference_name="var",
            input_parameters=task.SetVariableTaskInputParameters(env="frinx"),
        ).dict(exclude_none=True)

        test_mock = {
            "name": "var",
            "task_reference_name": "var",
            "type": "SET_VARIABLE",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {"env": "frinx"},
        }

        self.assertDictEqual(test_task, test_mock)

    def test_simple_task(self):
        test_task = task.SimpleTask(
            name=Inventory.InventoryAddDevice,
            task_reference_name="test",
            input_parameters=task.SimpleTaskInputParameters(
                device_name="IOS01", zone="uniconfig", service_state="IN_SERVICE", mount_body="body"
            ),
        ).dict(exclude_none=True)

        test_mock = {
            "name": "INVENTORY_add_device",
            "task_reference_name": "test",
            "type": "SIMPLE",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {
                "device_name": "IOS01",
                "zone": "uniconfig",
                "mount_body": "body",
                "service_state": "IN_SERVICE",
            },
        }

        self.assertDictEqual(test_task, test_mock)

    def test_start_workflow_from_def_task(self):
        workflow_input_parameters = {
            InventoryWorkflows.InstallDeviceByName.WorkflowInput().device_name.name: "IOS01"
        }

        task_inputs = task.StartWorkflowTaskInputParameters(
            start_workflow=task.StartWorkflowTaskFromDefInputParameters(
                workflow=InventoryWorkflows.InstallDeviceByName, input=workflow_input_parameters
            )
        )

        test_task = task.StartWorkflowTask(
            name="Install_device_by_name", task_reference_name="start", input_parameters=task_inputs
        ).dict(exclude_none=True)

        test_mock = {
            "name": "Install_device_by_name",
            "task_reference_name": "start",
            "type": "START_WORKFLOW",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {
                "start_workflow": {
                    "name": "Install_device_by_name",
                    "version": 1,
                    "input": {"device_name": "IOS01"},
                }
            },
        }

        self.assertDictEqual(test_task, test_mock)

    def test_start_workflow_plain_task(self):
        workflow_input_parameters = {
            InventoryWorkflows.InstallDeviceByName.WorkflowInput().device_name.name: "IOS01"
        }

        task_inputs = task.StartWorkflowTaskInputParameters(
            start_workflow=task.StartWorkflowTaskPlainInputParameters(
                name="Install_device_by_name", version=1, input=workflow_input_parameters
            )
        )

        test_task = task.StartWorkflowTask(
            name="Install_device_by_name", task_reference_name="start", input_parameters=task_inputs
        ).dict(exclude_none=True)

        test_mock = {
            "name": "Install_device_by_name",
            "task_reference_name": "start",
            "type": "START_WORKFLOW",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {
                "start_workflow": {
                    "name": "Install_device_by_name",
                    "version": 1,
                    "input": {"device_name": "IOS01"},
                }
            },
        }

        self.assertDictEqual(test_task, test_mock)

    def test_sub_workflow_task(self):
        sub_workflow_param = task.SubWorkflowParam(
            name=InventoryWorkflows.AddDeviceToInventory.__name__, version=1
        )

        workflows_inputs = InventoryWorkflows.AddDeviceToInventory.WorkflowInput()

        sub_workflow_input = {}
        sub_workflow_input.setdefault(workflows_inputs.device_name.name, "IOS01")
        sub_workflow_input.setdefault(workflows_inputs.zone.name, "uniconfig")

        test_task = task.SubWorkflowTask(
            name="subworkflow",
            task_reference_name="subworkflow",
            sub_workflow_param=sub_workflow_param,
            input_parameters=task.SubWorkflowInputParameters(**sub_workflow_input),
        ).dict(exclude_none=True)

        test_mock = {
            "name": "subworkflow",
            "task_reference_name": "subworkflow",
            "type": "SUB_WORKFLOW",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {"device_name": "IOS01", "zone": "uniconfig"},
            "sub_workflow_param": {"name": "AddDeviceToInventory", "version": 1},
        }

        self.assertDictEqual(test_task, test_mock)

    def test_switch_value_param_task(self):
        test_task = task.SwitchTask(
            name="switch",
            task_reference_name="switch",
            decision_cases={
                "true": [
                    task.WaitDurationTask(
                        name="wait",
                        task_reference_name="wait1",
                        input_parameters=task.WaitDurationTaskInputParameters(
                            duration="10 seconds"
                        ),
                    )
                ]
            },
            default_case=[
                task.WaitDurationTask(
                    name="wait",
                    task_reference_name="wait2",
                    input_parameters=task.WaitDurationTaskInputParameters(duration="10 seconds"),
                )
            ],
            expression="switch_case_value",
            evaluator_type=task.SwitchEvaluatorType.VALUE_PARAM,
            input_parameters=task.SwitchTaskValueParamInputParameters(
                switch_case_value="${workflow.input.value}"
            ),
        ).dict(exclude_none=True)

        test_mock = {
            "name": "switch",
            "task_reference_name": "switch",
            "type": "SWITCH",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [
                {
                    "name": "wait",
                    "task_reference_name": "wait2",
                    "type": "WAIT",
                    "start_delay": 0,
                    "optional": False,
                    "async_complete": False,
                    "default_case": [],
                    "input_parameters": {"duration": "10 seconds"},
                }
            ],
            "input_parameters": {"switch_case_value": "${workflow.input.value}"},
            "decision_cases": {
                "true": [
                    {
                        "name": "wait",
                        "task_reference_name": "wait1",
                        "type": "WAIT",
                        "start_delay": 0,
                        "optional": False,
                        "async_complete": False,
                        "default_case": [],
                        "input_parameters": {"duration": "10 seconds"},
                    }
                ]
            },
            "evaluator_type": "value-param",
            "expression": "switch_case_value",
        }

        self.assertDictEqual(test_task, test_mock)

    def test_switch_javascript_task(self):
        test_task = task.SwitchTask(
            name="switch",
            task_reference_name="switch",
            decision_cases={
                "true": [
                    task.WaitDurationTask(
                        name="wait",
                        task_reference_name="wait1",
                        input_parameters=task.WaitDurationTaskInputParameters(
                            duration="10 seconds"
                        ),
                    )
                ]
            },
            default_case=[
                task.WaitDurationTask(
                    name="wait",
                    task_reference_name="wait2",
                    input_parameters=task.WaitDurationTaskInputParameters(duration="10 seconds"),
                )
            ],
            expression="$.inputValue == 'true' ? 'true' : 'false'",
            evaluator_type=task.SwitchEvaluatorType.JAVASCRIPT,
            input_parameters=task.SwitchTaskInputParameters(input_value="${workflow.input.value}"),
        ).dict(exclude_none=True)

        test_mock = {
            "name": "switch",
            "task_reference_name": "switch",
            "type": "SWITCH",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [
                {
                    "name": "wait",
                    "task_reference_name": "wait2",
                    "type": "WAIT",
                    "start_delay": 0,
                    "optional": False,
                    "async_complete": False,
                    "default_case": [],
                    "input_parameters": {"duration": "10 seconds"},
                }
            ],
            "input_parameters": {"input_value": "${workflow.input.value}"},
            "decision_cases": {
                "true": [
                    {
                        "name": "wait",
                        "task_reference_name": "wait1",
                        "type": "WAIT",
                        "start_delay": 0,
                        "optional": False,
                        "async_complete": False,
                        "default_case": [],
                        "input_parameters": {"duration": "10 seconds"},
                    }
                ]
            },
            "evaluator_type": "javascript",
            "expression": "$.inputValue == 'true' ? 'true' : 'false'",
        }

        self.assertDictEqual(test_task, test_mock)

    def test_terminate_task(self):
        test_task = task.TerminateTask(
            name="terminate",
            task_reference_name="terminate",
            input_parameters=task.TerminateTaskInputParameters(
                termination_status=task.WorkflowStatus.COMPLETED,
                workflow_output={"output": "COMPLETED"},
            ),
        ).dict(exclude_none=True)

        test_mock = {
            "name": "terminate",
            "task_reference_name": "terminate",
            "type": "TERMINATE",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {
                "termination_status": "COMPLETED",
                "workflow_output": {"output": "COMPLETED"},
            },
        }

        self.assertDictEqual(test_task, test_mock)

    def test_wait_duration_task(self):
        test_task = task.WaitDurationTask(
            name="WAIT",
            task_reference_name="WAIT",
            input_parameters=task.WaitDurationTaskInputParameters(duration="10 seconds"),
        ).dict(exclude_none=True)

        test_mock = {
            "name": "WAIT",
            "task_reference_name": "WAIT",
            "type": "WAIT",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {"duration": "10 seconds"},
        }

        self.assertDictEqual(test_task, test_mock)

    def test_wait_until_task(self):
        test_task = task.WaitUntilTask(
            name="WAIT_UNTIL",
            task_reference_name="WAIT_UNTIL",
            input_parameters=task.WaitUntilTaskInputParameters(until="2022-12-25 09:00 PST"),
        ).dict(exclude_none=True)

        test_mock = {
            "name": "WAIT_UNTIL",
            "task_reference_name": "WAIT_UNTIL",
            "type": "WAIT",
            "start_delay": 0,
            "optional": False,
            "async_complete": False,
            "default_case": [],
            "input_parameters": {"until": "2022-12-25 09:00 PST"},
        }

        self.assertDictEqual(test_task, test_mock)


if __name__ == "__main__":
    unittest.main()
