from peewee import (
    Model, CharField, DoubleField,
    BooleanField, IntegerField, TextField, TimestampField
)
from common.system_util import SystemUtil
from api.ml_controller.ml_utils import RunUtils

_, py_config, _ = RunUtils.get_server_run_configuration()
db = SystemUtil.get_orm_db_conn(py_config)


# 모델 정의
class BaseModel(Model):
    class Meta:
        database = db

class AiConfigSparse(BaseModel):
    config_serving_log_sparse_id = IntegerField(primary_key=True)
    log_id = IntegerField(unique=True)
    alert_threshold = IntegerField()
    rare_rate = DoubleField(null=True)
    is_service_on = BooleanField(default=False)

    class Meta:
        table_name = 'ai_config_serving_log_sparse'


class AiConfigLogKeyword(BaseModel):
    config_serving_log_keyword_id = IntegerField(primary_key=True)
    log_id = IntegerField()
    keyword = CharField()
    keyword_type = CharField()

    class Meta:
        table_name = 'ai_config_serving_log_keyword'


class XaiopsConfigLog(BaseModel):
    log_id = IntegerField(primary_key=True)
    target_id = CharField()
    log_name = CharField(null=True)
    log_path = CharField(null=True)
    log_category = CharField()
    desc = CharField(null=True)
    host_id = IntegerField(null=True)
    host_name = CharField()
    inst_id = IntegerField(null=True)
    auto_training = BooleanField()
    enable = BooleanField(default=True)
    is_service_on = BooleanField(default=False)
    regset_id = IntegerField(null=True)
    date_pattern = CharField(null=True)
    log_type = CharField()

    class Meta:
        table_name = 'xaiops_config_log'


class AiConfigLogRegex(BaseModel):
    key = IntegerField(primary_key=True)
    delimiter = BooleanField()
    regex = CharField()
    regset_id = IntegerField()
    replace_str = CharField()

    class Meta:
        table_name = 'ai_config_log_regex'


class AiConfigLogRegexPreset(BaseModel):
    regset_id = IntegerField(primary_key=True)
    default_preset = BooleanField()
    set_name = CharField()

    class Meta:
        table_name = 'ai_config_log_regex_preset'

class AiConfigServingLogDigcn(BaseModel):
    config_serving_log_digcn_id = IntegerField(primary_key=True)
    module = CharField(max_length=300)
    inst_type = CharField(max_length=30)
    target_id = CharField(max_length=300)
    hyper_type = TextField()
    metric_id = CharField()
    params = TextField()
    created_dt = TimestampField(null=True)
    modified_dt = TimestampField(null=True)
    is_params_auto = BooleanField(default=False)
    recommend_param = CharField(null=True)

    class Meta:
        table_name = 'ai_config_serving_log_digcn'