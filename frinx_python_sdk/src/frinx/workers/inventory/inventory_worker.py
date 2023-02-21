from typing import Any
from typing import Optional

import frinx.services.inventory.inventory_worker as inventory
from frinx.common.conductor_enums import TaskResultStatus
from frinx.common.worker.service import ServiceWorkersImpl
from frinx.common.worker.task import Task
from frinx.common.worker.task_def import TaskDefinition
from frinx.common.worker.task_def import TaskInput
from frinx.common.worker.task_def import TaskOutput
from frinx.common.worker.task_result import TaskResult
from frinx.common.worker.worker import WorkerImpl
from frinx.services.inventory.utils import InventoryOutput


class Inventory(ServiceWorkersImpl):
    ###############################################################################

    class InventoryGetDevicesInfo(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "INVENTORY_get_device_info"
            description = "get a list of pages cursors from device inventory"
            labels = ["BASIC", "INVENTORY"]

        class WorkerInput(TaskInput):
            device_name: str

        class WorkerOutput(TaskOutput):
            response_code: int
            response_body: Any

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = inventory.get_device_status(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class InventoryInstallDeviceById(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "INVENTORY_install_device_by_id"
            description = "Install device by device ID"
            labels = ["BASIC", "INVENTORY"]
            timeoutSeconds = 3600
            responseTimeoutSeconds = 3600

        class WorkerInput(TaskInput):
            device_id: Optional[str]

        class WorkerOutput(TaskOutput):
            url: str
            response_code: int
            response_body: Any

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = inventory.install_device_by_id(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class InventoryUninstallDeviceById(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "INVENTORY_uninstall_device_by_id"
            description = "Uninstall device by device ID"
            labels = ["BASIC", "INVENTORY"]
            timeoutSeconds = 3600
            responseTimeoutSeconds = 3600

        class WorkerInput(TaskInput):
            device_id: Optional[str]

        class WorkerOutput(TaskOutput):
            url: str
            response_code: int
            response_body: Any

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = inventory.uninstall_device_by_id(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################
    class InventoryInstallDeviceByName(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "INVENTORY_install_device_by_name"
            description = "Install device by device name"
            labels = ["BASIC", "INVENTORY"]
            timeoutSeconds = 3600
            responseTimeoutSeconds = 3600

        class WorkerInput(TaskInput):
            device_name: str

        class WorkerOutput(TaskOutput):
            url: str
            response_code: int
            response_body: Any

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = inventory.install_device_by_name(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class InventoryUninstallDeviceByName(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "INVENTORY_uninstall_device_by_name"
            description = "Uninstall device by device name"
            labels = ["BASIC", "INVENTORY"]
            timeoutSeconds = 3600
            responseTimeoutSeconds = 3600

        class WorkerInput(TaskInput):
            device_name: Optional[str]

        class WorkerOutput(TaskOutput):
            url: str
            response_code: int
            response_body: Any

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = inventory.uninstall_device_by_name(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class InventoryGetLabels(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "INVENTORY_get_labels"
            description = "Get device labels"
            labels = ["BASICS", "MAIN", "INVENTORY"]
            timeoutSeconds = 3600
            responseTimeoutSeconds = 3600

        class WorkerInput(TaskInput):
            ...

        class WorkerOutput(TaskOutput):
            url: str
            response_code: int
            response_body: Any

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = inventory.get_labels()
            return response_handler(response, task_result)

    ###############################################################################

    class InventoryCreateLabel(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "INVENTORY_create_label"
            description = "Create device labels"
            labels = ["BASICS", "MAIN", "INVENTORY"]
            timeoutSeconds = 3600
            responseTimeoutSeconds = 3600

        class WorkerInput(TaskInput):
            label: str

        class WorkerOutput(TaskOutput):
            url: str
            response_code: int
            response_body: Any

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = inventory.create_label(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class InventoryAddDevice(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "INVENTORY_add_device"
            description = "Add device to inventory database"
            labels = ["BASICS", "MAIN", "INVENTORY"]
            timeoutSeconds = 3600
            responseTimeoutSeconds = 3600

        class WorkerInput(TaskInput):
            device_name: str
            zone: str
            service_state: str
            mount_body: str
            vendor: Optional[str]
            model: Optional[str]
            size: Optional[str]
            labels: Optional[str]

        class WorkerOutput(TaskOutput):
            url: str
            response_code: int
            response_body: Any

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = inventory.add_device(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################
    class InventoryGetPagesCursors(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "INVENTORY_get_pages_cursors"
            description = "Get a list of pages cursors from device inventory"
            labels = ["BASIC", "INVENTORY"]
            retry_timeout= 3600
            responseTimeoutSeconds = 3600

        class WorkerInput(TaskInput):
            labels: Optional[str]

        class WorkerOutput(TaskOutput):
            labels: str
            url: str
            response_code: str
            page_ids_count: str
            page_size: str
            page_ids: str

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = inventory.get_device_pages_cursors(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class InventoryGetAllDevicesAsDynamicForkTask(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "INVENTORY_get_all_devices_as_dynamic_fork_tasks"
            description = "Get all devices as dynamic fork task"
            labels = ["BASIC", "INVENTORY"]

        class WorkerInput(TaskInput):
            labels: Optional[str]
            task: str
            task_params: dict
            optional: bool = False

        class WorkerOutput(TaskOutput):
            url: str
            response_code: int
            response_body: Any

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = inventory.all_devices_fork_tasks(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################
    class InventoryGetPagesCursorsForkTasks(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "INVENTORY_get_pages_cursors_fork_tasks"
            description = "Get all pages cursors as dynamic fork tasks"
            labels = ["BASIC", "INVENTORY"]
            timeoutSeconds = 3600
            responseTimeoutSeconds = 3600

        class WorkerInput(TaskInput):
            task: str
            page_ids: str
            labels: Optional[str]

        class WorkerOutput(TaskOutput):
            url: str
            response_code: int
            response_body: Any

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = inventory.page_device_dynamic_fork_tasks(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class InventoryInstallInBatch(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "INVENTORY_install_in_batch"
            description = "Install devices in batch started from page cursor"
            labels = ["BASIC", "INVENTORY"]
            timeoutSeconds = 3600
            responseTimeoutSeconds = 3600

        class WorkerInput(TaskInput):
            page_size: str
            page_id: str
            labels: Optional[str]

        class WorkerOutput(TaskOutput):
            url: str
            dynamic_tasks_i: str
            dynamic_tasks: str

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = inventory.install_in_batch(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class InventoryUninstallInBatch(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "INVENTORY_uninstall_in_batch"
            description = "Uninstall devices in batch started from page cursor"
            labels = ["BASIC", "INVENTORY"]
            timeoutSeconds = 3600
            responseTimeoutSeconds = 3600

        class WorkerInput(TaskInput):
            page_size: int
            page_id: str
            labels: Optional[str]

        class WorkerOutput(TaskOutput):
            url: str
            dynamic_tasks_i: str
            dynamic_tasks: str

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = inventory.uninstall_in_batch(**task.input_data)
            return response_handler(response, task_result)


def response_handler(response: InventoryOutput, task_result: TaskResult) -> TaskResult:
    match response.status:
        case "data":
            task_result.status = TaskResultStatus.COMPLETED
            task_result.add_output_data("response_code", response.code)
            task_result.add_output_data("response_body", response.data)
            return task_result
        case _:
            task_result.status = TaskResultStatus.FAILED
            task_result.logs = str(response)
            task_result.add_output_data("response_code", response.code)
            task_result.add_output_data("response_body", response.data)
            return task_result