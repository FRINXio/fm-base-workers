import typing
from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class TransactionMeta(BaseModel):
    transaction_id: Optional[str] = Field(alias="UNICONFIGTXID", default=None)
    uniconfig_server_id: Optional[str] = Field(default=None)


class UniconfigOutput(BaseModel):
    code: int
    data: dict
    logs: Optional[list] | Optional[str] = None
    url: Optional[str] = None

    class Config:
        min_anystr_length = 1


class UniconfigRpcResponse(BaseModel):
    code: int
    data: Optional[dict] = None
    cookies: Optional[TransactionMeta] = None


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
    uniconfig_cookies_multizone: TransactionMeta = None

    class Config:
        min_anystr_length = 1


class UniconfigTransactionList(BaseModel):
    uniconfig_context: str | None = None

    class Config:
        min_anystr_length = 1


class UniconfigCommittedContext(BaseModel):
    committed_contexts: list | None = None

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
