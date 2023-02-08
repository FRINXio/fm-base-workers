from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import Extra


class TaskInput(BaseModel):
    class Config:
        allow_mutation = False
        extra = Extra.forbid
        validate_all = True


class TaskOutput(BaseModel):
    class Config:
        allow_mutation = False
        extra = Extra.allow


class TaskDefinition(BaseModel):
    name: str
    description: str
    labels: Optional[list] = None
    rbac: Optional[list[str]] = None
    ownerApp: Optional[str] = None
    createTime: Optional[int] = None
    updateTime: Optional[int] = None
    createdBy: Optional[str] = None
    updatedBy: Optional[str] = None
    retryCount: Optional[int] = None
    timeoutSeconds: Optional[int] = None
    inputKeys: Optional[list[str]] = None
    outputKeys: Optional[list[str]] = None
    timeoutPolicy: Optional[str] = None
    retryLogic: Optional[str] = None
    retryDelaySeconds: Optional[int] = None
    responseTimeoutSeconds: Optional[int] = None
    concurrentExecLimit: Optional[int] = None
    inputTemplate: Optional[dict[str, Any]] = None
    rateLimitPerFrequency: Optional[int] = None
    rateLimitFrequencyInSeconds: Optional[int] = None
    isolationGroupId: Optional[str] = None
    executionNameSpace: Optional[str] = None
    ownerEmail: Optional[str] = None
    pollTimeoutSeconds: Optional[int] = None
    backoffScaleFactor: Optional[int] = None

    class Config:
        allow_mutation = False
        extra = Extra.forbid


class DefaultTaskDefinition(BaseModel):
    retryCount: int = 0
    timeoutPolicy: str = "TIME_OUT_WF"
    timeoutSeconds: int = 60
    retryLogic: str = "FIXED"
    retryDelaySeconds: int = 0
    responseTimeoutSeconds: int = 59
    rateLimitPerFrequency: int = 0
    rateLimitFrequencyInSeconds: int = 5
    ownerEmail: str = "x_from"  # TODO import from rest_utils
    backoffScaleFactor: int = 1


class ConductorWorkerError(Exception):
    """Base error of Conductor worker."""


class InvalidTaskInputError(ConductorWorkerError):
    """Error due to invalid input of (simple) task."""


class FailedTaskError(ConductorWorkerError):
    """Exception causing task to fail with provided message instead of full traceback."""

    def __init__(self, error_msg: str) -> None:
        self.error_msg = error_msg
