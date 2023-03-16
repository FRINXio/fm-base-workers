from typing import Optional

from frinx.common.workflow.service import ServiceWorkflowsImpl
from frinx.common.workflow.task import SimpleTask
from frinx.common.workflow.task import SimpleTaskInputParameters
from frinx.common.workflow.workflow import FrontendWFInputFieldType
from frinx.common.workflow.workflow import WorkflowImpl
from frinx.common.workflow.workflow import WorkflowInputField
from frinx.workers.monitoring.influxdb_workers import Influx


class InfluxWF(ServiceWorkflowsImpl):
    class InfluxCreateBucket(WorkflowImpl):
        name = "Influx_create_bucket"
        version = 1
        description = "Create bucket"
        labels = ["INFLUX"]

        class WorkflowInput(WorkflowImpl.WorkflowInput):
            org = WorkflowInputField(
                name="org",
                frontend_default_value="frinx-machine",
                description="Organization name",
                type=FrontendWFInputFieldType.STRING,
            )

            token = WorkflowInputField(
                name="token",
                frontend_default_value="",
                description="Organization token",
                type=FrontendWFInputFieldType.STRING,
            )

            bucket = WorkflowInputField(
                name="bucket",
                frontend_default_value="frinx",
                description="Organization token",
                type=FrontendWFInputFieldType.STRING,
            )

        class WorkflowOutput(WorkflowImpl.WorkflowOutput):
            data: str

        def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:
            self.tasks.append(
                SimpleTask(
                    name=Influx.InfluxCreateBucket,
                    task_reference_name="create_bucket",
                    input_parameters=SimpleTaskInputParameters(
                        org=workflow_inputs.org.wf_input,
                        token=workflow_inputs.token.wf_input,
                        bucket=workflow_inputs.bucket.wf_input,
                    ),
                )
            )

    class InfluxQueryData(WorkflowImpl):
        name = "INFLUX_query_data"
        version = 1
        description = "Query data from InfluxDB"
        labels = ["INFLUX"]

        class WorkflowInput(WorkflowImpl.WorkflowInput):
            org = WorkflowInputField(
                name="org",
                frontend_default_value="frinx-machine",
                description="Organization name",
                type=FrontendWFInputFieldType.STRING,
            )

            token = WorkflowInputField(
                name="token",
                frontend_default_value="",
                description="Organization token",
                type=FrontendWFInputFieldType.STRING,
            )

            query = WorkflowInputField(
                name="query",
                frontend_default_value="",
                description="Query expression",
                type=FrontendWFInputFieldType.TEXTAREA,
            )

            format_data: WorkflowInputField = WorkflowInputField(
                name="format_data",
                frontend_default_value="table, _measurement, _value, host",
                description="Query expression",
                type=FrontendWFInputFieldType.STRING,
            )

        class WorkflowOutput(WorkflowImpl.WorkflowOutput):
            data: str

        def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:
            self.tasks.append(
                SimpleTask(
                    name=Influx.InfluxQueryData,
                    task_reference_name="query_data",
                    input_parameters=SimpleTaskInputParameters(
                        org=workflow_inputs.org.wf_input,
                        token=workflow_inputs.token.wf_input,
                        query=workflow_inputs.query.wf_input,
                        format_data=workflow_inputs.format_data.wf_input,
                    ),
                )
            )

    class InfluxWriteData(WorkflowImpl):
        name = "INFLUX_write_data"
        version = 1
        description = "Write data to InfluxDB"
        labels = ["INFLUX"]

        class WorkflowInput(WorkflowImpl.WorkflowInput):
            org = WorkflowInputField(
                name="org",
                frontend_default_value="frinx-machine",
                description="Organization name",
                type=FrontendWFInputFieldType.STRING,
            )

            token = WorkflowInputField(
                name="token",
                frontend_default_value="",
                description="Organization token",
                type=FrontendWFInputFieldType.STRING,
            )

            bucket = WorkflowInputField(
                name="bucket",
                frontend_default_value="frinx",
                description="Bucket name",
                type=FrontendWFInputFieldType.STRING,
            )

            measurement = WorkflowInputField(
                name="measurement",
                frontend_default_value="",
                description="Measurement name",
                type=FrontendWFInputFieldType.STRING,
            )

            tags = WorkflowInputField(
                name="tags",
                frontend_default_value="",
                description="Tags dictionary",
                type=FrontendWFInputFieldType.TEXTAREA,
            )

            fields = WorkflowInputField(
                name="fields",
                frontend_default_value="",
                description="Fields dictionary",
                type=FrontendWFInputFieldType.TEXTAREA,
            )

        class WorkflowOutput(WorkflowImpl.WorkflowOutput):
            data: str

        def workflow_builder(self, workflow_inputs: WorkflowInput) -> None:
            self.tasks.append(
                SimpleTask(
                    name=Influx.InfluxWriteData,
                    task_reference_name="write_data",
                    input_parameters=SimpleTaskInputParameters(
                        org=workflow_inputs.org.wf_input,
                        token=workflow_inputs.token.wf_input,
                        bucket=workflow_inputs.bucket.wf_input,
                        measurement=workflow_inputs.measurement.wf_input,
                        tags=workflow_inputs.tags.wf_input,
                        fields=workflow_inputs.fields.wf_input,
                    ),
                )
            )
