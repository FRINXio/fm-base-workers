from frinx.common.workflow.task import SimpleTask
from frinx.common.workflow.task import SimpleTaskInputParameters
from frinx.common.workflow.workflow import FrontendWFInputFieldType
from frinx.common.workflow.workflow import WorkflowImpl
from frinx.common.workflow.workflow import WorkflowInputField
from frinx.workers.http.http_worker import Http as HttpWorker


class HttpRequest(WorkflowImpl):
    name = "Http_request"
    version = 1
    description = "Simple HTTP request"
    labels = ["HTTP"]

    class WorkflowInput(WorkflowImpl.WorkflowInput):
        uri = WorkflowInputField(
            name="uri",
            frontend_default_value="",
            description="Request url",
            type=FrontendWFInputFieldType.STRING,
        )

        contentType = WorkflowInputField(
            name="contentType",
            frontend_default_value="application/json",
            description="Request contentType header",
            type=FrontendWFInputFieldType.STRING,
        )

        method = WorkflowInputField(
            name="method",
            frontend_default_value="GET",
            description="Request method",
            options=["GET", "PUT", "POST", "DELETE", "PATCH"],
            type=FrontendWFInputFieldType.SELECT,
        )

        headers = WorkflowInputField(
            name="headers",
            frontend_default_value={},
            description="Request headers",
            type=FrontendWFInputFieldType.TEXTAREA,
        )

        body = WorkflowInputField(
            name="body",
            frontend_default_value={},
            description="Request body",
            type=FrontendWFInputFieldType.TEXTAREA,
        )

        timeout = WorkflowInputField(
            name="timeout",
            frontend_default_value=360,
            description="Request timeout",
            type=FrontendWFInputFieldType.INT,
        )

    class WorkflowOutput(WorkflowImpl.WorkflowOutput):
        data: str

    def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:
        http_request = {
            "uri": workflow_inputs.uri.wf_input,
            "contentType": workflow_inputs.contentType.wf_input,
            "method": workflow_inputs.method.wf_input,
            "headers": workflow_inputs.headers.wf_input,
            "body": workflow_inputs.body.wf_input,
        }

        self.tasks.append(
            SimpleTask(
                name=HttpWorker.HttpTask,
                task_reference_name="http_task",
                input_parameters=SimpleTaskInputParameters(http_request=http_request),
            )
        )
