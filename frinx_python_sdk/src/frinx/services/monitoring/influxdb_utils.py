from typing import Any
from typing import Optional

from frinx.common.frinx_rest import influxdb_url_base
from influxdb_client import InfluxDBClient
from pydantic import BaseModel


class InfluxDbWrapper:
    def __init__(self, token: str, org: str) -> None:
        # TODO change to influxdb:8086
        self.url = "http://localhost:8086"
        self.token = token
        self.org = org

    def client(self) -> InfluxDBClient:
        return InfluxDBClient(url=self.url, token=self.token, org=self.org)


class InfluxOutput(BaseModel):
    code: int
    data: dict[str, Any]
    logs: Optional[list[str]] | Optional[str] = None
