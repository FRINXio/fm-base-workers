import typing
from typing import Any
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class TransactionMeta(BaseModel):
    transaction_id: Optional[str] = Field(alias="UNICONFIGTXID", default=None)
    uniconfig_server_id: Optional[str] = Field(default=None)


class UniconfigOutput(BaseModel):
    code: int
    data: dict[str, Any]
    logs: Optional[list[str]] | Optional[str] | None = None
    url: Optional[str] | None = None

    class Config:
        min_anystr_length = 1


class UniconfigRpcResponse(BaseModel):
    code: int
    data: Optional[dict[str, Any]] | None = None
    cookies: Optional[TransactionMeta] | None = None


class UniconfigCookies(BaseModel):
    uniconfig_cookies: TransactionMeta

    class Config:
        min_anystr_length = 1


class ClusterWithDevices(BaseModel):
    uc_cluster: str
    device_names: list[str]

    class Config:
        min_anystr_length = 1


UniconfigCookiesMultizone: typing.TypeAlias = dict[str, ClusterWithDevices]


class UniconfigContext(BaseModel):
    started_by_wf: str | None = None
    uniconfig_cookies_multizone: TransactionMeta | None = None

    class Config:
        min_anystr_length = 1


class UniconfigTransactionList(BaseModel):
    uniconfig_context: str | None = None

    class Config:
        min_anystr_length = 1


class UniconfigCommittedContext(BaseModel):
    committed_contexts: list[Any] | None = None

    class Config:
        min_anystr_length = 1


class UniconfigResponse(BaseModel):
    url: str
    transaction_id: str = Field(alias="UNICONFIGTXID")
    response_code: int
    response_body: dict[Any, Any]

    class Config:
        min_anystr_length = 1


class UniconfigRequest(BaseModel):
    cluster: str
    url: str
    data: dict[Any, Any]

    class Config:
        min_anystr_length = 1


class UniconfigConfigBlacklist(BaseModel):
    extension: List[str]  # TODO add default?


class Netconf(BaseModel):
    netconf_node_topology_host: str = Field(..., alias="netconf-node-topology:host")
    netconf_node_topology_port: int = Field(alias="netconf-node-topology:port", default=2022)
    netconf_node_topology_keepalive_delay: int = Field(
        alias="netconf-node-topology:keepalive-delay", default=5
    )
    netconf_node_topology_max_connection_attempts: int = Field(
        alias="netconf-node-topology:max-connection-attempts", default=1
    )
    netconf_node_topology_connection_timeout_millis: int = Field(
        alias="netconf-node-topology:connection-timeout-millis", default=60000
    )
    netconf_node_topology_default_request_timeout_millis: int = Field(
        alias="netconf-node-topology:default-request-timeout-millis", default=60000
    )
    netconf_node_topology_tcp_only: bool = Field(
        alias="netconf-node-topology:tcp-only", default=True
    )
    netconf_node_topology_username: str = Field(..., alias="netconf-node-topology:username")
    netconf_node_topology_password: str = Field(..., alias="netconf-node-topology:password")
    netconf_node_topology_sleep_factor: Optional[float] = Field(
        alias="netconf-node-topology:sleep-factor", default=1.0
    )
    uniconfig_config_uniconfig_native_enabled: Optional[bool] = Field(
        ..., alias="uniconfig-config:uniconfig-native-enabled"
    )
    netconf_node_topology_edit_config_test_option: Optional[str] = Field(
        alias="netconf-node-topology:edit-config-test-option", default="set"
    )
    uniconfig_config_blacklist: Optional[UniconfigConfigBlacklist] = Field(
        ..., alias="uniconfig-config:blacklist"
    )


class NetconfInputBody(BaseModel):
    node_id: str = Field(..., alias="node-id")
    netconf: Netconf


class NetconfMountBody(BaseModel):
    input: NetconfInputBody
