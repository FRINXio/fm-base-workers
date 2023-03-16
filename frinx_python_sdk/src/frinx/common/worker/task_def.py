from typing import Any
from typing import List
from typing import Optional

from frinx.common.conductor_enums import RetryLogic
from frinx.common.conductor_enums import TimeoutPolicy
from frinx.common.util import snake_to_camel_case
from pydantic import BaseModel
from pydantic import Extra
from pydantic import Field


class TaskInput(BaseModel):
    class Config:
        allow_mutation = False
        extra = Extra.forbid
        validate_all = True
        arbitrary_types_allowed = False
        allow_population_by_field_name = False


class TaskOutput(BaseModel):
    class Config:
        allow_mutation = False
        extra = Extra.allow


class TaskDefinition(BaseModel):
    name: str
    description: str
    labels: Optional[list[object]] = Field(default=None)
    rbac: Optional[list[object]] = Field(default=None)
    owner_app: Optional[str] = Field(default=None)
    create_time: Optional[int] = Field(default=None)
    update_time: Optional[int] = Field(default=None)
    created_by: Optional[str] = Field(default=None)
    updated_by: Optional[str] = Field(default=None)
    retry_count: Optional[int] = Field(default=None)
    timeout_seconds: Optional[int] = Field(default=None)
    input_keys: Optional[list[str]] = Field(default=None)
    output_keys: Optional[list[str]] = Field(default=None)
    timeout_policy: Optional[TimeoutPolicy] = Field(default=None)
    retry_logic: Optional[RetryLogic] = Field(default=None)
    retry_delay_seconds: Optional[int] = Field(default=None)
    response_timeout_seconds: Optional[int] = Field(default=None)
    concurrent_execLimit: Optional[int] = Field(default=None)
    input_template: Optional[dict[str, Any]] = Field(default=None)
    rate_limit_per_frequency: Optional[int] = Field(default=None)
    rate_limit_frequency_in_seconds: Optional[int] = Field(default=None)
    isolation_group_id: Optional[str] = Field(default=None)
    execution_name_space: Optional[str] = Field(default=None)
    owner_email: Optional[str] = Field(default=None)
    poll_timeout_seconds: Optional[int] = Field(default=None)
    backoff_scale_factor: Optional[int] = Field(default=None)
    limit_to_thread_count: Optional[int] = Field(default=None)

    class Config:
        # allow_mutation = False
        # extra = Extra.forbid
        validate_assignment = True
        alias_generator = snake_to_camel_case
        allow_population_by_field_name = True
        # TODO  add validators


class DefaultTaskDefinition(BaseModel):
    retry_count: int = 0
    timeout_policy: TimeoutPolicy = TimeoutPolicy.ALERT_ONLY
    timeout_seconds: int = 60
    retry_logic: RetryLogic = RetryLogic.FIXED
    retry_delay_seconds: int = 0
    response_timeout_seconds: int = 59
    rate_limit_per_frequency: int = 0
    rate_limit_frequency_in_seconds: int = 5
    owner_email: str = "x_from"  # TODO import from rest_utils
    limit_to_thread_count: int = 1


class ConductorWorkerError(Exception):
    """Base error of Conductor worker."""


class InvalidTaskInputError(ConductorWorkerError):
    """Error due to invalid input of (simple) task."""


class FailedTaskError(ConductorWorkerError):
    """Exception causing task to fail with provided message instead of full traceback."""

    def __init__(self, error_msg: str) -> None:
        self.error_msg = error_msg
