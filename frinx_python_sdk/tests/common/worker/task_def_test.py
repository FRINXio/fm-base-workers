import json
import unittest
from typing import Any
from typing import Optional

import frinx.services.http.http_worker as http
from frinx.common.conductor_enums import RetryLogic
from frinx.common.conductor_enums import TimeoutPolicy
from frinx.common.frinx_rest import x_from
from frinx.common.worker.service import ServiceWorkersImpl
from frinx.common.worker.task import Task
from frinx.common.worker.task_def import TaskDefinition
from frinx.common.worker.task_def import TaskInput
from frinx.common.worker.task_def import TaskOutput
from frinx.common.worker.task_result import TaskResult
from frinx.common.worker.worker import WorkerImpl
from pydantic import BaseModel
from pydantic import Field


class TestTaskGenerator(unittest.TestCase):
    def test_create_task_def(self):
        class Http(ServiceWorkersImpl):
            class HttpTask1(WorkerImpl):
                class WorkerDefinition(TaskDefinition):
                    name = "HTTP_task_1"
                    description = "Generic http task"
                    labels = ["BASIC", "HTTP"]
                    timeout_seconds = 360
                    response_timeout_seconds = 360
                    execution_name_space = "execution_namespace"
                    retry_count = 10
                    concurrent_exec_limit = 5

                class WorkerInput(TaskInput):
                    http_request: Optional[str | dict]

                class WorkerOutput(TaskOutput):
                    response: Any
                    body: Any
                    status_code: int = Field(..., alias="statusCode")
                    cookies: dict[str, Any]

                def execute(self, task_def: Task, task_result: TaskResult) -> TaskResult:
                    pass

            class HttpTask2(WorkerImpl):
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

                def execute(self, task_def: Task, task_result: TaskResult) -> TaskResult:
                    pass

        tasks = Http().Tasks()
        test_task = []
        for task in tasks:
            test_task.append(task.task_def.dict(exclude_none=True, by_alias=True))

        test_mock = [
            {
                "name": "HTTP_task_1",
                "description": '{"description": "Generic http task", "labels": ["BASIC", "HTTP"]}',
                "retryCount": 10,
                "timeoutSeconds": 360,
                "inputKeys": ["http_request"],
                "outputKeys": ["response", "body", "statusCode", "cookies"],
                "timeoutPolicy": "ALERT_ONLY",
                "retryLogic": "FIXED",
                "retryDelaySeconds": 0,
                "responseTimeoutSeconds": 360,
                "concurrentExecLimit": 5,
                "rateLimitPerFrequency": 0,
                "rateLimitFrequencyInSeconds": 5,
                "executionNameSpace": "execution_namespace",
                "ownerEmail": "fm-base-workers",
            },
            {
                "name": "HTTP_task",
                "description": '{"description": "Generic http task", "labels": ["BASIC", "HTTP"]}',
                "retryCount": 0,
                "timeoutSeconds": 360,
                "inputKeys": ["http_request"],
                "outputKeys": ["response", "body", "statusCode", "cookies"],
                "timeoutPolicy": "ALERT_ONLY",
                "retryLogic": "FIXED",
                "retryDelaySeconds": 0,
                "responseTimeoutSeconds": 360,
                "rateLimitPerFrequency": 0,
                "rateLimitFrequencyInSeconds": 5,
                "ownerEmail": "fm-base-workers",
            },
        ]

        self.assertListEqual(test_task, test_mock)

    def test_create_task_def_with_custom_default(self):
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

        class DefaultTaskDefinition(BaseModel):
            retry_count: int = 0
            timeout_policy: TimeoutPolicy = TimeoutPolicy.ALERT_ONLY
            timeout_seconds: int = 60
            retry_logic: RetryLogic = RetryLogic.FIXED
            retry_delay_seconds: int = 0
            response_timeout_seconds: int = 59
            rate_limit_per_frequency: int = 0
            rate_limit_frequency_in_seconds: int = 5
            owner_email: str = x_from
            limit_to_thread_count: int = 10

        test_task = HttpTask(task_def_template=DefaultTaskDefinition).task_def.dict(
            exclude_none=True
        )
        test_mock = {
            "name": "HTTP_task",
            "description": '{"description": "Generic http task", "labels": ["BASIC", "HTTP"]}',
            "retry_count": 0,
            "timeout_seconds": 360,
            "input_keys": ["http_request"],
            "output_keys": ["response", "body", "statusCode", "cookies"],
            "timeout_policy": "ALERT_ONLY",
            "retry_logic": "FIXED",
            "retry_delay_seconds": 0,
            "response_timeout_seconds": 360,
            "rate_limit_per_frequency": 0,
            "rate_limit_frequency_in_seconds": 5,
            "owner_email": x_from,
            "limit_to_thread_count": 10,
        }

        self.assertDictEqual(test_task, test_mock)


if __name__ == "__main__":
    unittest.main()
