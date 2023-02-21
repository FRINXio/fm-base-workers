import typing

from frinx.common.workflow.task import SimpleTask
from frinx.common.workflow.workflow import WorkflowImpl
from frinx.workers.uniconfig.uniconfig_worker import Uniconfig


class UcTxTest(WorkflowImpl):
    name = "UC_TX_test"
    version = 1
    description = (
        "Reuse a running uniconfig TX or start a new one if no uniconfig context is provided"
    )
    restartable = False
    schema_version = 2
    workflow_status_listener_enabled = True

    class WorkflowInput(WorkflowImpl.WorkflowInput):
        uniconfig_context: str = "${workflow.input.uniconfig_context.uniconfig_cookies_multizone}"
        devices: list[str] = "${workflow.input.devices}"
        oam_domain: str = "${workflow.input.oam_domain}"

    class WorkflowOutput(WorkflowImpl.WorkflowOutput):
        url: str
        response_code: str
        response_body: dict[str, typing.Any]

    def workflow_builder(self) -> WorkflowImpl:
        self.tasks.append(
            SimpleTask(
                name=Uniconfig.UniconfigTxCreateMultizone,
                task_reference_name="create",
                input_parameters=SimpleTask.InputData(
                    devices="${workflow.input.devices}", oam_domain="${workflow.input.oam_domain}"
                ),
            )
        )

        return self
