import copy
import random
from typing import Any

from frinx.common.conductor_enums import TaskResultStatus
from frinx.common.worker.service import ServiceWorkersImpl
from frinx.common.worker.task import Task
from frinx.common.worker.task_def import TaskDefinition
from frinx.common.worker.task_def import TaskInput
from frinx.common.worker.task_def import TaskOutput
from frinx.common.worker.task_result import TaskResult
from frinx.common.worker.worker import WorkerImpl


class TestWorker(ServiceWorkersImpl):
    class Echo(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "TEST_echo"
            description = "testing purposes: returns input unchanged"
            labels = ["TEST"]
            timeout_seconds = 60
            response_timeout_seconds = 60

        class WorkerInput(TaskInput):
            input: str

        class WorkerOutput(TaskOutput):
            output: str

        def execute(self, task: Task) -> TaskResult:
            task_result = TaskResult(
                status=TaskResultStatus.COMPLETED, logs=["Echo worker invoked successfully"]
            )
            task_result.add_output_data("output", task.input_data.get("input", ""))
            return task_result

    ###############################################################################

    class Sleep(WorkerImpl):
        DEFAULT_SLEEP = 10

        class WorkerDefinition(TaskDefinition):
            name = "TEST_sleep"
            description = "testing purposes: sleep"
            labels = ["TEST"]
            timeout_seconds = 600
            response_timeout_seconds = 600

        class WorkerInput(TaskInput):
            time: int

        class WorkerOutput(TaskOutput):
            time: int

        def execute(self, task: Task) -> TaskResult:
            sleep = task.input_data.get("time", self.DEFAULT_SLEEP)
            if sleep < 0 or sleep > 600:
                return TaskResult(
                    status=TaskResultStatus.FAILED,
                    logs=["Invalid sleep time, must be > 0 and < 600"],
                )

            import time

            task_result = TaskResult(
                status=TaskResultStatus.COMPLETED, logs=["Sleep worker invoked. Sleeping"]
            )
            time.sleep(sleep)
            task_result.add_output_data("time", sleep)
            return task_result

    ###############################################################################

    class DynamicForkGenerator(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "TEST_dynamic_fork_generate"
            description = "testing purposes: generate dynamic fork tasks"
            labels = ["TEST"]
            timeout_seconds = 60
            response_timeout_seconds = 60

        class WorkerInput(TaskInput):
            wf_count: int
            wf_name: str
            wf_inputs: dict

        class WorkerOutput(TaskOutput):
            dynamic_tasks_i: dict
            dynamic_tasks: list

        def execute(self, task: Task) -> TaskResult:
            wf_count = task.input_data.get("wf_count", 10)
            wf_name = task.input_data.get("wf_name", "Test_workflow")
            wf_inputs = task.input_data.get("wf_inputs", {})

            dynamic_tasks = []
            dynamic_tasks_i = {}

            for task_ref in range(0, wf_count):
                dynamic_tasks.append(
                    {
                        "name": "sub_task",
                        "taskReferenceName": str(task_ref),
                        "type": "SUB_WORKFLOW",
                        "subWorkflowParam": {"name": wf_name, "version": 1},
                    }
                )
                dynamic_tasks_i[str(task_ref)] = wf_inputs

            task_result = TaskResult(
                status=TaskResultStatus.COMPLETED,
                logs=["Dynamic fork generator worker invoked successfully"],
            )
            task_result.add_output_data("dynamic_tasks_i", dynamic_tasks_i)
            task_result.add_output_data("dynamic_tasks", dynamic_tasks)

            return task_result

    class LoremIpsum(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "TEST_lorem_ipsum"
            description = "testing purposes: text generator"
            labels = ["TEST"]
            timeout_seconds = 60
            response_timeout_seconds = 60

        class WorkerInput(TaskInput):
            num_paragraphs: int
            num_sentences: int
            num_words: int

        class WorkerOutput(TaskOutput):
            text: str
            bytes: int

        def execute(self, task: Task) -> TaskResult:
            text = generate_text(
                num_paragraphs=task.input_data.get("num_paragraphs", 3),
                num_sentences=task.input_data.get("num_sentences", 3),
                num_words=task.input_data.get("num_words", 3),
            )
            task_result = TaskResult(
                status=TaskResultStatus.COMPLETED, logs=["Lorem ipsum worker invoked successfully"]
            )
            task_result.add_output_data("text", text)
            task_result.add_output_data("bytes", len(text.encode("utf-8")))

            return task_result


WORDS = ["lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit"]


def generate_sentence(num_words: int):
    sentence = []
    for i in range(num_words):
        sentence.append(random.choice(WORDS))
    return " ".join(sentence).capitalize() + "."


def generate_paragraph(num_sentences: int, num_words: int):
    paragraph = []
    for i in range(num_sentences):
        paragraph.append(generate_sentence(num_words))
    return " ".join(paragraph)


def generate_text(num_paragraphs: int, num_sentences: int, num_words: int):
    text = []
    for i in range(num_paragraphs):
        text.append(generate_paragraph(num_sentences, num_words))
    return "\n\n".join(text)
