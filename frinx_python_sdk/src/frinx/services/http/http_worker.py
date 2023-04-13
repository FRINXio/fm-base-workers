from __future__ import print_function

import json
from typing import Any
from typing import Optional

import requests
import requests.auth
import requests.utils
from frinx.common.worker.task_result import TaskResult
from frinx.common.worker.task_result import TaskResultStatus
from pydantic import BaseModel


class HttpOutput(BaseModel):
    code: int
    data: dict[str, Any]
    logs: Optional[list[str]] | Optional[str] | None = None
    url: Optional[str] | None = None

    class Config:
        min_anystr_length = 1


def http_task(http_request: dict[str, Any] | str) -> TaskResult:
    if isinstance(http_request, str):
        http_request = json.loads(json.dumps(http_request))

    uri = http_request["uri"]
    if uri is None:
        return TaskResult(
            status=TaskResultStatus.FAILED, output={"output": {"url": uri}}, logs=["URI is empty"]
        )

    method = http_request["method"]
    if method is None or method.upper() not in ["GET", "PUT", "POST", "DELETE", "HEAD", "PATCH"]:
        return TaskResult(
            status=TaskResultStatus.FAILED,
            output={"output": {"url": uri}},
            logs=[f"Method {method} unsupported for {uri}"],
        )

    headers = {}
    if "contentType" in http_request:
        headers["Content-Type"] = http_request["contentType"]
    if "accept" in http_request:
        headers["Accept"] = http_request["accept"]

    additional_headers = http_request["headers"] if "headers" in http_request else {}
    headers.update(additional_headers)

    body = http_request.get("body", {})
    body = body if isinstance(body, str) else json.dumps(body if body else {})

    timeout = http_request["timeout"] if "timeout" in http_request else 60.0
    verify_cert = http_request["verifyCertificate"] if "verifyCertificate" in http_request else True

    cookies = http_request["cookies"] if "cookies" in http_request else {}

    request_auth = None
    if "basicAuth" in http_request:
        if "username" not in http_request["basicAuth"]:
            return TaskResult(
                status=TaskResultStatus.FAILED,
                output={"output": {"url": uri}},
                logs=[f"Basic auth without username for {uri}"],
            )

        if "password" not in http_request["basicAuth"]:
            return TaskResult(
                status=TaskResultStatus.FAILED,
                output={"output": {"url": uri}},
                logs=[f"Basic auth without password for {uri}"],
            )
        request_auth = requests.auth.HTTPBasicAuth(
            http_request["basicAuth"]["username"], http_request["basicAuth"]["password"]
        )

    response = requests.request(
        method,
        uri,
        headers=headers,
        data=body,
        cookies=cookies,
        timeout=timeout,
        auth=request_auth,
        verify=verify_cert,
    )

    if 400 <= response.status_code < 600:
        return TaskResult(
            status=TaskResultStatus.FAILED,
            output={
                "statusCode": response.status_code,
                "response": {"headers": dict(response.headers)},
                "body": response.content.decode("utf-8", "ignore"),
                "cookies": requests.utils.dict_from_cookiejar(response.cookies),
            },
            logs=[
                f"HTTP {response.request.method} request to {response.request.url} succeeded. Headers: {response.request.headers.items()}"
            ],
        )

    return TaskResult(
        status=TaskResultStatus.COMPLETED,
        output={
            "statusCode": response.status_code,
            "response": {"headers": dict(response.headers)},
            "body": response.content.decode("utf-8", "ignore"),
            "cookies": requests.utils.dict_from_cookiejar(response.cookies),
        },
        logs=[
            f"HTTP {response.request.method} request to {response.request.url} succeeded. Headers: {response.request.headers.items()}"
        ],
    )
