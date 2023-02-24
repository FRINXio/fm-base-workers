import typing

from frinx.common.workflow.service import ServiceWorkflowsImpl
from frinx.common.workflow.task import DecisionCaseValueTask
from frinx.common.workflow.task import DecisionCaseValueTaskInputParameters
from frinx.common.workflow.task import SimpleTask
from frinx.common.workflow.task import SimpleTaskInputParameters
from frinx.common.workflow.task import TerminateTask
from frinx.common.workflow.task import TerminateTaskInputParameters
from frinx.common.workflow.task import WorkflowStatus
from frinx.common.workflow.workflow import FrontendWFInputFieldType
from frinx.common.workflow.workflow import WorkflowImpl
from frinx.common.workflow.workflow import WorkflowInputField
from frinx.services.inventory.utils import DeviceSize
from frinx.services.inventory.utils import ServiceState
from frinx.workers.inventory.inventory_worker import Inventory


class InventoryWorkflows(ServiceWorkflowsImpl):
    class InstallDeviceByName(WorkflowImpl):
        name = "Install_device_by_name"
        version = 1
        description = "Install device from device inventory by device name"
        restartable = False
        schema_version = 2
        labels = ["BASICS", "INVENTORY"]

        class WorkflowInput(WorkflowImpl.WorkflowInput):
            device_name = WorkflowInputField(
                name="device_name",
                frontend_default_value="IOS01",
                description="Device name from Device Inventory",
                type=FrontendWFInputFieldType.STRING,
            )

        class WorkflowOutput(WorkflowImpl.WorkflowOutput):
            url: str
            response_code: str
            response_body: dict[str, typing.Any]

        def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:
            self.tasks.append(
                SimpleTask(
                    name=Inventory.InventoryInstallDeviceByName,
                    task_reference_name="Install_device_by_name",
                    input_parameters=SimpleTaskInputParameters(
                        device_name="${workflow.input.device_name}"
                    ),
                )
            )

    class UninstallDeviceByName(WorkflowImpl):
        name = "Uninstall_device_by_name"
        version = 1
        description = "Uninstall device from device inventory by device name"
        restartable = False
        schema_version = 2
        labels = ["BASICS", "INVENTORY"]

        class WorkflowInput(WorkflowImpl.WorkflowInput):
            device_name = WorkflowInputField(
                name="device_name",
                frontend_default_value="IOS01",
                description="Device name from Device Inventory",
                type=FrontendWFInputFieldType.STRING,
            )

        class WorkflowOutput(WorkflowImpl.WorkflowOutput):
            url: str
            response_code: str
            response_body: dict[str, typing.Any]

        def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:
            self.tasks.append(
                SimpleTask(
                    name=Inventory.InventoryUninstallDeviceByName,
                    task_reference_name="Uninstall_device_by_name",
                    input_parameters=SimpleTaskInputParameters(
                        device_name="${workflow.input.device_name}"
                    ),
                )
            )

    class InstallDeviceById(WorkflowImpl):
        name = "Install_device_by_id"
        version = 1
        description = "Install device from device inventory by device id"
        restartable = False
        schema_version = 2
        labels = ["BASICS", "INVENTORY"]

        class WorkflowInput(WorkflowImpl.WorkflowInput):
            device_id = WorkflowInputField(
                name="device_id",
                frontend_default_value="IOS01",
                description="Device name from Device Inventory",
                type=FrontendWFInputFieldType.STRING,
            )

        class WorkflowOutput(WorkflowImpl.WorkflowOutput):
            url: str
            response_code: str
            response_body: dict[str, typing.Any]

        def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:
            self.tasks.append(
                SimpleTask(
                    name=Inventory.InventoryUninstallDeviceById,
                    task_reference_name="Install_device_by_id",
                    input_parameters=SimpleTaskInputParameters(
                        device_id="${workflow.input.device_id}"
                    ),
                )
            )

    class UninstallDeviceById(WorkflowImpl):
        name = "Uninstall_device_by_id"
        version = 1
        description = "Uninstall device from device inventory by device id"
        restartable = False
        schema_version = 2
        labels = ["BASICS", "INVENTORY"]

        class WorkflowInput(WorkflowImpl.WorkflowInput):
            device_id = WorkflowInputField(
                name="device_id",
                frontend_default_value="IOS01",
                description="Device name from Device Inventory",
                type=FrontendWFInputFieldType.STRING,
            )

        class WorkflowOutput(WorkflowImpl.WorkflowOutput):
            url: str
            response_code: str
            response_body: dict[str, typing.Any]

        def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:
            self.tasks.append(
                SimpleTask(
                    name=Inventory.InventoryUninstallDeviceById,
                    task_reference_name="Uninstall_device_by_id",
                    input_parameters=SimpleTaskInputParameters(
                        device_id="${workflow.input.device_id}"
                    ),
                )
            )

    class AddDeviceToInventory(WorkflowImpl):
        name = "Add_device_to_inventory"
        version = 1
        description = "Add device to inventory"
        restartable = True
        schema_version = 2
        labels = ["BASICS", "INVENTORY"]
        update_time = 2
        workflow_status_listener_enabled = True

        class WorkflowInput(WorkflowImpl.WorkflowInput):
            device_name = WorkflowInputField(
                name="device_name",
                frontend_default_value="IOS01",
                description="Device name",
                type=FrontendWFInputFieldType.STRING,
            )

            zone = WorkflowInputField(
                name="zone",
                frontend_default_value="uniconfig",
                description="Deployment zone",
                type=FrontendWFInputFieldType.STRING,
            )

            service_state = WorkflowInputField(
                name="service_state",
                frontend_default_value=ServiceState.IN_SERVICE,
                description="Device service state",
                type=FrontendWFInputFieldType.SELECT,
                options=ServiceState.list(),
            )

            mount_body = WorkflowInputField(
                name="mount_body",
                frontend_default_value=None,
                description="Device mount body",
                type=FrontendWFInputFieldType.TEXTAREA,
            )

            vendor = WorkflowInputField(
                name="vendor",
                frontend_default_value=None,
                description="Device vendor",
                type=FrontendWFInputFieldType.STRING,
            )

            model = WorkflowInputField(
                name="model",
                frontend_default_value=None,
                description="Device model",
                type=FrontendWFInputFieldType.STRING,
            )

            device_size = WorkflowInputField(
                name="device_size",
                frontend_default_value=DeviceSize.MEDIUM,
                description="Device size",
                type=FrontendWFInputFieldType.SELECT,
                options=DeviceSize.list(),
            )

            labels = WorkflowInputField(
                name="labels",
                frontend_default_value=None,
                description="Device status",
                type=FrontendWFInputFieldType.STRING,
            )

            install = WorkflowInputField(
                name="install",
                frontend_default_value=False,
                description="Install device",
                type=FrontendWFInputFieldType.TOGGLE,
            )

        class WorkflowOutput(WorkflowImpl.WorkflowOutput):
            url: str
            response_code: str
            response_body: dict[str, typing.Any]

        def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:
            add_device = SimpleTask(
                name=Inventory.InventoryAddDevice,
                task_reference_name="Add_device_to_inventory",
                input_parameters=SimpleTaskInputParameters(
                    device_name="${workflow.input.device_name}",
                    zone="${workflow.input.zone}",
                    service_state="${workflow.input.service_state}",
                    mount_body="${workflow.input.mount_body}",
                    vendor="${workflow.input.vendor}",
                    model="${workflow.input.model}",
                    device_size="${workflow.input.device_size}",
                    labels="${workflow.input.labels}",
                ),
            )

            default_tasks = [
                TerminateTask(
                    name="skip_install",
                    task_reference_name="skip_install",
                    input_parameters=TerminateTaskInputParameters(
                        termination_status=WorkflowStatus.COMPLETED, workflow_output={"a": "b"}
                    ),
                )
            ]

            true_tasks = [
                SimpleTask(
                    name=Inventory.InventoryInstallDeviceById,
                    task_reference_name="Add_device_to_inventory.output.response_body.add_device.device.id",
                    input_parameters=SimpleTaskInputParameters(
                        device_id="${Add_device_to_inventory.output.response_body.addDevice.device.id}"
                    ),
                )
            ]

            self.tasks.append(add_device)

            self.tasks.append(
                (
                    DecisionCaseValueTask(
                        name="decisionTask",
                        task_reference_name="decisionTask",
                        case_value_param="install",
                        decision_cases={"true": true_tasks},
                        default_case=default_tasks,
                        input_parameters=DecisionCaseValueTaskInputParameters(
                            case_value_param="${workflow.input.install}"
                        ),
                    )
                )
            )
