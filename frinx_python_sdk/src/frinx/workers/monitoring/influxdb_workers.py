from typing import Any
from typing import Optional

from frinx.common.conductor_enums import TaskResultStatus
from frinx.common.worker.service import ServiceWorkersImpl
from frinx.common.worker.task import Task
from frinx.common.worker.task_def import TaskDefinition
from frinx.common.worker.task_def import TaskInput
from frinx.common.worker.task_def import TaskOutput
from frinx.common.worker.task_result import TaskResult
from frinx.common.worker.worker import WorkerImpl
from frinx.services.monitoring import influxdb_worker
from frinx.services.monitoring.influxdb_utils import InfluxOutput


class Influx(ServiceWorkersImpl):
    class InfluxWriteData(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "INFLUX_write_data"
            description = "Write data do InfluxDB"
            labels = ["INFLUX"]
            timeout_seconds = 300

        class WorkerInput(TaskInput):
            org: str
            token: str
            bucket: str
            measurement: str
            tags: dict[str, Any] | str
            fields: dict[str, Any] | str

        class WorkerOutput(TaskOutput):
            output: dict[str, Any]

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = influxdb_worker.influx_write_data(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################
    class InfluxQueryData(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "INFLUX_query_data"
            description = "Query data from InfluxDB"
            labels = ["INFLUX"]
            timeout_seconds = 300

        class WorkerInput(TaskInput):
            org: str
            token: str
            query: str
            format_data: Optional[list[str] | str]

        class WorkerOutput(TaskOutput):
            output: dict[str, Any]

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = influxdb_worker.influx_query_data(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################
    class InfluxCreateBucket(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "INFLUX_create_bucket"
            description = "Create bucket for organization in InfluxDB"
            labels = ["INFLUX"]
            timeout_seconds = 300

        class WorkerInput(TaskInput):
            org: str
            token: str
            bucket: str

        class WorkerOutput(TaskOutput):
            code: dict[str, Any]
            data: dict[str, Any]
            logs: Optional[str]

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = influxdb_worker.influx_create_bucket(**task.input_data)
            return response_handler(response, task_result)


def response_handler(response: InfluxOutput, task_result: TaskResult) -> TaskResult:
    match response.code:
        case 200 | 201:
            task_result.status = TaskResultStatus.COMPLETED
            if response.code:
                task_result.add_output_data("response_code", response.code)
            if response.data:
                task_result.add_output_data("response_body", response.data)
            if response.logs:
                task_result.logs = response.logs

            return task_result
        case _:
            task_result.status = TaskResultStatus.FAILED
            task_result.logs = task_result.logs or str(response)
            if response.code:
                task_result.add_output_data("response_code", response.code)
            if response.data:
                task_result.add_output_data("response_body", response.data)
            return task_result
