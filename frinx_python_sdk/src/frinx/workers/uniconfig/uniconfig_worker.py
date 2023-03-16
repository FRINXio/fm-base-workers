import time
from typing import Any
from typing import Optional

import frinx.services.uniconfig.uniconfig_worker as uniconfig
from frinx.common.conductor_enums import TaskResultStatus
from frinx.common.worker.service import ServiceWorkersImpl
from frinx.common.worker.task import Task
from frinx.common.worker.task_def import TaskDefinition
from frinx.common.worker.task_def import TaskInput
from frinx.common.worker.task_def import TaskOutput
from frinx.common.worker.task_result import TaskResult
from frinx.common.worker.worker import WorkerImpl
from frinx.services.uniconfig.models import UniconfigContext
from frinx.services.uniconfig.utils import UniconfigOutput


class Uniconfig(ServiceWorkersImpl):
    ###############################################################################

    class UniconfigReadStructuredDeviceData(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "UNICONFIG_read_structured_device_data"
            description = (
                "Read device configuration or operational data in structured format e.g. openconfig"
            )
            labels = ["BASICS", "UNICONFIG", "OPENCONFIG"]

        class WorkerInput(TaskInput):
            device_id: str
            uri: str
            uniconfig_context: Optional[dict]

        class WorkerOutput(TaskOutput):
            url: str
            response_code: int
            response_body: Any

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = uniconfig.read_structured_data(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class UniconfigWriteStructuredDeviceData(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "UNICONFIG_write_structured_device_data"
            description = "Write device configuration data in structured format e.g. openconfig"
            labels = ["BASICS", "UNICONFIG"]

        class WorkerInput(TaskInput):
            device_id: str
            uri: str
            template: str
            params: Optional[str]
            uniconfig_context: Optional[UniconfigContext]

        class WorkerOutput(TaskOutput):
            url: str
            response_code: int
            response_body: Any

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = uniconfig.write_structured_data(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class UniconfigDeleteStructuredDeviceData(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "UNICONFIG_delete_structured_device_data"
            description = "Delete device configuration data in structured format e.g. openconfig"
            labels = ["BASICS", "UNICONFIG", "OPENCONFIG"]

        class WorkerInput(TaskInput):
            device_id: str
            uri: str
            uniconfig_context: Optional[UniconfigContext]

        class WorkerOutput(TaskOutput):
            url: str
            response_code: int
            response_body: Any

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = uniconfig.delete_structured_data(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class UniconfigCommit(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "UNICONFIG_commit"
            description = "Commit uniconfig"
            labels = ["BASICS", "UNICONFIG"]
            responseTimeoutSeconds = 600
            timeoutSeconds = 600

        class WorkerInput(TaskInput):
            devices: str | list
            uniconfig_context: Optional[UniconfigContext] | str

        class WorkerOutput(TaskOutput):
            url: str
            response_code: int
            response_body: Any

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            print(task)
            time.sleep(5)
            response = uniconfig.commit(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class UniconfigDryrunCommit(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "UNICONFIG_dryrun_commit"
            description = "Dryrun Commit uniconfig"
            labels = ["BASICS", "UNICONFIG"]
            responseTimeoutSeconds = 600
            timeoutSeconds = 600

        class WorkerInput(TaskInput):
            devices: str
            uniconfig_context: Optional[UniconfigContext]

        class WorkerOutput(TaskOutput):
            url: str
            response_code: int
            response_body: Any

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = uniconfig.dryrun_commit(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class UniconfigCalculateDiff(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "UNICONFIG_calculate_diff"
            description = "Calculate uniconfig diff"
            labels = ["BASICS", "UNICONFIG"]
            responseTimeoutSeconds = 600
            timeoutSeconds = 600

        class WorkerInput(TaskInput):
            devices: str
            uniconfig_context: Optional[dict]

        class WorkerOutput(TaskOutput):
            url: str
            response_code: int
            response_body: Any

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = uniconfig.calc_diff(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class UniconfigSyncFromNetwork(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "UNICONFIG_sync_from_network"
            description = "Sync uniconfig from network"
            labels = ["BASICS", "UNICONFIG"]
            responseTimeoutSeconds = 600
            timeoutSeconds = 600

        class WorkerInput(TaskInput):
            devices: str
            uniconfig_context: Optional[dict]

        class WorkerOutput(TaskOutput):
            url: str
            response_code: int
            response_body: Any

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = uniconfig.sync_from_network(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class UniconfigReplaceConfigWithOper(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "UNICONFIG_replace_config_with_oper"
            description = "Replace config with oper in uniconfig"
            labels = ["BASICS", "UNICONFIG"]
            responseTimeoutSeconds = 600
            timeoutSeconds = 600

        class WorkerInput(TaskInput):
            devices: str
            uniconfig_context: Optional[dict]

        class WorkerOutput(TaskOutput):
            url: str
            response_code: int
            response_body: Any

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = uniconfig.replace_config_with_oper(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class UniconfigTxFindStarted(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "UNICONFIG_tx_find_started"
            description = "Find all started UC transaction in a failed workflow"
            labels = ["BASICS", "UNICONFIG", "TX"]

        class WorkerInput(TaskInput):
            failed_wf_id: str

        class WorkerOutput(TaskOutput):
            uniconfig_contexts: dict

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = uniconfig.find_started_tx(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class UniconfigTxRollback(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "UNICONFIG_tx_rollback"
            description = "Rollback all tx from uniconfig_contexts"
            labels = ["BASICS", "UNICONFIG", "TX"]

        class WorkerInput(TaskInput):
            uniconfig_contexts: str

        class WorkerOutput(TaskOutput):
            ...

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = uniconfig.rollback_all_tx(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class UniconfigTxCreateMultizone(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "UNICONFIG_tx_create_multizone"
            description = "Create a dedicated multizone transaction(s)"
            labels = ["BASICS", "UNICONFIG", "TX"]

        class WorkerInput(TaskInput):
            devices: Optional[list[str]] | Optional[str]
            oam_domain: Optional[str]

        class WorkerOutput(TaskOutput):
            uniconfig_cookies_multizone: dict

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = uniconfig.create_tx_multizone(**task.input_data)

            match response.code:
                case 200 | 201:
                    task_result.status = TaskResultStatus.COMPLETED
                    if response.data:
                        task_result.add_output_data_dict(response.data)
                    if response.logs:
                        task_result.logs = response.logs
                    return task_result
                case _:
                    task_result.status = TaskResultStatus.FAILED
                    task_result.logs = task_result.logs or str(response)
                    if response.data:
                        task_result.add_output_data_dict(response.data)
                    return task_result

    ###############################################################################

    class UniconfigTxCloseTransaction(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "UNICONFIG_tx_close_multizone"
            description = "Close a dedicated multizone transaction(s)"
            labels = ["BASICS", "UNICONFIG", "TX"]

        class WorkerInput(TaskInput):
            uniconfig_context: Optional[UniconfigContext] | Optional[str]

        class WorkerOutput(TaskOutput):
            UNICONFIGTXID_multizone: dict

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = uniconfig.close_tx_multizone(**task.input_data)
            return response_handler(response, task_result)


def response_handler(response: UniconfigOutput, task_result: TaskResult) -> TaskResult:
    match response.code:
        case 200 | 201:
            task_result.status = TaskResultStatus.COMPLETED
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
            task_result.status = TaskResultStatus.FAILED
            task_result.logs = task_result.logs or str(response)
            if response.code:
                task_result.add_output_data("response_code", response.code)
            if response.data:
                task_result.add_output_data("response_body", response.data)
            if response.url:
                task_result.add_output_data("url", response.url)
            return task_result
