from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Type
from typing import TypeAlias

from frinx.common.conductor_enums import SwitchEvaluatorType
from frinx.common.conductor_enums import WorkflowStatus
from frinx.common.util import snake_to_camel_case
from frinx.common.worker.worker import WorkerImpl
from pydantic import BaseModel
from pydantic import Extra
from pydantic import Field
from pydantic import StrictBool
from pydantic import root_validator
from pydantic.utils import ROOT_KEY

WorkflowTask: TypeAlias = dict[str, str]
TaskDef: TypeAlias = dict[str, str]
TaskToDomain: TypeAlias = dict[str, str]
WorkflowDef: TypeAlias = dict[str, Any]


class TaskType(str, Enum):
    SIMPLE = "SIMPLE"
    DYNAMIC = "DYNAMIC"
    FORK_JOIN = "FORK_JOIN"
    FORK_JOIN_DYNAMIC = "FORK_JOIN_DYNAMIC"
    DECISION = "DECISION"
    SWITCH = "SWITCH"
    JOIN = "JOIN"
    DO_WHILE = "DO_WHILE"
    SUB_WORKFLOW = "SUB_WORKFLOW"
    START_WORKFLOW = "START_WORKFLOW"
    EVENT = "EVENT"
    WAIT = "WAIT"
    HUMAN = "HUMAN"
    USER_DEFINED = "USER_DEFINED"
    HTTP = "HTTP"
    LAMBDA = "LAMBDA"
    INLINE = "INLINE"
    EXCLUSIVE_JOIN = "EXCLUSIVE_JOIN"
    TERMINATE = "TERMINATE"
    KAFKA_PUBLISH = "KAFKA_PUBLISH"
    JSON_JQ_TRANSFORM = "JSON_JQ_TRANSFORM"
    SET_VARIABLE = "SET_VARIABLE"


class WorkflowTaskImpl(BaseModel):
    class InputData(BaseModel):
        class Config:
            alias_generator = snake_to_camel_case
            allow_population_by_field_name = True
            validate_assignment = True
            validate_all = True

    class SubWorkflowParam(BaseModel):
        class Config:
            alias_generator = snake_to_camel_case
            allow_population_by_field_name = True
            validate_assignment = True
            validate_all = True

    # REQUIRED
    name: str
    task_reference_name: str
    # PREDEFINED
    type: TaskType
    start_delay: int = Field(default=0)
    optional: StrictBool = Field(default=False)
    async_complete: StrictBool = Field(default=False)

    # OPTIONAL
    description: str = Field(default=None)
    input_parameters: InputData|dict[str, Any] = Field(default={})
    dynamic_task_name_param: str = Field(default=None)
    case_value_param: str = Field(default=None)
    case_expression: str = Field(default=None)
    script_expression: str = Field(default=None)
    decision_cases: dict[str, list[WorkflowTask]] = Field(default=None)
    dynamic_fork_join_tasks_param: str = Field(default=None)
    dynamic_fork_tasks_param: str = Field(default=None)
    dynamic_fork_tasks_input_param_name: str = Field(default=None)
    default_case: list[WorkflowTask] = Field(default=None)
    fork_tasks: list[list[WorkflowTask]] = Field(default=None)
    sub_workflow_param: SubWorkflowParam = Field(default=None)
    join_on: list[str] = Field(default=None)
    sink: str = Field(default=None)
    task_definition: TaskDef = Field(default=None)
    rate_limited: StrictBool = Field(default=None)
    default_exclusive_join_task: list[str] = Field(default=None)
    loop_condition: str = Field(default=None)
    loop_over: list[Any] = Field(default=None)
    retry_count: int = Field(default=None)
    evaluator_type: str = Field(default=None)
    expression: str = Field(default=None)
    workflow_task_type: str = Field(default=None)

    class Config:
        alias_generator = snake_to_camel_case
        allow_population_by_field_name = True
        validate_assignment = True
        validate_all = True


class DoWhileTask(WorkflowTaskImpl):
    type = TaskType.DO_WHILE
    loop_condition: str
    loop_over: List[WorkflowTaskImpl]


class LoopTask(WorkflowTaskImpl):
    type = TaskType.DO_WHILE
    loop_condition: str
    loop_over: List[WorkflowTaskImpl]


class DynamicForkTask(WorkflowTaskImpl):
    class InputData(WorkflowTaskImpl.InputData):
        def __init__(self, **data: Any) -> None:
            if self.__custom_root_type__ and data.keys() != {ROOT_KEY}:
                data = {ROOT_KEY: data}
            super().__init__(**data)

        class Config:
            extra = Extra.allow
            alias_generator = snake_to_camel_case
            allow_population_by_field_name = True
            validate_assignment = True
            allow_mutation = True
            validate_all = True

    type = TaskType.FORK_JOIN_DYNAMIC
    dynamic_fork_tasks_param: str
    dynamic_fork_tasks_input_param_name: str
    input_parameters: InputData

    @root_validator(pre=True)
    def check_input_values(cls, values:Dict[str, Any]) -> Dict[str, Any]:
        workflow_input = (
            values["input_parameters"]
            if isinstance(values["input_parameters"], dict)
            else values["input_parameters"].dict()
        )

        if workflow_input[values["dynamic_fork_tasks_param"]] is None:
            raise ValueError("Missing dynamic_fork_tasks_param")
        if workflow_input[values["dynamic_fork_tasks_input_param_name"]] is None:
            raise ValueError("Missing dynamic_fork_tasks_input_param_name")

        if not isinstance(workflow_input[values["dynamic_fork_tasks_param"]], List):
            raise ValueError("Missing dynamic_fork_tasks_param")

        # for task_impl in workflow_input[values["dynamic_fork_tasks_param"]]:
        #     task = WorkflowTaskImpl(**task_impl)
        # print(workflow_input[values["dynamic_fork_tasks_input_param_name"][task_impl]])

        #
        # for k in workflow_input[values["dynamic_fork_tasks_param"]]:
        #     if not isinstance(WorkflowTaskImpl(**k), WorkflowTaskImpl): raise ValueError("Missing dynamic_fork_tasks_param")
        #
        # test = DynamicForkTask.InputData()

        return values


class DynamicForkArrayTask(WorkflowTaskImpl):
    class InputData(WorkflowTaskImpl.InputData):
        fork_task_name: Type[Any] | str = Field(default=None)
        fork_task_inputs: List[Any]

    type = TaskType.FORK_JOIN_DYNAMIC
    dynamic_fork_tasks_param: str
    dynamic_fork_tasks_input_param_name: str
    input_parameters: InputData | dict[str, Any]

    @root_validator(pre=True)
    def check_input_values(cls, values:Dict[str, Any]) -> Dict[str, Any]:
        workflow_input = (
            values["input_parameters"]
            if isinstance(values["input_parameters"], dict)
            else values["input_parameters"].dict()
        )
        fork_task = workflow_input["fork_task_name"]

        # TODO validate input
        values["input_parameters"].fork_task_name = fork_task.WorkerDefinition.__fields__.get(
            "name"
        ).default

        # TODO validate fork_task_inputs
        # values["input_parameters"].fork_task_inputs = fork_task.WorkerDefinition.__fields__.get("name").default
        print(values["input_parameters"])
        return values


class ForkTask(WorkflowTaskImpl):
    type = TaskType.FORK_JOIN
    fork_tasks: list[list[WorkflowTaskImpl]]


# TODO HTTP TASK


class HttpMethod(str, Enum):
    GET = ("GET",)
    PUT = ("PUT",)
    POST = ("POST",)
    DELETE = ("DELETE",)
    HEAD = ("HEAD",)
    OPTIONS = "OPTIONS"


class HumanTask(WorkflowTaskImpl):
    class InputData(WorkflowTaskImpl.InputData):
        evaluator_type: str = "javascript"
        expression: str

    # Inner classes must be defined before inner parameters
    type = TaskType.HUMAN
    input_parameters: InputData  | dict[str, Any]


class InlineTask(WorkflowTaskImpl):
    class InputData(WorkflowTaskImpl.InputData):
        evaluator_type: str = "javascript"
        expression: str

    # Inner classes must be defined before inner parameters
    type = TaskType.INLINE
    input_parameters: InputData | dict[str, Any]


class WaitDurationTask(WorkflowTaskImpl):
    class InputData(WorkflowTaskImpl.InputData):
        duration: str

    # Inner classes must be defined before inner parameters
    type = TaskType.WAIT
    input_parameters: InputData  | dict[str, Any]


class WaitUntilTask(WorkflowTaskImpl):
    class InputData(WorkflowTaskImpl.InputData):
        until: str

    # Inner classes must be defined before inner parameters
    type = TaskType.WAIT
    input_parameters: InputData  | dict[str, Any]


class TerminateTask(WorkflowTaskImpl):
    class InputData(WorkflowTaskImpl.InputData):
        termination_status: WorkflowStatus
        termination_reason: Optional[str]
        workflow_output: Optional[Dict[str, Any]]

        class Config:
            extra = Extra.allow
            alias_generator = snake_to_camel_case
            allow_population_by_field_name = True
            validate_assignment = True
            allow_mutation = True
            validate_all = True

    # Inner classes must be defined before inner parameters
    type = TaskType.TERMINATE
    input_parameters: InputData  | dict[str, Any]


class StartTask(WorkflowTaskImpl):
    class InputData(WorkflowTaskImpl.InputData):
        name: str
        version: int = Field(default=None)
        input: Optional[Dict[str, object]] = {}
        correlationId: Optional[str]

    # Inner classes must be defined before inner parameters
    type = TaskType.START_WORKFLOW
    input_parameters: InputData  | Dict[str, Any]


# TODO SWITCH TASK
class SwitchTask(WorkflowTaskImpl):
    class InputData(WorkflowTaskImpl.InputData):
        ...

        class Config:
            extra = Extra.allow
            alias_generator = snake_to_camel_case
            allow_population_by_field_name = True
            validate_assignment = True
            allow_mutation = True
            validate_all = True

    class InputDataValueParam(InputData):
        switchCaseValue: str

    type = TaskType.DECISION
    default_case: Optional[List[WorkflowTaskImpl]] = Field(default=[])
    decision_cases: Dict[str, List[WorkflowTaskImpl]]
    evaluator_type: SwitchEvaluatorType = Field(default=SwitchEvaluatorType.JAVASCRIPT)
    case_expression: str

    @root_validator(pre=True)
    def check_input_values(cls, values:Dict[str, Any]) -> Dict[str, Any]:
        match values.get("evaluator_type"):
            case SwitchEvaluatorType.VALUE_PARAM:
                SwitchTask.InputDataValueParam(**values.get("input_parameters", {}))
        return values


class SubWorkflowTask(WorkflowTaskImpl):
    class SubClass:
        ...

    class SubWorkflowParam(WorkflowTaskImpl.SubWorkflowParam):
        name: str
        version: int
        task_to_domain: TaskToDomain = Field(default=None)
        workflow_definition: WorkflowDef = Field(default=None)

        class Config:
            alias_generator = snake_to_camel_case
            allow_population_by_field_name = True
            validate_assignment = True
            validate_all = True

    @root_validator(pre=True)
    def check_input_values(cls, values:Dict[str, Any]) -> Dict[str, Any]:
        worker = values["worker"]
        if isinstance(worker, type) and issubclass(worker, WorkerImpl):
            # TODO IMPORT WORKFLOW INSTEAD OF TASK
            task = worker()
            # print(task.task_def)
            values["name"] = task.task_def.name
            # values['version'] = task.task_def.version

        return values

    # Inner classes must be defined before inner parameters
    worker: Any
    type = TaskType.SUB_WORKFLOW
    sub_workflow_param: SubWorkflowParam = Field(default=SubWorkflowParam)


# TODO INLINE SUBWORKFLOW TASK


class SimpleTask(WorkflowTaskImpl):
    class InputData(WorkflowTaskImpl.InputData):
        def __init__(self, **data: Any) -> None:
            if self.__custom_root_type__ and data.keys() != {ROOT_KEY}:
                data = {ROOT_KEY: data}
            super().__init__(**data)

        class Config:
            extra = Extra.allow
            alias_generator = snake_to_camel_case
            allow_population_by_field_name = True
            validate_assignment = True
            allow_mutation = True
            validate_all = True

    # Inner classes must be defined before inner parameters
    name: Any
    type = TaskType.SIMPLE
    input_parameters: InputData  | Dict[str, Any]

    @root_validator(pre=True)
    def check_input_values(cls, values:Dict[str, Any]) -> Dict[str, Any]:
        worker_def = values["name"]

        if isinstance(worker_def, type) and issubclass(worker_def, WorkerImpl):
            # Init task instance
            # TODO check if OK
            task_instance = worker_def()
            # Validate input
            task_input = task_instance.__class__.WorkerInput.__fields__.items()
            workflow_input = (
                values["input_parameters"]
                if isinstance(values["input_parameters"], Dict)
                else values["input_parameters"].dict()
            )
            for k, v in task_input:
                if workflow_input[k] is None:
                    if v.required is False:
                        pass
                    else:
                        # TODO check
                        break
                # TODO validate multiple optional inputs
                # elif not isinstance(workflow_input[k], v.type_):
                #     raise ValueError("has wrong type %s", workflow_input[k], v.type_)
                else:
                    pass
            values["name"] = task_instance.task_def.name
        return values


class SetVariableTask(WorkflowTaskImpl):
    class InputData(WorkflowTaskImpl.InputData):
        def __init__(self, **data: Any) -> None:
            if self.__custom_root_type__ and data.keys() != {ROOT_KEY}:
                data = {ROOT_KEY: data}
            super().__init__(**data)

        class Config:
            extra = Extra.allow
            alias_generator = snake_to_camel_case
            allow_population_by_field_name = True
            validate_assignment = True
            allow_mutation = True
            validate_all = True

    # Inner classes must be defined before inner parameters
    type = TaskType.SET_VARIABLE
    input_parameters: InputData  | Dict[str, Any]


class KafkaRequest(BaseModel):
    boot_strap_servers: str
    key: str
    key_serializer: str
    value: str
    request_timeout_ms: str
    max_block_ms: str
    headers: Dict[str, Any] = Field(default=None)
    topic: str

    class Config:
        alias_generator = snake_to_camel_case
        allow_population_by_field_name = True
        validate_assignment = True
        allow_mutation = True


class KafkaPublishTask(WorkflowTaskImpl):
    class InputData(WorkflowTaskImpl.InputData):
        kafka_request: KafkaRequest

    type = TaskType.KAFKA_PUBLISH
    input_parameters: InputData


class JsonJQTask(WorkflowTaskImpl):
    class InputData(WorkflowTaskImpl.InputData):
        query_expression: str

    type = TaskType.JSON_JQ_TRANSFORM
    input_parameters: InputData


class JoinTask(WorkflowTaskImpl):
    type = TaskType.JOIN
    join_on: List[str] = []


class ExclusiveJoinTask(WorkflowTaskImpl):
    type = TaskType.EXCLUSIVE_JOIN
    join_on: List[str] = []


# TODO EVENT TASKS
# class ConductorEventTask(WorkflowTaskImpl):
#
#     class InputData(WorkflowTaskImpl.InputData):
#         query_expression: str
#
#     type = TaskType.EVENT
#     join_on: List[str] = []
