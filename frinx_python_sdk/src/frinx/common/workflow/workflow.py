from abc import ABC
from abc import abstractmethod
from typing import List
from typing import Optional

from frinx.client.FrinxConductorWrapper import FrinxConductorWrapper
from frinx.common.conductor_enums import TimeoutPolicy
from frinx.common.util import snake_to_camel_case
from frinx.common.workflow.task import WorkflowTaskImpl
from pydantic import BaseModel
from pydantic import Extra
from pydantic import Field


class WorkflowImpl(BaseModel, ABC):
    class WorkflowInput(BaseModel):
        ...

        class Config:
            allow_mutation = False
            extra = Extra.forbid
            validate_all = True

    class WorkflowOutput(BaseModel):
        ...

        class Config:
            allow_mutation = False
            extra = Extra.forbid
            validate_all = True

    name: str
    version: int

    # LABELS, RBAC, DESCRIPTION, INPUT VALUES
    description: str
    labels: Optional[list] = Field(default=None)
    rbac: Optional[List[str]] = Field(default=None)

    # PREDEFINED
    restartable: bool = Field(default=False)
    output_parameters: dict[str, object] = Field(default={})
    input_parameters: List[str] = Field(default=[])
    tasks: list[WorkflowTaskImpl] = Field(default=[])
    timeout_policy: TimeoutPolicy = Field(default=TimeoutPolicy.ALERT_ONLY)
    timeout_seconds: int = Field(default=60)

    owner_app: str = Field(default=None)
    create_time: int = Field(default=None)
    update_time: int = Field(default=None)
    created_by: str = Field(default=None)
    updated_by: str = Field(default=None)
    failure_workflow: str = Field(default=None)
    schema_version: int = Field(default=None)
    workflow_status_listener_enabled: bool = Field(default=None)
    owner_email: str = Field(default=None)
    variables: dict[str, object] = Field(default=None)
    input_template: dict[str, object] = Field(default=None)

    def register(self, cc: FrinxConductorWrapper) -> None:
        cc.updateWorkflow(workflow=self.workflow_builder().json(by_alias=True, exclude_none=True))

    @abstractmethod
    def workflow_builder(self):
        pass

    class Config:
        alias_generator = snake_to_camel_case
        allow_population_by_field_name = True
        validate_assignment = True
        validate_all = True
