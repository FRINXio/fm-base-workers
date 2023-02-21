import typing

from frinx.common.conductor_enums import SwitchEvaluatorType
from frinx.common.conductor_enums import WorkflowStatus
from frinx.common.workflow.task import SimpleTask
from frinx.common.workflow.task import SwitchTask
from frinx.common.workflow.task import TerminateTask
from frinx.common.workflow.workflow import WorkflowImpl
from frinx.workers.uniconfig.uniconfig_worker import Uniconfig


class UcTxStart(WorkflowImpl):
    name = "UC_TX_start"
    version = 1
    description = (
        "Reuse a running uniconfig TX or start a new one if no uniconfig context is provided"
    )
    labels = ["TX", "MULTIZONE"]
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
        false_decision_tasks = [
            SimpleTask(
                name=Uniconfig.UniconfigTxCreateMultizone,
                task_reference_name="create",
                input_parameters=SimpleTask.InputData(
                    devices="${workflow.input.devices}", oam_domain="${workflow.input.oam_domain}"
                ),
            ),
            TerminateTask(
                name="terminate",
                task_reference_name="return_new_tx_id",
                input_parameters=TerminateTask.InputData(
                    termination_status=WorkflowStatus.COMPLETED,
                    workflow_output={
                        "uniconfig_cookies_multizone": "${create.output.uniconfig_cookies_multizone}",
                        "started_by_wf": "${workflow.parentWorkflowId}",
                    },
                ),
            ),
        ]

        true_decision_tasks = [
            TerminateTask(
                name="terminate",
                task_reference_name="return_parent_tx_id",
                input_parameters=TerminateTask.InputData(
                    termination_status=WorkflowStatus.COMPLETED,
                    workflow_output={"uniconfig_context": "${workflow.input.uniconfig_context}"},
                ),
            )
        ]

        self.tasks.append(
            SwitchTask(
                name="decide_task",
                task_reference_name="should_close_current_tx",
                case_expression="$.parent_tx_multizone ? 'True' : 'False'",
                evaluator_type=SwitchEvaluatorType.JAVASCRIPT,
                decision_cases={"True": true_decision_tasks, "False": false_decision_tasks},
            )
        )

        return self
