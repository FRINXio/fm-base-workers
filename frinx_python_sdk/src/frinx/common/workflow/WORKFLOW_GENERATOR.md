### DECISION TASK

```python
self.tasks.append(DecisionTask(
    name="decision",
    task_reference_name="decision",
    decision_cases={
        "true": [
            HumanTask(
                name="human",
                task_reference_name="human"
            )
        ],
    },
    default_case=[
        TerminateTask(
            name="terminate",
            task_reference_name="terminate",
            input_parameters=TerminateTaskInputParameters(
                termination_status=WorkflowStatus.FAILED
            ))
    ],
    input_parameters=DecisionTaskInputParameters(
        status="${workflow.input.status}"
    ),
    case_expression="$.status === 'true' ? 'true' : 'false'"
))
```

#### Case-Value decision task

```python
self.tasks.append(DecisionCaseValueTask(
    name="decision",
    task_reference_name="decision",
    decision_cases={
        "true": [
            HumanTask(
                name="human",
                task_reference_name="human"
            )
        ],
    },
    default_case=[
        TerminateTask(
            name="terminate",
            task_reference_name="terminate",
            input_parameters=TerminateTaskInputParameters(
                termination_status=WorkflowStatus.FAILED
            ))
    ],
    input_parameters=DecisionCaseValueTaskInputParameters(
        case_value_param="${workflow.input.status}"
    ),
))
```

### DO_WHILE TASK

```python
loop_tasks = WaitDurationTask(
    name="wait",
    task_reference_name="wait",
    input_parameters=WaitDurationTaskInputParameters(
        duration="1 seconds"
    )
)

self.tasks.append(DoWhileTask(
    name="do_while",
    task_reference_name="LoopTask",
    loop_condition="if ( $.LoopTask['iteration'] < $.value ) { true; } else { false; }",
    loop_over=[
        loop_tasks
    ],
    input_parameters={
        "value": workflow_inputs.value.wf_input
    }
))
```

### DYNAMIC_FORK TASK

```python
task_inputs = InventoryWorkflows.InstallDeviceByName.WorkflowInput()

fork_inputs = [
    {
        task_inputs.device_name.name: "IOS01"
    },
    {
        task_inputs.device_name.name: "IOS02"
    },
    {
        task_inputs.device_name.name: "IOS02"
    }
]

self.tasks.append(DynamicForkTask(
    name="dyn_fork",
    task_reference_name="dyn_fork",
    input_parameters=DynamicForkArraysTaskFromDefInputParameters(
        fork_task_name=InventoryWorkflows.InstallDeviceByName,
        fork_task_inputs=fork_inputs
    ),
))

self.tasks.append(JoinTask(
    name="join",
    task_reference_name="join"
))
```

```python
self.tasks.append(DynamicForkTask(
    name="dyn_fork",
    task_reference_name="dyn_fork",
    input_parameters=DynamicForkTaskFromDefInputParameters(
        dynamic_tasks=InventoryWorkflows.InstallDeviceByName,
        dynamic_tasks_input=workflow_inputs.device_name.wf_input
    ),
))

self.tasks.append(JoinTask(
    name="join",
    task_reference_name="join"
))

```

```python
task_inputs = InventoryWorkflows.InstallDeviceByName.WorkflowInput()

fork_inputs = [
    {
        task_inputs.device_name.name: "IOS01"
    },
    {
        task_inputs.device_name.name: "IOS02"
    },
    {
        task_inputs.device_name.name: "IOS02"
    }
]

input_parameters = DynamicForkArraysTaskInputParameters(
    fork_task_name="Install_device_by_name",
    fork_task_inputs=fork_inputs
)

self.tasks.append(DynamicForkTask(
    name="dyn_fork",
    task_reference_name="dyn_fork",
    input_parameters=input_parameters
))
```

```python
self.tasks.append(DynamicForkTask(
    name="dyn_fork",
    task_reference_name="dyn_fork",
    input_parameters=DynamicForkTaskInputParameters(
        dynamic_tasks_input="Install_device_by_name",
        dynamic_tasks=[
            {
                task_inputs.device_name.name: "IOS01"
            },
            {
                task_inputs.device_name.name: "IOS02"
            },
            {
                task_inputs.device_name.name: "IOS02"
            }
        ]
    )
))
```

### EVENT TASK

```python
self.tasks.append(EventTask(
    name="Event",
    task_reference_name="event_a",
    sink="conductor:Wait_task",
    async_complete=False
))
```

### EXCLUSIVE_JOIN TASK

```python
self.tasks.append(ExclusiveJoinTask(
    name="exclusive_join",
    task_reference_name="exclusive_join",
))

```

or with defined join_on tasks: <br>
A list of task reference names that this JOIN task will wait for completion

```python
self.tasks.append(ExclusiveJoinTask(
    name="exclusive_join",
    task_reference_name="exclusive_join",
    join_on=["task1", "task2"]
))

```

### HUMAN TASK

```python
self.tasks.append(HumanTask(
    name="human",
    task_reference_name="human"
))
```

### INLINE TASK

```python
self.tasks.append(InlineTask(
    name="inline",
    task_reference_name="inline",
    input_parameters=InlineTaskInputParameters(
        expression='if ($.value){return {"result": true}} else { return {"result": false}}',
        value="${workflow.variables.test}"
    )))

```

INFO: expression wrapped into javascript function: <br>

```javascript
expression = "function e() { if ($.value){return {\"result\": true}} else { return {\"result\": false}} } e();"
```

### JOIN TASK

```python
self.tasks.append(JoinTask(
    name="join", 
    task_reference_name="join"
))
```

or with defined join_on tasks: <br>
A list of task reference names that this JOIN task will wait for completion

```python
self.tasks.append(JoinTask(
    name="join", 
    task_reference_name="join",
    join_on=["task1", "task2"]
))
```

### JSON_JQ_TRANSFORM TASK

```python
json_jq = JsonJqTask(
    name="json_jq",
    task_reference_name="json_jq",
    input_parameters=JsonJqTaskInputParameters(
        query_expression="{ key3: (.key1.value1 + .key2.value2) }",
        key_1={
            "value1": [
                "a",
                "b"
            ]
        },
        key2={
            "value2": [
                "c",
                "d"
            ]
        }
    )
)
self.tasks.append(json_jq)
```

### KAFKAPUBLISH TASK

TODO

### SET_VARIABLE TASK

```python
self.tasks.append(SetVariableTask(
    name="var",
    task_reference_name="var",
    input_parameters=SetVariableTaskInputParameters(
        env="frinx"
    )
))
```

### SIMPLE TASK

```python
self.tasks.append(
    SimpleTask(
        name=Inventory.InventoryAddDevice,
        task_reference_name="test",
        input_parameters=SimpleTaskInputParameters(
            device_name="IOS01",
            zone="uniconfig",
            service_state="aha",
            mount_body="body"
        )
    )
)
```

### START_WORKFLOW TASK

Start Workflow is an operator task used to start another workflow from an existing workflow. Unlike a sub-workflow task,
a start workflow task doesn’t create a relationship between the current workflow and the newly started workflow. That
means it doesn’t wait for the started workflow to get completed.

#### INPUT PARAMETERS

**start_workflow**:

* StartWorkflowTaskInputParameters : StartWorkflowTaskPlainInputParameters|StartWorkflowTaskFromDefInputParameters
* StartWorkflowTaskPlainInputParameters
* StartWorkflowTaskFromDefInputParameters

**input**:

```python
workflow_input_parameters = {
    InventoryWorkflows.InstallDeviceByName.WorkflowInput().device_name.name: "IOS01"
}

task_inputs = StartWorkflowTaskInputParameters(
    start_workflow=StartWorkflowTaskFromDefInputParameters(
        workflow=InventoryWorkflows.InstallDeviceByName,
        input=workflow_input_parameters
    )
)

install_workflow = StartWorkflowTask(
    name="Install_device_by_name",
    task_reference_name="start",
    input_parameters=task_inputs
)

self.tasks.append(install_workflow)
```

```python
workflow_input_parameters = {
    InventoryWorkflows.InstallDeviceByName.WorkflowInput().device_name.name: "IOS01"
}

task_inputs = StartWorkflowTaskInputParameters(
    start_workflow=StartWorkflowTaskFromDefInputParameters(
        workflow=InventoryWorkflows.InstallDeviceByName,
        input=workflow_input_parameters
    )
)

self.tasks.append(StartWorkflowTask(
    name="Install_device_by_name",
    task_reference_name="start",
    input_parameters=task_inputs
))
```

### SUBWORKFLOW TASK

```python
sub_workflow_param = SubWorkflowParam(
    name=InventoryWorkflows.AddDeviceToInventory.__name__,
    version=1
)

workflows_inputs = InventoryWorkflows.AddDeviceToInventory.WorkflowInput()

sub_workflow_input = {}
sub_workflow_input.setdefault(workflows_inputs.device_name.name, "IOS01")
sub_workflow_input.setdefault(workflows_inputs.zone.name, "uniconfig")

self.tasks.append(SubWorkflowTask(
    name="subworkflow",
    task_reference_name="subworkflow",
    sub_workflow_param=sub_workflow_param,
    input_parameters=SubWorkflowInputParameters(
    **sub_workflow_input
    )
))
```

SubWorkflowFromDefParam validate subworkflow and workflow inputs

```python
sub_workflow_param = SubWorkflowFromDefParam(
    name=InventoryWorkflows.AddDeviceToInventory
)

workflows_inputs = InventoryWorkflows.AddDeviceToInventory.WorkflowInput()

sub_workflow_input = {}
sub_workflow_input.setdefault(workflows_inputs.device_name.name, "IOS01")
sub_workflow_input.setdefault(workflows_inputs.zone.name, "uniconfig")

self.tasks.append(SubWorkflowTask(
    name="subworkflow",
    task_reference_name="subworkflow",
    sub_workflow_param=sub_workflow_param,
    input_parameters=SubWorkflowInputParameters(
    **sub_workflow_input
    )
))
```

### SWITCH TASK

#### INPUT PARAMETERS

* SwitchTaskValueParamInputParameters -> VALUE-PARAM
* SwitchTaskInputParameters -> JAVASCRIPT

VALUE-PARAM evaluator type

```python
switch = SwitchTask(
    name="switch",
    task_reference_name="switch",
    decision_cases={
        "true": [
            WaitDurationTask(
                name="wait",
                task_reference_name="wait1",
                input_parameters=WaitDurationTaskInputParameters(
                    duration="10 seconds"
                )
            )
        ]},
    default_case=[
        WaitDurationTask(
            name="wait",
            task_reference_name="wait2",
            input_parameters=WaitDurationTaskInputParameters(
                duration="10 seconds"
            )
        )
    ],
    expression="switch_case_value",
    evaluator_type=SwitchEvaluatorType.VALUE_PARAM,
    input_parameters=SwitchTaskValueParamInputParameters(
        switch_case_value="${workflow.input.value}"
    )
)
self.tasks.append(switch)
```

JAVASCRIPT evaluator type

```python
switch = SwitchTask(
    name="switch",
    task_reference_name="switch",
    decision_cases={
        "true": [
            WaitDurationTask(
                name="wait",
                task_reference_name="wait1",
                input_parameters=WaitDurationTaskInputParameters(
                    duration="10 seconds"
                )
            )
        ]},
    default_case=[
        WaitDurationTask(
            name="wait",
            task_reference_name="wait2",
            input_parameters=WaitDurationTaskInputParameters(
                duration="10 seconds"
            )
        )
    ],
    expression="$.inputValue == 'true' ? 'true' : 'false'",
    evaluator_type=SwitchEvaluatorType.JAVASCRIPT,
    input_parameters=SwitchTaskInputParameters(
        input_value="${workflow.input.value}"
    )
)

self.tasks.append(switch)
```

### TERMINATE TASK

```python
TerminateTask(
    name="terminate",
    task_reference_name="terminate",
    input_parameters=TerminateTaskInputParameters(
        termination_status=WorkflowStatus.COMPLETED, 
        workflow_output={"output": "COMPLETED"}
    )
)
```

### WAIT_DURATION TASK

```python
self.tasks.append(WaitDurationTask(
    name="WAIT",
    task_reference_name="WAIT",
    input_parameters=WaitDurationTaskInputParameters(
        duration="10 seconds"
    )
))
```

### WAIT_UNTIL TASK

```python
self.tasks.append(WaitUntilTask(
    name="WAIT_UNTIL",
    task_reference_name="WAIT_UNTIL",
    input_parameters=WaitUntilTaskInputParameters(
        until='2022-12-25 09:00 PST'
    )
))
```
