from typing import Any
from typing import Optional

import frinx.services.http.http_worker as http
from frinx.common.worker.service import ServiceWorkersImpl
from frinx.common.worker.task import Task
from frinx.common.worker.task_def import TaskDefinition
from frinx.common.worker.task_def import TaskInput
from frinx.common.worker.task_def import TaskOutput
from frinx.common.worker.task_result import TaskResult
from frinx.common.worker.worker import WorkerImpl
from pydantic import Field


class Http(ServiceWorkersImpl):
    ###############################################################################

    class HttpTask(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "HTTP_task"
            description = "Generic http task"
            labels = ["BASIC", "HTTP"]
            timeout_seconds = 360
            response_timeout_seconds = 360

        class WorkerInput(TaskInput):
            http_request: Optional[str | dict]

        class WorkerOutput(TaskOutput):
            response: Any
            body: Any
            status_code: int = Field(..., alias="statusCode")
            cookies: dict[str, Any]

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = http.http_task(**task.input_data)
            return response
