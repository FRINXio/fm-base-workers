import typing

from frinx.common.conductor_enums import SwitchEvaluatorType
from frinx.common.conductor_enums import WorkflowStatus
from frinx.common.workflow.task import SimpleTask
from frinx.common.workflow.task import SwitchTask
from frinx.common.workflow.task import TerminateTask
from frinx.common.workflow.workflow import WorkflowImpl
from frinx.workers.uniconfig.uniconfig_worker import Uniconfig


class UcTxClose(WorkflowImpl):
    name = "UC_TX_close"
    version = 1
    description = "Close a running uniconfig TX in case it was started by the same WF"
    restartable = False
    schema_version = 2
    workflow_status_listener_enabled = True

    class WorkflowInput(WorkflowImpl.WorkflowInput):
        started_by_wf: str = "${workflow.input.uniconfig_context.started_by_wf}"
        parent_wf: str = "${workflow.parentWorkflowId}"

    class WorkflowOutput(WorkflowImpl.WorkflowOutput):
        url: str
        response_code: str
        response_body: dict[str, typing.Any]

    def workflow_builder(self) -> WorkflowImpl:
        true_decision_tasks = [
            SimpleTask(
                name=Uniconfig.UniconfigTxCloseTransaction,
                task_reference_name="close",
                input_parameters=SimpleTask.InputData(
                    uniconfig_context="${workflow.input.uniconfig_context}"
                ),
            ),
            TerminateTask(
                name="terminate",
                task_reference_name="closed_tx",
                input_parameters=TerminateTask.InputData(
                    termination_status=WorkflowStatus.COMPLETED,
                    workflow_output={
                        "closed_current_context": "${workflow.input.uniconfig_context}"
                    },
                ),
            ),
        ]

        false_decision_tasks = [
            TerminateTask(
                name="terminate",
                task_reference_name="dont_close_parent_tx",
                input_parameters=TerminateTask.InputData(
                    termination_status=WorkflowStatus.COMPLETED,
                    workflow_output={
                        "unclosed_parent_uniconfig_context": "${workflow.input.uniconfig_context}"
                    },
                ),
            )
        ]

        self.tasks.append(
            SwitchTask(
                name="decide_task",
                task_reference_name="should_close_current_tx",
                case_expression="$.started_by_wf === $.parent_wf ? 'True' : 'False'",
                evaluator_type=SwitchEvaluatorType.JAVASCRIPT,
                decision_cases={"True": true_decision_tasks, "False": false_decision_tasks},
            )
        )

        return self
