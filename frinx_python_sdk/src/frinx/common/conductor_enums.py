from enum import Enum


class TaskResultStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    FAILED_WITH_TERMINAL_ERROR = "FAILED_WITH_TERMINAL_ERROR"
    IN_PROGRESS = "IN_PROGRESS"


class WorkflowStatus(str, Enum):
    COMPLETED = ("COMPLETED",)
    FAILED = ("FAILED",)
    PAUSED = ("PAUSED",)
    RUNNING = ("RUNNING",)
    TERMINATED = ("TERMINATED",)
    TIMEOUT_OUT = ("TIMED_OUT",)


class TimeoutPolicy(str, Enum):
    TIME_OUT_WORKFLOW = ("TIME_OUT_WF",)
    ALERT_ONLY = ("ALERT_ONLY",)


class SwitchEvaluatorType(str, Enum):
    JAVASCRIPT = ("javascript",)
    VALUE_PARAM = "value-param"


class RetryLogic(str, Enum):
    FIXED = ("FIXED",)
    EXPONENTIAL_BACKOFF = ("EXPONENTIAL_BACKOFF",)
    LINEAR_BACKOFF = ("LINEAR_BACKOFF",)
