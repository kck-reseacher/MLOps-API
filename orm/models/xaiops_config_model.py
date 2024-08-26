from peewee import (
    Model, AutoField, CharField, TextField, DoubleField, BigIntegerField,
    TimestampField, BooleanField, IntegerField, ForeignKeyField, BigAutoField, SQL
)

from api.ml_controller.ml_utils import RunUtils
from common.system_util import SystemUtil

_, py_config, _ = RunUtils.get_server_run_configuration()

db = SystemUtil.get_orm_db_conn(py_config)


# 모델 정의
class BaseModel(Model):
    class Meta:
        database = db


class XaiopsConfigHost(BaseModel):
    host_id = AutoField(primary_key=True)  # Auto-incremented primary key
    addr = CharField(max_length=255, null=True)
    auto_training = BooleanField()
    cpu_type = CharField(max_length=255, null=True)
    desc = CharField(max_length=255, null=True)
    enable = BooleanField(null=True)
    host_name = CharField(max_length=255)
    is_virtual = BooleanField()
    name = CharField(max_length=255)
    os_info = CharField(max_length=255, null=True)
    os_version = CharField(max_length=255, null=True)
    parent_id = IntegerField(null=True)
    parent_name = CharField(max_length=255, null=True)
    target_id = CharField(max_length=255, unique=True)
    load_fcst_enable = BooleanField(default=False)
    dbsln_enable = BooleanField(default=False)

    class Meta:
        table_name = 'xaiops_config_host'
        constraints = [
            SQL('CONSTRAINT xaiops_host_pkey PRIMARY KEY (host_id)'),
        ]


class XaiopsConfigHostGroup(BaseModel):
    host_group_id = AutoField(primary_key=True)
    host_group_name = CharField(max_length=255)
    host_group_order = IntegerField(default=1)
    auto_training = BooleanField(default=False)

    class Meta:
        table_name = 'xaiops_config_host_group'


class XaiopsConfigHostGroupMapHost(BaseModel):
    config_host_group_map_host_id = AutoField(primary_key=True)
    host_id = ForeignKeyField(XaiopsConfigHost, backref='host_group_maps', null=True, on_delete='CASCADE')
    host_group_id = ForeignKeyField(XaiopsConfigHostGroup, backref='host_group_maps', null=True, on_delete='CASCADE')

    class Meta:
        table_name = 'xaiops_config_host_group_map_host'
        indexes = (
            (('host_group_id', 'host_id'), True),  # Unique constraint on (host_group_id, host_id)
        )
        constraints = [
            SQL('FOREIGN KEY (host_group_id) REFERENCES xaiops_config_host_group(host_group_id)'),
            SQL('FOREIGN KEY (host_id) REFERENCES xaiops_config_host(host_id)')
        ]


class XaiopsConfigInstance(BaseModel):
    inst_id = AutoField(primary_key=True)
    target_id = CharField(max_length=300)
    inst_type = CharField(max_length=300)
    host_id = ForeignKeyField(XaiopsConfigHost, backref='instances', null=True, on_delete='SET NULL')
    addr = CharField(max_length=300, null=True)
    name = CharField(max_length=50)
    enable = BooleanField(default=True)
    auto_training = BooleanField(default=False)
    desc = CharField(max_length=300, null=True)
    inst_info = TextField(null=True)
    imx_db_id = IntegerField(null=True)
    inst_solution = CharField(max_length=50, null=True)
    inst_product_type = TextField(null=True)
    rac_info = TextField(null=True)
    inst_product_version = CharField(null=True)
    database_name = CharField(null=True)
    biz_name = CharField(null=True)
    load_fcst_enable = BooleanField(default=False)
    dbsln_enable = BooleanField(default=False)

    class Meta:
        table_name = 'xaiops_config_instance'
        indexes = (
            (('host_id',), False),  # Create an index on host_id
        )
        constraints = [
            SQL('CONSTRAINT xaiops_config_instance_unique UNIQUE (inst_type, target_id)'),
        ]


class XaiopsConfigInstanceGroup(BaseModel):
    inst_group_id = AutoField(primary_key=True)
    inst_group_name = CharField(max_length=255)
    auto_training = BooleanField(default=False)
    inst_group_order = IntegerField(default=1)

    class Meta:
        table_name = 'xaiops_config_instance_group'


class XaiopsConfigInstanceGroupMapInstance(BaseModel):
    config_inst_group_map_inst_id = AutoField(primary_key=True)
    inst_group_id = ForeignKeyField(XaiopsConfigInstanceGroup, backref='instance_group_maps', on_delete='CASCADE')
    inst_id = IntegerField()  # Assuming inst_id is an integer field from another table

    class Meta:
        table_name = 'xaiops_config_instance_group_map_instance'
        indexes = (
            (('inst_group_id', 'inst_id'), True),  # Unique constraint on (inst_group_id, inst_id)
            (('inst_group_id',), False),           # Index on inst_group_id
            (('inst_id',), False)                  # Index on inst_id
        )


class XaiopsConfigService(BaseModel):
    tx_seq = AutoField()
    auto_training = BooleanField(default=False)
    create_dt = TimestampField(null=True)
    enable = BooleanField(default=True)
    exec_count = BigIntegerField()
    tx_code = CharField(max_length=255, unique=True)
    tx_code_name = CharField(max_length=255)
    txn_id = CharField(max_length=255, null=True)
    txn_name = CharField(max_length=255, null=True)
    update_dt = TimestampField(null=True)
    load_fcst_enable = BooleanField(default=False)
    dbsln_enable = BooleanField(default=False)

    class Meta:
        table_name = 'xaiops_config_service'


class XaiopsConfigServiceGroup(BaseModel):
    service_group_id = AutoField(primary_key=True)
    biz_code = CharField(max_length=255, unique=True, null=False)
    biz_name = CharField(max_length=255, null=False)
    auto_training = BooleanField(default=False, null=False)

    class Meta:
        table_name = 'xaiops_config_service_group'


class XaiopsConfigServiceGroupMapService(BaseModel):
    service_group_id = ForeignKeyField(XaiopsConfigServiceGroup, backref='services', on_delete='CASCADE', null=False)
    tx_seq = BigIntegerField(null=False)
    config_service_group_map_service_id = BigAutoField(primary_key=True)

    class Meta:
        table_name = 'xaiops_config_service_group_map_service'
        indexes = (
            (('tx_seq', 'service_group_id'), True),
        )


class XaiopsConfigNetwork(BaseModel):
    network_id = AutoField(primary_key=True)
    target_id = CharField(max_length=255, unique=True, null=False)
    ip_addr = CharField(null=True)
    network_name = CharField(max_length=255, null=True)
    name = CharField(max_length=255, null=True)
    enable = BooleanField(null=True)
    desc = CharField(max_length=255, null=True)
    auto_training = BooleanField(default=False, null=False)
    load_fcst_enable = BooleanField(default=False, null=False)
    dbsln_enable = BooleanField(default=False, null=False)

    class Meta:
        table_name = 'xaiops_config_network'