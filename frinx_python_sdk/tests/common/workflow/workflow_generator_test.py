import unittest

from frinx.common.conductor_enums import TimeoutPolicy
from frinx.common.workflow.task import SimpleTask
from frinx.common.workflow.task import SimpleTaskInputParameters
from frinx.common.workflow.workflow import FrontendWFInputFieldType
from frinx.common.workflow.workflow import WorkflowImpl
from frinx.common.workflow.workflow import WorkflowInputField
from frinx.workers.http.http_worker import Http as HttpWorker


class TestWorkflowGenerator(unittest.TestCase):
    def test_workflow_build(self):
        class HttpRequest(WorkflowImpl):
            name = "Http_request"
            version = 1
            description = "Simple HTTP request"
            labels = ["HTTP"]
            rbac = ["network-admin"]
            timeout_policy = TimeoutPolicy.TIME_OUT_WORKFLOW
            restartable = True

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

        test_workflow = HttpRequest().dict(exclude_none=True)

        test_mock = {
            "name": "Http_request",
            "version": 1,
            "description": '{"description": "Simple HTTP request", "labels": ["HTTP"], "rbac": ["network-admin"]}',
            "labels": ["HTTP"],
            "rbac": ["network-admin"],
            "restartable": True,
            "output_parameters": {},
            "input_parameters": [
                '{"uri": {"value": "", "description": "Request url", "type": "string", "options": null}}',
                '{"contentType": {"value": "application/json", "description": "Request contentType header", "type": "string", "options": null}}',
                '{"method": {"value": "GET", "description": "Request method", "type": "select", "options": ["GET", "PUT", "POST", "DELETE", "PATCH"]}}',
                '{"headers": {"value": {}, "description": "Request headers", "type": "textarea", "options": null}}',
                '{"body": {"value": {}, "description": "Request body", "type": "textarea", "options": null}}',
                '{"timeout": {"value": 360, "description": "Request timeout", "type": "int", "options": null}}',
            ],
            "tasks": [
                {
                    "name": "HTTP_task",
                    "task_reference_name": "http_task",
                    "type": "SIMPLE",
                    "start_delay": 0,
                    "optional": False,
                    "async_complete": False,
                    "default_case": [],
                    "input_parameters": {
                        "http_request": {
                            "uri": "${workflow.input.uri}",
                            "contentType": "${workflow.input.contentType}",
                            "method": "${workflow.input.method}",
                            "headers": "${workflow.input.headers}",
                            "body": "${workflow.input.body}",
                        }
                    },
                }
            ],
            "timeout_policy": "TIME_OUT_WF",
            "timeout_seconds": 60,
            "input_template": {
                "uri": "",
                "contentType": "application/json",
                "method": "GET",
                "headers": {},
                "body": {},
                "timeout": 360,
            },
        }

        self.assertDictEqual(test_workflow, test_mock)


if __name__ == "__main__":
    unittest.main()
