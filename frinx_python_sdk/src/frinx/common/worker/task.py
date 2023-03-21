from typing import Any
from typing import TypeAlias

from pydantic import BaseModel
from pydantic import Extra
from pydantic import Field

WorkflowTask: TypeAlias = dict[str, str]
TaskDef: TypeAlias = dict[str, str]
from frinx.common.util import snake_to_camel_case


class Task(BaseModel):
    input_data: dict[str, object] = Field(default={})
    workflow_task: Any = Field(default=None)
    task_definition: Any = Field(default=None)

    task_type: str = Field(default=None)
    status: str = Field(default=None)
    reference_task_name: str = Field(default=None)
    retry_count: int = Field(default=None)
    seq: int = Field(default=None)
    correlation_id: str = Field(default=None)
    poll_count: int = Field(default=None)
    task_def_name: str = Field(default=None)
    scheduled_time: int = Field(default=None)
    start_time: int = Field(default=None)
    end_time: int = Field(default=None)
    update_time: int = Field(default=None)
    start_delay_in_seconds: int = Field(default=None)
    retried_task_id: str = Field(default=None)
    retried: bool = Field(default=None)
    executed: bool = Field(default=None)
    callback_from_worker: bool = Field(default=None)
    response_timeout_seconds: int = Field(default=None)
    workflow_instance_id: str = Field(default=None)
    workflow_type: str = Field(default=None)
    task_id: str = Field(default=None)
    reason_for_incompletion: str = Field(default=None)
    callback_after_seconds: int = Field(default=None)
    worker_id: str = Field(default=None)
    output_data: dict[str, object] = Field(default=None)
    domain: str = Field(default=None)
    rate_limit_per_frequency: int = Field(default=None)
    rate_limit_frequency_in_seconds: int = Field(default=None)
    external_input_payload_storage_path: str = Field(default=None)
    external_output_payload_storage_path: str = Field(default=None)
    workflow_priority: int = Field(default=None)
    execution_name_space: str = Field(default=None)
    isolation_group_id: str = Field(default=None)
    iteration: int = Field(default=None)
    sub_workflow_id: str = Field(default=None)
    subworkflow_changed: bool = Field(default=None)
    loop_over_task: bool = Field(default=None)
    queue_wait_time: int = Field(default=None)

    class Config:
        allow_mutation = True
        extra = Extra.forbid
        validate_assignment = True
        alias_generator = snake_to_camel_case
        allow_population_by_field_name = True
        # TODO  add validators
