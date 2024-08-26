from peewee import (
    Model, CharField, TextField, BigIntegerField,
    TimestampField, BooleanField, IntegerField
)
from playhouse.postgres_ext import JSONField
from common.system_util import SystemUtil
from api.ml_controller.ml_utils import RunUtils

_, py_config, _ = RunUtils.get_server_run_configuration()

db = SystemUtil.get_orm_db_conn(py_config)


# 모델 정의
class BaseModel(Model):
    class Meta:
        database = db


class AiConfigServing(BaseModel):
    serving_name = CharField(max_length=255, primary_key=True)
    business_types = TextField(null=True)
    create_dt = TimestampField(null=True)
    inst_type = CharField(max_length=255, null=True)
    metric_ids_json = JSONField(null=True)
    module = CharField(max_length=255, null=True)
    service_on_boot = BooleanField(null=True)
    target_id = CharField(max_length=255, null=True)
    update_dt = TimestampField(null=True)
    update_pkl_dt = TimestampField(null=True)
    train_hyper_params = JSONField(null=True)
    target_list = TextField()

    class Meta:
        table_name = 'ai_config_serving'
