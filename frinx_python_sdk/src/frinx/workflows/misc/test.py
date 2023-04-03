from frinx.common.workflow.service import ServiceWorkflowsImpl
from frinx.common.workflow.task import DynamicForkTask
from frinx.common.workflow.task import DynamicForkTaskInputParameters
from frinx.common.workflow.task import JoinTask
from frinx.common.workflow.task import SimpleTask
from frinx.common.workflow.task import SimpleTaskInputParameters
from frinx.common.workflow.workflow import FrontendWFInputFieldType
from frinx.common.workflow.workflow import WorkflowImpl
from frinx.common.workflow.workflow import WorkflowInputField
from frinx.workers.test.test_worker import TestWorker


class TestWorkflow(WorkflowImpl):
    name = "Test_workflow"
    version = 1
    description = "Test workflow built from test workers"
    labels = ["TEST"]
    timeout_seconds = 60 * 5

    class WorkflowInput(WorkflowImpl.WorkflowInput):
        num_paragraphs = WorkflowInputField(
            name="num_paragraphs",
            frontend_default_value=10,
            description="Paragraphs to generate",
            type=FrontendWFInputFieldType.INT,
        )

        num_sentences = WorkflowInputField(
            name="num_sentences",
            frontend_default_value=10,
            description="Sentences to generate per paragraph",
            type=FrontendWFInputFieldType.INT,
        )

        num_words = WorkflowInputField(
            name="num_words",
            frontend_default_value=10,
            description="Words to generate per sentence",
            type=FrontendWFInputFieldType.INT,
        )

        sleep_time = WorkflowInputField(
            name="sleep_time",
            frontend_default_value="10",
            description="How many seconds to sleep during the workflow",
            type=FrontendWFInputFieldType.INT,
        )

    class WorkflowOutput(WorkflowImpl.WorkflowOutput):
        text: str
        bytes: int

    def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:
        self.tasks.append(
            SimpleTask(
                name=TestWorker.LoremIpsum,
                task_reference_name="generate",
                input_parameters=SimpleTaskInputParameters(
                    num_paragraphs=workflow_inputs.num_paragraphs.wf_input,
                    num_sentences=workflow_inputs.num_sentences.wf_input,
                    num_words=workflow_inputs.num_words.wf_input,
                ),
            )
        )
        self.tasks.append(
            SimpleTask(
                name=TestWorker.Sleep,
                task_reference_name="sleep",
                input_parameters=SimpleTaskInputParameters(
                    time=workflow_inputs.sleep_time.wf_input
                ),
            )
        )
        self.tasks.append(
            SimpleTask(
                name=TestWorker.Echo,
                task_reference_name="echo",
                input_parameters=SimpleTaskInputParameters(input="${generate.output.text}"),
            )
        )

        self.output_parameters["text"] = "${echo.output.output}"
        self.output_parameters["bytes"] = "${generate.output.bytes}"


class TestForkWorkflow(WorkflowImpl):
    name = "Test_fork_workflow"
    version = 1
    description = "Test workflows executed in a parallel, dynamic fork"
    labels = ["TEST"]
    timeout_seconds = 60 * 5

    class WorkflowInput(TestWorkflow.WorkflowInput):
        fork_count = WorkflowInputField(
            name="fork_count",
            frontend_default_value=10,
            description="How many forks to execute in parallel",
            type=FrontendWFInputFieldType.INT,
        )

    class WorkflowOutput(WorkflowImpl.WorkflowOutput):
        pass

    def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:
        self.tasks.append(
            SimpleTask(
                name=TestWorker.DynamicForkGenerator,
                task_reference_name="fork_generator",
                input_parameters=SimpleTaskInputParameters(
                    wf_count=workflow_inputs.fork_count.wf_input,
                    wf_name="Test_workflow",
                    wf_inputs={
                        "num_words": workflow_inputs.num_words.wf_input,
                        "num_sentences": workflow_inputs.num_sentences.wf_input,
                        "num_paragraphs": workflow_inputs.num_paragraphs.wf_input,
                        "sleep_time": workflow_inputs.sleep_time.wf_input,
                    },
                ),
            )
        )

        self.tasks.append(
            DynamicForkTask(
                name="dyn_fork",
                task_reference_name="dyn_fork",
                dynamicForkTasksParam="dynamic_tasks",
                dynamic_fork_tasks_input_param_name="dynamic_tasks_input",
                input_parameters=DynamicForkTaskInputParameters(
                    dynamic_tasks="${fork_generator.output.dynamic_tasks}",
                    dynamic_tasks_input="${fork_generator.output.dynamic_tasks_i}",
                ),
            )
        )

        self.tasks.append(JoinTask(name="dyn_fork_join", task_reference_name="dyn_fork_join"))
