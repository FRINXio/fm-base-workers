from typing import Any

from frinx.common.conductor_enums import TaskResultStatus
from frinx.common.worker.service import ServiceWorkersImpl
from frinx.common.worker.task import Task
from frinx.common.worker.task_def import TaskDefinition
from frinx.common.worker.task_def import TaskInput
from frinx.common.worker.task_def import TaskOutput
from frinx.common.worker.task_result import TaskResult
from frinx.common.worker.worker import WorkerImpl
from frinx.services.uniconfig import netconf_worker
from frinx.services.uniconfig.models import NetconfInputBody
from frinx.services.uniconfig.models import UniconfigOutput


class NETCONF(ServiceWorkersImpl):
    class NetconfMountNetconf(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "Netconf_mount_netconf"
            description = "mount a Netconf device"
            labels = ["BASIC", "NETCONF"]
            timeout_seconds = 600
            response_timeout_seconds = 600

        class WorkerInput(TaskInput):
            device_id: str
            host: str
            port: str
            keepalive_delay: str
            tcp_only: str
            username: str
            password: str
            uniconfig_native: str
            blacklist: str
            dry_run_journal_size: str
            reconcile: str
            sleep_factor: str
            between_attempts_timeout_millis: str
            connection_timeout_millis: str
            schema_cache_directory: str
            enabled_notifications: str
            capability: str

        class WorkerOutput(TaskOutput):
            url: str
            request_body: dict[str, Any]
            response_body: dict[str, Any]
            response_code: int

        def execute(self, task: Task) -> TaskResult:
            response = netconf_worker.execute_mount_netconf(**task.input_data)
            return response_handler(response)

    ###############################################################################
    class NetconfMountAnyNetconf(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "Netconf_mount_any_netconf"
            description = "mount any Netconf device"
            labels = ["BASIC", "NETCONF"]
            timeout_seconds = 600
            response_timeout_seconds = 600

        class WorkerInput(TaskInput):
            mount_body: NetconfInputBody

        class WorkerOutput(TaskOutput):
            url: str
            request_body: dict[str, Any]
            response_body: dict[str, Any]
            response_code: int

        def execute(self, task: Task) -> TaskResult:
            response = netconf_worker.execute_mount_any(**task.input_data)
            return response_handler(response)

    ###############################################################################

    class NetconfUnmountNetconf(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "Netconf_unmount_netconf"
            description = "unmount a netconf device"
            labels = ["BASIC", "NETCONF"]

        class WorkerInput(TaskInput):
            device_id: str

        class WorkerOutput(TaskOutput):
            url: str
            response_body: dict[str, Any]
            response_code: int

        def execute(self, task: Task) -> TaskResult:
            response = netconf_worker.execute_unmount_netconf(**task.input_data)
            return response_handler(response)

    ###############################################################################

    class NetconfReadStructuredDeviceData(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "Netconf_read_structured_device_data"
            description = (
                "Read device configuration or operational data in structured format e.g. netconf"
            )
            labels = ["BASIC", "NETCONF"]

        class WorkerInput(TaskInput):
            device_id: str
            uri: str
            uniconfig_context: str

        class WorkerOutput(TaskOutput):
            url: str
            response_body: dict[str, Any]
            response_code: int

        def execute(self, task: Task) -> TaskResult:
            response = netconf_worker.read_structured_data_sync(**task.input_data)
            return response_handler(response)


def response_handler(response: UniconfigOutput) -> TaskResult:
    match response.code:
        case response_code if response_code in range(200, 299):
            task_result = TaskResult(status=TaskResultStatus.COMPLETED)
            if response.code:
                task_result.add_output_data("response_code", response.code)
            if response.data:
                task_result.add_output_data("response_body", response.data)
            if response.url:
                task_result.add_output_data("url", response.url)
            if response.logs:
                task_result.logs = response.logs

            return task_result
        case _:
            task_result = TaskResult(status=TaskResultStatus.FAILED)
            task_result.logs = task_result.logs or str(response)
            if response.code:
                task_result.add_output_data("response_code", response.code)
            if response.data:
                task_result.add_output_data("response_body", response.data)
            if response.url:
                task_result.add_output_data("url", response.url)
            return task_result
