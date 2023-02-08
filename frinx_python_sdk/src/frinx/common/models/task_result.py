import pprint
import re  # noqa: F401
from typing import Any

import six
from conductor.client.http.models.task_result_status import TaskResultStatus


class TaskResult(object):

    swagger_types = {"status": "str", "output": "dict(str, object)", "logs": "list[TaskExecLog]"}

    attribute_map = {"status": "status", "output": "output", "logs": "logs"}

    def __init__(self, status=None, output=None, logs=None) -> None:  # noqa: E501

        self._status: str
        self._output: dict[str, Any] = {}
        self._logs: list[str] = []

        if status is not None:
            self.status = status
        if output is not None:
            self.output = output
        if logs is not None:
            self.logs = logs

    @property
    def status(self) -> str:
        """Gets the status of this TaskResult.  # noqa: E501


        :return: The status of this TaskResult.  # noqa: E501
        :rtype: str
        """
        return self._status

    @status.setter
    def status(self, status: str) -> None:
        """Sets the status of this TaskResult.


        :param status: The status of this TaskResult.  # noqa: E501
        :type: str
        """
        allowed_values = [task_result_status.name for task_result_status in TaskResultStatus]
        if status not in allowed_values:
            raise ValueError(
                "Invalid value for `status` ({0}), must be one of {1}".format(  # noqa: E501
                    status, allowed_values
                )
            )

        self._status = TaskResultStatus[status].value

    @property
    def output(self) -> dict[str, object]:
        """Gets the output_data of this TaskResult.  # noqa: E501


        :return: The output_data of this TaskResult.  # noqa: E501
        :rtype: dict(str, object)
        """
        return self._output

    @output.setter
    def output(self, output_data: dict[str, Any]) -> None:
        """Sets the output_data of this TaskResult.


        :param output_data: The output_data of this TaskResult.  # noqa: E501
        :type: dict(str, object)
        """

        self._output = output_data

    @property
    def logs(self) -> list[str]:
        """Gets the logs of this TaskResult.  # noqa: E501


        :return: The logs of this TaskResult.  # noqa: E501
        :rtype: list[TaskExecLog]
        """
        return self._logs

    @logs.setter
    def logs(self, logs: Any) -> None:
        """Sets the logs of this TaskResult.


        :param logs: The logs of this TaskResult.  # noqa: E501
        :type: list[TaskExecLog]
        """
        self._logs = logs

        if type(logs) is str:
            self._logs = [logs]

    def to_dict(self) -> dict[str, Any]:
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(
                    map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value)
                )
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(
                    map(
                        lambda item: (item[0], item[1].to_dict())
                        if hasattr(item[1], "to_dict")
                        else item,
                        value.items(),
                    )
                )
            else:
                result[attr] = value
        if issubclass(TaskResult, dict):
            # for key, value in self.items():
            for key, value in self.__dict__.items():
                result[key] = value

        return result

    def to_str(self) -> str:
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self) -> str:
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other: Any) -> Any:
        """Returns true if both objects are equal"""
        if not isinstance(other, TaskResult):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other: Any) -> Any:
        """Returns true if both objects are not equal"""
        return not self == other

    def add_output_data(self, key: str, value: Any) -> None:
        if self.output is None:
            self.output = {}
        self.output[key] = value
