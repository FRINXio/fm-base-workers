import typing

from frinx.common.conductor_enums import WorkflowStatus
from frinx.common.workflow.service import ServiceWorkflowsImpl
from frinx.common.workflow.task import DecisionTask
from frinx.common.workflow.task import DecisionTaskInputParameters
from frinx.common.workflow.task import SimpleTask
from frinx.common.workflow.task import SimpleTaskInputParameters
from frinx.common.workflow.task import TerminateTask
from frinx.common.workflow.task import TerminateTaskInputParameters
from frinx.common.workflow.workflow import FrontendWFInputFieldType
from frinx.common.workflow.workflow import WorkflowImpl
from frinx.common.workflow.workflow import WorkflowInputField
from frinx.workers.uniconfig.uniconfig_worker import Uniconfig


class UniconfigTransactions(ServiceWorkflowsImpl):
    class UcTxClose(WorkflowImpl):
        name = "UC_TX_close"
        version = 1
        description = "Close a running uniconfig TX in case it was started by the same WF"
        restartable = False
        schema_version = 2
        workflow_status_listener_enabled = True
        labels = ["TX", "MULTIZONE"]

        class WorkflowInput(WorkflowImpl.WorkflowInput):
            started_by_wf = WorkflowInputField(
                name="started_by_wf",
                frontend_default_value="test",
                description="blablabla",
                options=None,
                type=FrontendWFInputFieldType.STRING,
            )

            parent_wf = WorkflowInputField(
                name="parent_wf",
                frontend_default_value="test",
                description="blablabla",
                options=None,
                type=FrontendWFInputFieldType.STRING,
            )

        class WorkflowOutput(WorkflowImpl.WorkflowOutput):
            url: str
            response_code: str
            response_body: dict[str, typing.Any]

        def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:
            # inputs = self.WorkflowInput()

            true_decision_tasks = [
                SimpleTask(
                    name=Uniconfig.UniconfigTxCloseTransaction,
                    task_reference_name="close",
                    input_parameters=SimpleTaskInputParameters(
                        uniconfig_context=workflow_inputs.parent_wf.wf_input
                    ),
                ),
                TerminateTask(
                    name="terminate",
                    task_reference_name="closed_tx",
                    input_parameters=TerminateTaskInputParameters(
                        termination_status=WorkflowStatus.COMPLETED,
                        workflow_output={
                            "closed_current_context": workflow_inputs.parent_wf.wf_input
                        },
                    ),
                ),
            ]

            false_decision_tasks = [
                TerminateTask(
                    name="terminate",
                    task_reference_name="dont_close_parent_tx",
                    input_parameters=TerminateTaskInputParameters(
                        termination_status=WorkflowStatus.COMPLETED,
                        workflow_output={
                            "unclosed_parent_uniconfig_context": workflow_inputs.parent_wf.wf_input
                        },
                    ),
                )
            ]

            self.tasks.append(
                DecisionTask(
                    name="decide_task",
                    task_reference_name="should_close_current_tx",
                    case_expression="$.started_by_wf === $.parent_wf ? 'True' : 'False'",
                    decision_cases={"True": true_decision_tasks},
                    case_value_param="started_by_wf",
                    default_case=false_decision_tasks,
                    input_parameters=DecisionTaskInputParameters(),
                )
            )

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
            uniconfig_context = WorkflowInputField(
                name="uniconfig_context",
                frontend_default_value="uniconfig_context",
                description="blablabla",
                options=None,
                type=FrontendWFInputFieldType.TOGGLE,
            )

            devices = WorkflowInputField(
                name="devices",
                frontend_default_value="test",
                description="blablabla",
                options=None,
                type=FrontendWFInputFieldType.STRING,
            )

            oam_domain = WorkflowInputField(
                name="oam_domain",
                frontend_default_value="test",
                description="blablabla",
                options=None,
                type=FrontendWFInputFieldType.STRING,
            )

        class WorkflowOutput(WorkflowImpl.WorkflowOutput):
            url: str
            response_code: str
            response_body: dict[str, typing.Any]

        def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:
            false_decision_tasks = [
                SimpleTask(
                    name=Uniconfig.UniconfigTxCreateMultizone,
                    task_reference_name="create",
                    input_parameters=SimpleTaskInputParameters(
                        devices="${workflow.input.oam_domain",
                        oam_domain=workflow_inputs.oam_domain.wf_input,
                    ),
                ),
                TerminateTask(
                    name="terminate",
                    task_reference_name="return_new_tx_id",
                    input_parameters=TerminateTaskInputParameters(
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
                    input_parameters=TerminateTaskInputParameters(
                        termination_status=WorkflowStatus.COMPLETED,
                        workflow_output={
                            "uniconfig_context": workflow_inputs.uniconfig_context.wf_input
                        },
                    ),
                )
            ]

            self.tasks.append(
                DecisionTask(
                    name="decide_task",
                    task_reference_name="should_close_current_tx",
                    case_expression="$.parent_tx_multizone ? 'True' : 'False'",
                    decision_cases={"True": true_decision_tasks},
                    default_case=false_decision_tasks,
                    input_parameters=DecisionTaskInputParameters(),
                )
            )
