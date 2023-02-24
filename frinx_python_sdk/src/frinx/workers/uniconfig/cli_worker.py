from frinx.common.conductor_enums import TaskResultStatus
from frinx.common.worker.service import ServiceWorkersImpl
from frinx.common.worker.task import Task
from frinx.common.worker.task_def import TaskDefinition
from frinx.common.worker.task_def import TaskInput
from frinx.common.worker.task_def import TaskOutput
from frinx.common.worker.task_result import TaskResult
from frinx.common.worker.worker import WorkerImpl
from frinx.services.uniconfig import cli_worker
from frinx.services.uniconfig.models import UniconfigOutput


class CLI(ServiceWorkersImpl):
    class CliMountCli(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "CLI_mount_cli"
            description = "mount a CLI device"
            labels = ["BASIC", "CLI"]
            timeout_seconds = 600
            response_timeout_seconds = 600

        class WorkerInput(TaskInput):
            device_id: str
            type: str
            version: str
            host: str
            protocol: str
            port: str
            username: str
            password: str

        class WorkerOutput(TaskOutput):
            url: str
            response_body: dict
            response_code: int

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = cli_worker.execute_mount_cli(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class CliUnmountCli(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "CLI_unmount_cli"
            description = "unmount a CLI device"
            labels = ["BASIC", "CLI"]
            timeout_seconds = 600
            response_timeout_seconds = 600

        class WorkerInput(TaskInput):
            device_id: str

        class WorkerOutput(TaskOutput):
            url: str
            response_body: dict
            response_code: int

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = cli_worker.execute_unmount_cli(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class CliExecuteAndReadRpcCli(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "CLI_execute_and_read_rpc_cli"
            description = "execute commands for a CLI device"
            labels = ["BASIC", "CLI"]
            timeout_seconds = 600
            response_timeout_seconds = 600

        class WorkerInput(TaskInput):
            device_id: str
            template: str
            params: str
            uniconfig_context: str
            output_timer: str

        class WorkerOutput(TaskOutput):
            url: str
            response_body: dict
            response_code: int

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = cli_worker.execute_and_read_rpc_cli(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class CliGetCliJournal(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "CLI_get_cli_journal"
            description = "Read cli journal for a device"
            labels = ["BASIC", "CLI"]
            response_timeout_seconds = 10

        class WorkerInput(TaskInput):
            device_id: str
            uniconfig_context: str

        class WorkerOutput(TaskOutput):
            url: str
            response_body: dict
            response_code: int

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = cli_worker.execute_get_cli_journal(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class CliExecuteCli(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "CLI_execute_cli"
            description = "execute commands for a CLI device"
            labels = ["BASIC", "CLI"]
            timeout_seconds = 60
            response_timeout_seconds = 60

        class WorkerInput(TaskInput):
            device_id: str
            template: str
            params: str
            uniconfig_context: str

        class WorkerOutput(TaskOutput):
            url: str
            response_body: dict
            response_code: int

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = cli_worker.execute_cli(**task.input_data)
            return response_handler(response, task_result)

    ###############################################################################

    class CliExecuteAndExpectCli(WorkerImpl):
        class WorkerDefinition(TaskDefinition):
            name = "CLI_execute_and_expect_cli"
            description = "execute commands for a CLI device"
            labels = ["BASIC", "CLI"]
            timeout_seconds = 60
            response_timeout_seconds = 60

        class WorkerInput(TaskInput):
            device_id: str
            template: str
            params: str
            uniconfig_context: str

        class WorkerOutput(TaskOutput):
            url: str
            response_body: dict
            response_code: int

        def execute(self, task: Task, task_result: TaskResult) -> TaskResult:
            response = cli_worker.execute_and_expect_cli(**task.input_data)
            return response_handler(response, task_result)


def response_handler(response: UniconfigOutput, task_result: TaskResult) -> TaskResult:
    match response.code:
        case 200 | 201:
            task_result.status = TaskResultStatus.COMPLETED
            if response.code:
                task_result.add_output_data("response_code", response.code)
            if response.data:
                task_result.add_output_data("response_body", response.data)
            if response.url:
                task_result.add_output_data("url", response.url)
            if response.logs:
                task_result.logs = response.logs

            return task_result
        case _:
            task_result.status = TaskResultStatus.FAILED
            task_result.logs = task_result.logs or str(response)
            if response.code:
                task_result.add_output_data("response_code", response.code)
            if response.data:
                task_result.add_output_data("response_body", response.data)
            if response.url:
                task_result.add_output_data("url", response.url)
            return task_result
