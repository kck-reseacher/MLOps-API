from pydantic import BaseModel, Field, Extra, StrictStr
from typing import List, Optional


class UpdateConfigRequestModel(BaseModel):
    sys_id: str = Field(title="시스템ID", default="102")
    inst_type: str = Field(title="인스턴스타입", default="was")
    target_id: str = Field(title="타겟ID", default="214")

    class Config:
        extra = Extra.ignore


class GroupMenuItem(BaseModel):
    service: StrictStr = Field(..., description="AI서비스 명 ex) 'exem_aiops_anls_inst'")
    type: StrictStr = Field(..., description="인스턴스 타입, DB타입의 경우 product_type, ex) 'was', 'ORACLE', 'os'")
    groupId: Optional[int] = Field(None, description="그룹 아이디")
    servingName: Optional[StrictStr] = Field(None,
                                             description="{AI서비스명}\_{인스턴스타입}\_{타겟아이디} ex) 'exem_aiops_anls_inst_was_1201'")
    serviceOnBoot: bool = Field(..., description="부팅 시 실행 여부")

    class Config:
        extra = Extra.ignore


class TargetMenuItem(BaseModel):
    service: StrictStr = Field(..., description="AI서비스 명 ex) 'exem_aiops_anls_inst'")
    servingName: StrictStr = Field(...,
                                   description="{AI서비스명}\_{인스턴스타입}\_{타겟아이디} ex) 'exem_aiops_anls_inst_was_1201'")
    serviceOnBoot: bool = Field(..., description="부팅 시 실행 여부")

    class Config:
        extra = Extra.ignore


class TargetLogItem(BaseModel):
    alertThreshold: int = Field(..., description="희소로그 분당 알림 기준")
    anomalyThreshold: int = Field(..., description="로그이상탐지 수동 임계치 값")
    autoAnomalyThreshold: int = Field(..., description="로그이상탐지 자동 임계치 값")
    excludeKeywords: List[StrictStr] = Field(..., description="희소로그 제외 키워드")
    isLogServiceOn: bool = Field(..., description="로그이상탐지 실시간 추론 여부")
    isParamAuto: bool = Field(..., description="로그이상탐지 임계치 추천 값 자동 지정 여부")
    isSparseServiceOn: bool = Field(..., description="희소로그 실시간 추론 여부")
    rareRate: float = Field(..., description="희소로그 희소율 검출 상한가")
    serviceOnBoot: bool = Field(..., description="부팅 시 실행 여부")
    setName: Optional[StrictStr] = Field(None, description="프리셋 명")
    targetId: StrictStr = Field(..., description="타겟아이디")
    userKeywords: List[StrictStr] = Field(..., description="희소로그 포함 키워드")

    class Config:
        extra = Extra.ignore


class GroupOnOffItem(BaseModel):
    service: StrictStr = Field(..., description="AI서비스 명 ex) 'exem_aiops_anls_inst'")
    type: StrictStr = Field(..., description="인스턴스 타입, DB타입의 경우 product_type, ex) 'was', 'ORACLE', 'os'")
    groupId: int = Field(..., description="그룹 아이디")
    onOff: bool = Field(..., description="그룹 서빙 활성/비활성화 여부")

    class Config:
        extra = Extra.ignore


class TargetOnOffItem(BaseModel):
    service: StrictStr = Field(..., description="AI서비스 명 ex) 'exem_aiops_anls_inst'")
    type: StrictStr = Field(..., description="인스턴스 타입, DB타입의 경우 product_type, ex) 'was', 'ORACLE', 'os', 'syslog'")
    servingName: StrictStr = Field(..., description="{AI서비스명}\_{인스턴스타입}\_{타겟아이디} ex) 'exem_aiops_anls_inst_was_1201'")
    targetId: StrictStr = Field(..., description="타겟 아이디, ex) '1201'")
    onOff: bool = Field(..., description="타겟 서빙 활성/비활성화 여부")

    class Config:
        extra = Extra.ignore
