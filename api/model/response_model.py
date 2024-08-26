from typing import Any, List, Union, Dict, Optional
from pydantic import BaseModel, Field


class MsgItem(BaseModel):
    anomaly_threshold: int


class RangeItem(BaseModel):
    msg: MsgItem


class DigcnItem(BaseModel):
    range: RangeItem
    use: bool
    preset: Optional[Dict]


class SparselogItem(BaseModel):
    include_keyword: str
    rare_rate: float
    use: bool
    exclude_keyword: str
    alert_threshold: int


class ServiceItem(BaseModel):
    targetId: str
    digcn: DigcnItem
    sparselog: SparselogItem


class DataItem(BaseModel):
    sysId: int
    targetId: str
    service: ServiceItem
    train: Dict[str, Any]


class LogInfoResponseModel(BaseModel):
    success: bool
    data: List[DataItem]
    message: Union[str, Any]
    error_code: Union[str, Any]


class ResponseModel(BaseModel):
    success: bool
    message: Optional[str] = None
    total: int
    data: Optional[Any] = None
