from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import TypeAlias

from frinx.client.FrinxConductorWrapper import FrinxConductorWrapper
from frinx.common.conductor_enums import TaskResultStatus
from frinx.common.util import jsonify_description
from frinx.common.util import snake_to_camel_case
from frinx.common.worker.task import Task
from frinx.common.worker.task_def import BaseTaskdef
from frinx.common.worker.task_def import DefaultTaskDefinition
from frinx.common.worker.task_def import TaskDefinition
from frinx.common.worker.task_def import TaskInput
from frinx.common.worker.task_def import TaskOutput
from frinx.common.worker.task_result import TaskResult
from pydantic import ValidationError
from pydantic.dataclasses import dataclass

RawTaskIO: TypeAlias = dict[str, Any]
TaskExecLog: TypeAlias = str


class Config:
    arbitrary_types_allowed = True
    alias_generator = snake_to_camel_case
    allow_population_by_field_name = True


@dataclass(config=Config)
class WorkerImpl(ABC):
    task_def: TaskDefinition = None
    task_def_template: type[BaseTaskdef] | type[DefaultTaskDefinition] = None

    class WorkerDefinition(TaskDefinition): ...

    class WorkerInput(TaskInput): ...

    class WorkerOutput(TaskOutput): ...

    def __init__(
        self, task_def_template: type[BaseTaskdef] | type[DefaultTaskDefinition] = None
    ) -> None:
        self.task_def = self.task_definition_builder(task_def_template)

    @classmethod
    def task_definition_builder(
        cls, task_def_template: type[BaseTaskdef] | type[DefaultTaskDefinition] = None
    ) -> TaskDefinition:
        cls.validate()

        params = {}
        for param in cls.WorkerDefinition.__fields__.values():
            params[param.alias] = param.default
            if param.alias == "inputKeys":
                params[param.alias] = [field.alias for field in cls.WorkerInput.__fields__.values()]
            if param.alias == "outputKeys":
                params[param.alias] = [
                    field.alias for field in cls.WorkerOutput.__fields__.values()
                ]

        # Create Description in JSON format
        params["description"] = jsonify_description(
            params["description"], params["labels"], params["rbac"]
        )

        params.pop("labels")
        params.pop("rbac")

        if task_def_template is None:
            task_def_template = DefaultTaskDefinition.__fields__.items()
        else:
            task_def_template = task_def_template.__fields__.items()

        # Transform dict to TaskDefinition object use default values in necessary
        task_def = TaskDefinition(**params)

        for key, value in task_def_template:
            if value.default is not None and task_def.__getattribute__(key) is None:
                task_def.__setattr__(key, value.default)

        return task_def

    def register(self, conductor_client: FrinxConductorWrapper) -> None:
        conductor_client.register(
            task_type=self.task_def.name,
            task_definition=self.task_def.dict(by_alias=True, exclude_none=True),
            exec_function=self._execute_wrapper,
        )

    @abstractmethod
    def execute(self, task: Task) -> TaskResult:
        pass

    @classmethod
    def _execute_wrapper(cls, task: RawTaskIO) -> Any:
        try:
            cls.WorkerInput.parse_obj(task["inputData"])
        except ValidationError as error:
            return TaskResult(status=TaskResultStatus.FAILED, logs=[TaskExecLog(str(error))]).dict()

        try:
            # TODO check if ok
            task_result = cls.execute(cls, Task(**task)).dict()  # type: ignore[arg-type]
            return task_result

        except Exception as error:
            return TaskResult(status=TaskResultStatus.FAILED, logs=[TaskExecLog(str(error))]).dict()

    @classmethod
    def validate(cls) -> None:
        if not issubclass(cls.WorkerInput, TaskInput):
            error_msg = (
                "Expecting task input model to be a subclass of "
                f"'{TaskInput.__qualname__}', not '{cls.WorkerInput.__qualname__}'"
            )
            raise TypeError(error_msg)

        if not issubclass(cls.WorkerOutput, TaskOutput):
            error_msg = (
                "Expecting task output model to be a subclass of "
                f"'{TaskOutput.__qualname__}', not '{cls.WorkerOutput.__qualname__}'"
            )
            raise TypeError(error_msg)
