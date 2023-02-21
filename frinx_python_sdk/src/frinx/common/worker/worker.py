from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import TypeAlias

from frinx.client.FrinxConductorWrapper import FrinxConductorWrapper
from frinx.common.conductor_enums import TaskResultStatus
from frinx.common.util import jsonify_description
from frinx.common.worker.task import Task
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


@dataclass(config=Config)
class WorkerImpl(ABC):
    task_def: TaskDefinition = None

    class WorkerDefinition(TaskDefinition):
        ...

    class WorkerInput(TaskInput):
        ...

    class WorkerOutput(TaskOutput):
        ...

    def __init__(self) -> None:
        self.task_def = self.task_definition_builder()

    @classmethod
    def task_definition_builder(cls) -> TaskDefinition:
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

        # Transform dict to TaskDefinition object use default values in necessary
        task_def = TaskDefinition(**params)
        for k, v in DefaultTaskDefinition.__fields__.items():
            if v.default is not None and task_def.__getattribute__(k) is None:
                task_def.__setattr__(k, v.default)

        return task_def

    def register(self, cc: FrinxConductorWrapper) -> None:
        cc.register(
            task_type=self.task_def.name,
            task_definition=self.task_def.dict(),
            exec_function=self._execute_wrapper,
        )

    @abstractmethod
    def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
        pass

    @classmethod
    def _execute_wrapper(cls, task: RawTaskIO) -> Any:
        try:
            task_data = cls.WorkerInput.parse_obj(task["inputData"])
        except ValidationError as e:
            return TaskResult(status=TaskResultStatus.FAILED, logs=[TaskExecLog(str(e))]).dict()

        try:
            # TODO check if ok
            task_result = cls.execute(cls, Task(**task), TaskResult()).dict()
            return task_result

        except Exception as e:
            return TaskResult(status=TaskResultStatus.FAILED, logs=[TaskExecLog(str(e))]).dict()

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
