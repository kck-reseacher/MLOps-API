import json
import traceback
import pandas as pd

import algorithms.logseq.config.default_regex as basereg
from api.ml_controller.ml_utils import RunUtils
from common.system_util import SystemUtil
from common.redisai import REDIS
from orm.models.config_serving_model import *
from orm.models.config_log_model import *
from orm.models.xaiops_config_model import *

_, py_config, _ = RunUtils.get_server_run_configuration()
db = SystemUtil.get_orm_db_conn(py_config)

xaiops_config_mapping = {
    "os": (XaiopsConfigHost, [XaiopsConfigHost.target_id, XaiopsConfigHost.name]),
    "hostGroup": (XaiopsConfigHost, [XaiopsConfigHost.target_id, XaiopsConfigHost.name]),
    "service": (XaiopsConfigService, [XaiopsConfigService.tx_code, XaiopsConfigService.tx_code_name]),
    "network": (XaiopsConfigNetwork, [XaiopsConfigNetwork.target_id, XaiopsConfigNetwork.name]),
    "instanceGroup": (XaiopsConfigInstance, [XaiopsConfigInstance.target_id, XaiopsConfigInstance.name,
                                             XaiopsConfigInstance.inst_product_type])
}


def select_config_inst_group() -> pd.DataFrame:
    """

    :return df: xaiops_config_instance_group 테이블 데이터
    """
    df = pd.DataFrame()
    db.connect(reuse_if_open=True)
    try:
        query = XaiopsConfigInstanceGroup.select()
        query_result = list(query.dicts())
        df = pd.DataFrame(query_result)
    except Exception:
        tb = traceback.format_exc()
        print(f"select_config_inst_group Exception: {tb}")

    return df


def select_config_host_group() -> pd.DataFrame:
    """
    :return df: xaiops_config_host_group 테이블 데이터
    """
    df = pd.DataFrame()
    db.connect(reuse_if_open=True)
    try:
        query = XaiopsConfigHostGroup.select()
        query_result = list(query.dicts())
        df = pd.DataFrame(query_result)
    except Exception:
        tb = traceback.format_exc()
        print(f"select_config_host_group Exception: {tb}")

    return df


def select_config_inst_group_map_inst() -> pd.DataFrame:
    """
    :return df: xaiops_config_instance_group_map_instance 테이블 데이터
    """
    df = pd.DataFrame()
    db.connect(reuse_if_open=True)
    try:
        query = XaiopsConfigInstanceGroupMapInstance.select()
        query_result = list(query.dicts())
        df = pd.DataFrame(query_result)
    except Exception:
        tb = traceback.format_exc()
        print(f"select_config_inst_group_map_inst Exception: {tb}")

    return df


def select_config_host_group_map_host() -> pd.DataFrame:
    """
    :return df: xaiops_config_host_group_map_host 테이블 데이터
    """
    df = pd.DataFrame()
    db.connect(reuse_if_open=True)
    try:
        query = XaiopsConfigHostGroupMapHost.select()
        query_result = list(query.dicts())
        df = pd.DataFrame(query_result)
    except Exception:
        tb = traceback.format_exc()
        print(f"select_config_host_group_map_host Exception: {tb}")

    return df


def select_config_service_group_map_service() -> pd.DataFrame:
    df = pd.DataFrame()
    db.connect(reuse_if_open=True)
    try:
        query = XaiopsConfigServiceGroupMapService.select()
        query_result = list(query.dicts())
        df = pd.DataFrame(query_result)
    except Exception:
        tb = traceback.format_exc()
        print(f"select_config_service_group_map_service Exception: {tb}")

    return df


def get_inst_group_target_list(group_id: int) -> pd.DataFrame:
    """
    xaiops_config_instance 테이블 데이터 조회
    :param group_id: ex) 177
    :return df: group_id에 맵핑된 인스턴스 타겟 데이터
    """
    df = pd.DataFrame()
    db.connect(reuse_if_open=True)
    try:
        subquery = (XaiopsConfigInstanceGroupMapInstance
                    .select(XaiopsConfigInstanceGroupMapInstance.inst_id)
                    .where(XaiopsConfigInstanceGroupMapInstance.inst_group_id == group_id)
                    )

        query = (XaiopsConfigInstance
                 .select(XaiopsConfigInstance.inst_type, XaiopsConfigInstance.target_id, XaiopsConfigInstance.inst_product_type)
                 .where((XaiopsConfigInstance.inst_id.in_(subquery))
                        & (XaiopsConfigInstance.enable == True))
                 )

        query_result = list(query.dicts())
        df = pd.DataFrame(query_result)
    except Exception:
        tb = traceback.format_exc()
        print(f"get_inst_group_target_list Exception: {tb}")

    return df


def get_host_group_target_list(group_id: int) -> pd.DataFrame:
    """
    xaiops_config_host 테이블 데이터 조회
    :param group_id: ex) 177
    :return df: group_id에 맵핑된 host 타겟 데이터
    """
    df = pd.DataFrame()
    db.connect(reuse_if_open=True)
    try:
        subquery = (XaiopsConfigHostGroupMapHost
                    .select(XaiopsConfigHostGroupMapHost.host_id)
                    .where(XaiopsConfigHostGroupMapHost.host_group_id == group_id)
                    )

        query = (XaiopsConfigHost
                 .select(XaiopsConfigHost.target_id)
                 .where((XaiopsConfigHost.host_id.in_(subquery))
                        & (XaiopsConfigHost.enable == True))
                 )

        query_result = list(query.dicts())
        df = pd.DataFrame(query_result)
    except Exception:
        tb = traceback.format_exc()
        print(f"get_host_group_target_list Exception: {tb}")

    return df


def get_service_group_target_list(group_id: int) -> pd.DataFrame:
    """
    xaiops_config_service 테이블 데이터 조회
    :param group_id: ex) 177
    :return df: group_id에 맵핑된 서비스 타겟 데이터
    """
    df = pd.DataFrame()
    db.connect(reuse_if_open=True)
    try:
        subquery = (XaiopsConfigServiceGroupMapService
                    .select(XaiopsConfigServiceGroupMapService.tx_seq)
                    .where(XaiopsConfigServiceGroupMapService.service_group_id == group_id)
                    )

        query = (XaiopsConfigService
                 .select(XaiopsConfigService.tx_code)
                 .where((XaiopsConfigService.tx_seq.in_(subquery))
                        & (XaiopsConfigService.enable == True))
                 )

        query_result = list(query.dicts())
        df = pd.DataFrame(query_result)
    except Exception:
        tb = traceback.format_exc()
        print(f"get_service_group_target_list Exception: {tb}")

    return df


def select_config_inst(inst_type: str) -> pd.DataFrame:
    """
    xaiops_config_instance 테이블 데이터 조회
    :param inst_type: ex) 'was'
    :return df: xaiops_config_instance 테이블 데이터
    """
    df = pd.DataFrame()
    db.connect(reuse_if_open=True)
    try:
        query = (XaiopsConfigInstance
                 .select(XaiopsConfigInstance.inst_id, XaiopsConfigInstance.target_id)
                 .where((XaiopsConfigInstance.inst_type == inst_type)
                        & (XaiopsConfigInstance.enable == True))
                 )

        query_result = list(query.dicts())
        df = pd.DataFrame(query_result)
    except Exception:
        tb = traceback.format_exc()
        print(f"select_config_inst Exception: {tb}")

    return df


def select_config_inst_for_product_type(inst_type: str, product_type: str) -> pd.DataFrame:
    """
    xaiops_config_instance 테이블 데이터 조회
    :param inst_type: ex) 'db'
    :param product_type: ex) 'ORACLE'
    :return df: xaiops_config_instance 테이블 데이터
    """
    df = pd.DataFrame()
    db.connect(reuse_if_open=True)
    try:
        query = (XaiopsConfigInstance
                 .select(XaiopsConfigInstance.inst_id, XaiopsConfigInstance.target_id)
                 .where((XaiopsConfigInstance.inst_type == inst_type)
                        & (XaiopsConfigInstance.inst_product_type == product_type)
                        & (XaiopsConfigInstance.enable == True))
                 )

        query_result = list(query.dicts())
        df = pd.DataFrame(query_result)
    except Exception:
        tb = traceback.format_exc()
        print(f"select_config_inst_for_product_type Exception: {tb}")

    return df


def select_config_host() -> pd.DataFrame:
    """
    xaiops_config_host 테이블 데이터 조회
    :return df: xaiops_config_host 테이블 데이터
    """
    df = pd.DataFrame()
    db.connect(reuse_if_open=True)
    try:
        query = (XaiopsConfigHost
                 .select(XaiopsConfigHost.host_id, XaiopsConfigHost.target_id)
                 .where(XaiopsConfigHost.enable == True)
                 )

        query_result = list(query.dicts())
        df = pd.DataFrame(query_result)
    except Exception:
        tb = traceback.format_exc()
        print(f"select_config_host Exception: {tb}")

    return df


def select_config_service() -> pd.DataFrame:
    df = pd.DataFrame()
    db.connect(reuse_if_open=True)
    try:
        query = (XaiopsConfigService
                .select(XaiopsConfigService.tx_seq, XaiopsConfigService.tx_code)
                .where(XaiopsConfigService.enable == True)
                )

        query_result = list(query.dicts())
        df = pd.DataFrame(query_result)
    except Exception:
        tb = traceback.format_exc()
        print(f"select_config_service Exception: {tb}")

    return df


def select_config_network() -> pd.DataFrame:
    """
    xaiops_config_network 테이블 데이터 조회
    :return df: xaiops_config_network 테이블 데이터
    """
    df = pd.DataFrame()
    db.connect(reuse_if_open=True)
    try:
        query = (XaiopsConfigNetwork
                 .select(XaiopsConfigNetwork.network_id, XaiopsConfigNetwork.target_id)
                 .where(XaiopsConfigNetwork.enable == True)
                 )

        query_result = list(query.dicts())
        df = pd.DataFrame(query_result)
    except Exception:
        tb = traceback.format_exc()
        print(f"select_config_network Exception: {tb}")

    return df


def append_group_target_list(group_target_list: list,
                             target_id: str,
                             config_instance_dict: dict,
                             config_serving_dict: dict,
                             inst_type: str,
                             redis_serving_targets: dict,
                             none_fields=False):
    """
    group_target_list 에 타겟 정보를 추가하는 함수

    :param group_target_list: 그룹에 맵핑된 타겟 정보
    :param target_id: ex) '1201'
    :param config_instance_dict: xaiops_config_instance 테이블 데이터
    :param config_serving_dict: ai_config_serving 테이블 데이터
    :param inst_type: ex) 'was'
    :param redis_serving_targets: redis-server에 저장된 서빙 대상
    :param none_fields: none_fields = True의 경우 필드를 None으로 리턴
    :return:
    """
    if target_id in config_instance_dict.keys():
        group_target_list.append({
            'servingName': None if none_fields else config_serving_dict[target_id].get('serving_name'),
            'targetId': target_id,
            'targetName': config_instance_dict[target_id]['name'],
            'instType': inst_type,
            'instProductType': config_instance_dict[target_id]['inst_product_type'],
            'serviceOnBoot': None if none_fields else config_serving_dict[target_id].get('service_on_boot'),
            'confirmProcess': None if none_fields else (config_serving_dict[target_id].get(
                'serving_name') in redis_serving_targets.keys() if redis_serving_targets is not None else False)
        })


def process_exem_aiops_load_fcst(group_target_list: list,
                                 config_serving_dict: dict,
                                 config_instance_dict: dict,
                                 inst_type: str,
                                 product_type: str,
                                 redis_serving_targets: dict):
    """
    부하예측(system) 기능의 그룹에 맵핑된 타겟 정보를 group_target_list에 추가

    :param group_target_list: 그룹에 맵핑된 타겟 정보
    :param config_serving_dict: ai_config_serving 테이블 데이터
    :param config_instance_dict: xaiops_config_instance 테이블 데이터
    :param inst_type: ex) 'was'
    :param product_type: ex) 'ORACLE'
    :param redis_serving_targets: redis-server에 저장된 서빙 대상
    :return:
    """
    target_key = product_type if inst_type == 'db' else 'all'
    if target_key in config_serving_dict.keys():
        target_list = json.loads(config_serving_dict[target_key]['target_list'])
        for target_id in target_list:
            append_group_target_list(group_target_list, target_id, config_instance_dict, config_serving_dict, inst_type,
                                     redis_serving_targets, none_fields=True)


def process_exem_aiops_event_fcst(group_target_list: list,
                                  config_serving_dict: dict,
                                  config_instance_dict: dict,
                                  group_id: int,
                                  redis_serving_targets: dict):
    """
    이슈 예측 기능의 그룹에 맵핑된 타겟 정보를 group_target_list에 추가

    :param group_target_list: 그룹에 맵핑된 타겟 정보
    :param config_serving_dict: ai_config_serving 테이블 데이터
    :param config_instance_dict: xaiops_config_instance 테이블 데이터
    :param group_id: ex) 177
    :param redis_serving_targets: redis-server에 저장된 서빙 대상
    :return:
    """
    target_dict = json.loads(config_serving_dict[str(group_id)]['target_list'])
    for inst_type, target_ids in target_dict.items():
        for target_id in target_ids:
            append_group_target_list(group_target_list, target_id, config_instance_dict, config_serving_dict, inst_type,
                                     redis_serving_targets, none_fields=True)


## 미분류 그룹 처리
def process_group_id_minus_1(group_target_list: list,
                             inst_type: str,
                             product_type: str,
                             config_instance_dict: dict,
                             config_serving_dict: dict,
                             redis_serving_targets: dict):
    """
    미분류 그룹(group_id = -1)에 대한 처리, 미분류된 타겟 정보를 group_target_list에 추가

    :param group_target_list: 그룹에 맵핑된 타겟 정보
    :param inst_type: ex) 'was'
    :param config_instance_dict: xaiops_config_instance 테이블 데이터
    :param config_serving_dict: ai_config_serving 테이블 데이터
    :param redis_serving_targets: redis-server에 저장된 서빙 대상
    :return:
    """
    db.connect(reuse_if_open=True)
    try:
        group_map_values = []
        if inst_type == "os":
            id_df = select_config_host()
            host_group_map_df = select_config_host_group_map_host()
            group_map_values = host_group_map_df['host_id'].values
        elif inst_type == "service":
            id_df = select_config_service()
            service_group_map_df = select_config_service_group_map_service()
            group_map_values = service_group_map_df['tx_seq'].values
        elif inst_type == "network":
            id_df = select_config_network()
        else:
            if inst_type == 'db':
                id_df = select_config_inst_for_product_type(inst_type, product_type)
            else:
                id_df = select_config_inst(inst_type)
            inst_group_map_df = select_config_inst_group_map_inst()
            group_map_values = inst_group_map_df['inst_id'].values

        for index, row in id_df.iterrows():
            target_id = row.get('target_id')
            if inst_type == 'network':
                id_value = row.get('network_id')
            elif inst_type == 'os':
                id_value = row.get('host_id')
            elif inst_type == 'service':
                id_value = row.get('tx_seq')
                target_id = row.get('tx_code')
            else:
                id_value = row.get('inst_id')
            if id_value not in group_map_values and target_id in config_serving_dict.keys():
                append_group_target_list(group_target_list, target_id, config_instance_dict, config_serving_dict, inst_type,
                                         redis_serving_targets)
    except Exception:
        tb = traceback.format_exc()
        print(f"process_group_id_minus_1 Exception: {tb}")


def process_default(group_target_list: list,
                    group_id: int,
                    inst_type: str,
                    config_instance_dict: dict,
                    config_serving_dict: dict,
                    product_type: str,
                    redis_serving_targets: dict):
    """
    그룹에 맵핑된 타겟 목록을 group_target_list에 추가

    :param group_target_list: 그룹에 맵핑된 타겟 정보
    :param group_id: ex) 177
    :param inst_type: ex) 'was'
    :param config_instance_dict: xaiops_config_instance 테이블 데이터
    :param config_serving_dict: ai_config_serving 테이블 데이터
    :param product_type: ex) 'ORACLE'
    :param redis_serving_targets: redis-server에 저장된 서빙 대상
    :return:
    """
    db.connect(reuse_if_open=True)
    try:
        if inst_type == 'os':
            target_list = get_host_group_target_list(group_id)['target_id'].values
        elif inst_type == 'service':
            target_list = get_service_group_target_list(group_id)['tx_code'].values
        else:
            inst_group_target_df = get_inst_group_target_list(group_id)
            if inst_type == 'db':
                target_list = inst_group_target_df.loc[(inst_group_target_df['inst_type'] == inst_type) & (
                            inst_group_target_df['inst_product_type'] == product_type)]['target_id'].values
            else:
                target_list = inst_group_target_df.loc[inst_group_target_df['inst_type'] == inst_type]['target_id'].values

        for target_id in target_list:
            if target_id in config_serving_dict.keys():
                append_group_target_list(group_target_list, target_id, config_instance_dict, config_serving_dict, inst_type,
                                         redis_serving_targets)
    except Exception:
        tb = traceback.format_exc()
        print(f"process_default Exception: {tb}")

def select_ai_config_serving(ai_service: str, type: str) -> dict:
    """
    ai_config_serving 테이블에서 데이터를 조회하여 리턴

    :param ai_service: ex) 'exem_aiops_anls_inst'
    :param type: ex) 'was'
    :return config_serving_dict: ai_config_serving 테이블 데이터
    """
    config_serving_dict = {}
    db.connect(reuse_if_open=True)
    try:
        config_serving_query = AiConfigServing.select().where((AiConfigServing.module == ai_service)
                                                    & (AiConfigServing.inst_type == type))
        for config in config_serving_query:
            config_serving_dict[config.target_id] = {
                'serving_name': config.serving_name,
                'inst_type': config.inst_type,
                'module': config.module,
                'service_on_boot': config.service_on_boot,
                'target_list': config.target_list
            }
    except Exception:
        tb = traceback.format_exc()
        print(f"select_ai_config_serving Exception: {tb}")

    return config_serving_dict


def select_group_target_list(ai_service: str, inst_type: str, product_type: str, group_id: int) -> list:
    """
    ai_service 기능 및 타입, 그룹 id 별로 맵핑된 타겟 목록을 리턴한다.

    :param ai_service: ex) 'exem_aiops_anls_inst'
    :param inst_type: ex) 'was'
    :param product_type: ex) 'ORACLE'
    :param group_id: ex) 177
    :return group_target_list: 특정 그룹에 맵핑된 타겟 목록
    """
    group_target_list = []
    db.connect(reuse_if_open=True)
    try:
        if ai_service != 'exem_aiops_load_fcst' and group_id == None:
            return []

        config_serving_dict = select_ai_config_serving(ai_service, inst_type)

        if inst_type in ['was', 'db', 'web', 'tp']:
            config_class = XaiopsConfigInstance
            fields = [XaiopsConfigInstance.target_id, XaiopsConfigInstance.name, XaiopsConfigInstance.inst_product_type]
            config_query = (config_class
                            .select(*fields)
                            .where((config_class.inst_type == inst_type) & (config_class.enable == True)))
        else:
            config_class, fields = xaiops_config_mapping[inst_type]
            config_query = config_class.select(*fields).where(config_class.enable == True)

        config_instance_dict = {}
        for config in config_query:
            target_id = config.target_id if hasattr(config, 'target_id') else config.tx_code
            name = config.name if hasattr(config, 'name') else config.tx_code_name
            inst_product_type = config.inst_product_type if hasattr(config, 'inst_product_type') else None
            config_instance_dict[target_id] = {
                'name': name,
                'inst_product_type': inst_product_type
            }

        redis_serving_targets = REDIS.hgetall('RedisServingTargets::mlc')
        if ai_service == 'exem_aiops_load_fcst':
            process_exem_aiops_load_fcst(group_target_list, config_serving_dict, config_instance_dict, inst_type,
                                         product_type, redis_serving_targets)
        elif ai_service == 'exem_aiops_event_fcst':
            process_exem_aiops_event_fcst(group_target_list, config_serving_dict, config_instance_dict, group_id,
                                          redis_serving_targets)
        elif group_id == -1:
            process_group_id_minus_1(group_target_list, inst_type, product_type, config_instance_dict, config_serving_dict,
                                     redis_serving_targets)
        else:
            process_default(group_target_list, group_id, inst_type, config_instance_dict, config_serving_dict,
                            product_type, redis_serving_targets)

    except Exception:
        tb = traceback.format_exc()
        print(f"select_group_target_list Exception: {tb}")

    return group_target_list


def select_xaiops_config_log() -> dict:
    """
    xaiops_config_log 테이블을 조회하여 meta 데이터 생성
    :return config_log_dict: 로그 관련 meta 데이터
    """
    config_log_dict = {}
    db.connect(reuse_if_open=True)
    try:
        config_log_query = XaiopsConfigLog.select()
        for config in config_log_query:
            config_log_dict[config.target_id] = {
                'log_id': config.log_id,
                'target_id': config.target_id,
                'target_name': config.log_name,
                'category': config.log_category,
                'is_service_on': config.is_service_on,
                'regset_id': config.regset_id,
                'hostname': config.host_name
            }
    except Exception:
        tb = traceback.format_exc()
        print(f"select_xaiops_config_log Exception: {tb}")

    return config_log_dict


def select_regex_preset() -> dict:
    """
    ai_config_log_regex_preset 테이블을 조회하여 meta 데이터 생성
    :return preset_dict: 프리셋 관련 데이터
    """
    preset_dict = {}
    db.connect(reuse_if_open=True)
    try:
        preset_result = AiConfigLogRegexPreset.select()
        for preset in preset_result:
            preset_dict[preset.regset_id] = {
                'set_name': preset.set_name
            }
    except Exception:
        tb = traceback.format_exc()
        print(f"select_regex_preset Exception: {tb}")

    return preset_dict


def select_log_sparse() -> dict:
    """
    ai_config_serving_log_sparse 테이블을 조회하여 meta 데이터 생성

    :return config_sparse_dict: 희소로그 meta 데이터
    """
    config_sparse_dict = {}
    db.connect(reuse_if_open=True)
    try:
        config_sparse_query = AiConfigSparse.select()
        for config in config_sparse_query:
            config_sparse_dict[config.log_id] = {
                'alert_threshold': config.alert_threshold,
                'rare_rate': config.rare_rate,
                'is_sparse_service_on': config.is_service_on
            }
    except Exception:
        tb = traceback.format_exc()
        print(f"select_log_sparse Exception: {tb}")

    return config_sparse_dict


def select_log_keyword() -> dict:
    """
    ai_config_serving_log_keyword 테이블을 조회하여 meta 데이터 생성

    :return config_log_keyword_dict: 사용자 키워드, 제외 키워드 관련 데이터
    """
    config_log_keyword_dict = {}
    db.connect(reuse_if_open=True)
    try:
        unique_log_ids = (AiConfigLogKeyword
                          .select(AiConfigLogKeyword.log_id)
                          .distinct())
        for entry in unique_log_ids:
            log_id_keyword_query = AiConfigLogKeyword.select().where(AiConfigLogKeyword.log_id == entry.log_id)
            query_result = list(log_id_keyword_query.dicts())
            keyword_df = pd.DataFrame(query_result)
            config_log_keyword_dict[entry.log_id] = {
                'exclude_keyword': list(keyword_df.loc[keyword_df['keyword_type'] == 'exclude']['keyword'].values),
                'include_keyword': list(keyword_df.loc[keyword_df['keyword_type'] == 'include']['keyword'].values)
            }
    except Exception:
        tb = traceback.format_exc()
        print(f"select_log_keyword Exception: {tb}")

    return config_log_keyword_dict


def select_log_digcn() -> dict:
    """
    ai_config_serving_log_digcn 테이블을 조회하여 meta 데이터 생성

    :return config_digcn_dict: ai_config_serving_log_digcn 테이블 데이터
    """
    db.connect(reuse_if_open=True)
    config_digcn_dict = {}
    try:
        config_digcn_query = AiConfigServingLogDigcn.select()
        for config in config_digcn_query:
            config_digcn_dict[config.target_id] = {
                'metric_id': config.metric_id,
                'anomaly_threshold': json.loads(config.params)['anomaly_threshold'],
                'auto_anomaly_threshold': json.loads(config.recommend_param)['anomaly_threshold'],
                'is_params_auto': config.is_params_auto,
            }
    except Exception:
        tb = traceback.format_exc()
        print(f"select_log_digcn Exception: {tb}")

    return config_digcn_dict


def select_log_service_list(ai_service: str, log_type: str) -> list:
    """
    학습/서비스 > 서빙 > 로그이상탐지 화면의 정보 데이터를 리턴

    :param ai_service: ex) 'exem_aiops_anls_inst'
    :param log_type: ex) 'syslog'
    :return log_data_list: 학습/서비스 > 서빙 > 로그이상탐지 화면에 필요한 리턴 포맷 데이터
    """
    db.connect(reuse_if_open=True)
    log_data_list = []

    try:
        config_serving_dict = select_ai_config_serving(ai_service, log_type)
        config_log_dict = select_xaiops_config_log()
        preset_dict = select_regex_preset()
        config_sparse_dict = select_log_sparse()
        config_log_keyword_dict = select_log_keyword()
        config_digcn_dict = select_log_digcn()

        redis_serving_targets = REDIS.hgetall('RedisServingTargets::mlc')

        for target_id in config_serving_dict.keys():
            log_id = config_log_dict[target_id]['log_id']
            regset_id = config_log_dict[target_id]['regset_id'] if config_log_dict[target_id][
                                                                       'regset_id'] is not None else None
            log_data_list.append(
                {
                    'servingName': config_serving_dict[target_id]['serving_name'],
                    'targetId': target_id,
                    'targetName': config_log_dict[target_id]['target_name'],
                    'instType': config_serving_dict[target_id]['inst_type'],
                    'module': config_serving_dict[target_id]['module'],
                    'serviceOnBoot': config_serving_dict[target_id]['service_on_boot'],
                    'confirmProcess': config_serving_dict[target_id]['serving_name'] in redis_serving_targets.keys() if redis_serving_targets is not None else False,
                    'logCategory': config_log_dict[target_id]['category'],
                    'alertThreshold': config_sparse_dict[log_id]['alert_threshold'],
                    'rareRate': config_sparse_dict[log_id]['rare_rate'],
                    'userKeywords': config_log_keyword_dict[log_id][
                        'include_keyword'] if log_id in config_log_keyword_dict.keys() else [],
                    'excludeKeywords': config_log_keyword_dict[log_id][
                        'exclude_keyword'] if log_id in config_log_keyword_dict.keys() else [],
                    'metricId': config_digcn_dict[target_id]['metric_id'],
                    'anomalyThreshold': config_digcn_dict[target_id]['anomaly_threshold'],
                    'autoAnomalyThreshold': config_digcn_dict[target_id]['auto_anomaly_threshold'],
                    'setName': preset_dict[regset_id]['set_name'] if regset_id in preset_dict.keys() else None,
                    'regsetId': int(regset_id) if regset_id is not None else None,
                    'hostName': config_log_dict[target_id]['hostname'],
                    'isLogServiceOn': config_log_dict[target_id]['is_service_on'],
                    'isSparseServiceOn': config_sparse_dict[log_id]['is_sparse_service_on'],
                    'isParamAuto': config_digcn_dict[target_id]['is_params_auto']
                }
            )
    except Exception:
        tb = traceback.format_exc()
        print(f"select_log_service_list Exception : {tb}")

    return log_data_list


def process_unclassified_group(inst_type: str,
                               total_target_list: list,
                               config_serving_df: pd.DataFrame,
                               redis_serving_targets: dict,
                               group_dict: dict,
                               product_type=None):
    """
    그룹 조회 시 미분류 그룹(group_id = -1)을 처리하기 위한 함수

    :param inst_type: ex) 'was'
    :param total_target_list: 모든 그룹에 맵핑된 타겟 리스트 ex) ['1201', '1202']
    :param config_serving_df: ai_config_serving 테이블을 조회한 데이터프레임
    :param redis_serving_targets: redis-server에 저장된 서빙 대상
    :param group_dict: group 조회 리턴 데이터
    :param product_type: instance product type ex) 'ORACLE'
    :return group_dict: group 조회 리턴 데이터
    """
    db.connect(reuse_if_open=True)
    try:
        if inst_type == 'os':
            query = XaiopsConfigHost.select().where(XaiopsConfigHost.enable == True)
        elif inst_type == 'service':
            query = XaiopsConfigService.select().where(XaiopsConfigService.enable == True)
        else:
            if inst_type == 'db':
                query = XaiopsConfigInstance.select()\
                        .where((XaiopsConfigInstance.inst_type == inst_type)
                               & (XaiopsConfigInstance.inst_product_type == product_type)
                               & (XaiopsConfigInstance.enable == True))
            else:
                query = XaiopsConfigInstance.select()\
                        .where((XaiopsConfigInstance.inst_type == inst_type)
                               & (XaiopsConfigInstance.enable == True))

        query_result = list(query.dicts())
        config_df = pd.DataFrame(query_result)
        target_id_prefix = 'tx_code' if inst_type == 'service' else 'target_id'
        unclassified_group_targets = list(set(config_df[target_id_prefix].values) - set(total_target_list))
        if len(unclassified_group_targets) > 0:
            group_df = config_serving_df[config_serving_df['target_id'].isin(unclassified_group_targets)]
            if not group_df.empty:
                group_dict[-1] = {
                    'name': '미분류',
                    'group_id': -1,
                    'service_on_boot': False if False in group_df['service_on_boot'].values else True,
                    'confirm_process': all(item in redis_serving_targets.keys() for item in group_df['serving_name'].values) if redis_serving_targets is not None else False,
                    'serving_name': None
                }
    except Exception:
        tb = traceback.format_exc()
        print(f"process_unclassified_group Exception: {tb}")

    return group_dict


def select_config_instance_group_dict(config_serving_df: pd.DataFrame, redis_serving_targets: dict, inst_type: str, product_type: str) -> dict:
    """
    AI서비스의 'was', 'db', 'web', 'tp' 타입에 맵핑된 그룹 정보를 조회

    :param config_serving_df: ai_config_serving 테이블을 조회한 데이터프레임
    :param redis_serving_targets: redis-server에 저장된 서빙 대상
    :param inst_type: ex) 'was'
    :param product_type: ex) 'ORACLE'
    :return instance_group_dict: 인스턴스 타입에 맵핑된 그룹 정보
    """
    db.connect(reuse_if_open=True)
    total_target_list = []
    instance_group_dict = {}
    try:
        instance_group_query = XaiopsConfigInstanceGroup.select()
        for config in instance_group_query:
            inst_group_target_df = get_inst_group_target_list(config.inst_group_id)
            if not inst_group_target_df.empty:
                if inst_type == 'db':
                    target_list = inst_group_target_df.loc[(inst_group_target_df['inst_type'] == inst_type) & (
                    (inst_group_target_df['inst_product_type'] == product_type))]['target_id'].values
                else:
                    target_list = inst_group_target_df.loc[inst_group_target_df['inst_type'] == inst_type]['target_id'].values
                total_target_list.extend(target_list)
                group_df = config_serving_df[config_serving_df['target_id'].isin(target_list)]
                for target_id in target_list:
                    if target_id in config_serving_df['target_id'].values:
                        if config.inst_group_id not in instance_group_dict.keys():
                            instance_group_dict[config.inst_group_id] = {
                                'name': config.inst_group_name,
                                'group_id': config.inst_group_id,
                                'service_on_boot': False if False in group_df['service_on_boot'].values else True,
                                'confirm_process': all(
                                    item in redis_serving_targets.keys() for item in group_df['serving_name'].values) if redis_serving_targets is not None else False,
                                'serving_name': None
                            }
        # 미분류 타겟
        instance_group_dict = process_unclassified_group(inst_type,
                                                         total_target_list,
                                                         config_serving_df,
                                                         redis_serving_targets,
                                                         instance_group_dict,
                                                         product_type)
    except Exception:
        tb = traceback.format_exc()
        print(f"select_config_instance_group_dict Exception: {tb}")

    return instance_group_dict


def select_config_host_group_dict(config_serving_df: pd.DataFrame, redis_serving_targets: dict) -> dict:
    """
    AI서비스의 os타입에 맵핑된 그룹 정보를 조회

    :param config_serving_df: ai_config_serving 테이블을 조회한 데이터프레임
    :param redis_serving_targets: redis-server에 저장된 서빙 대상
    :return host_group_dict: os타입에 맵핑된 그룹 정보
    """
    db.connect(reuse_if_open=True)
    total_target_list = []
    host_group_dict = {}
    try:
        host_group_query = XaiopsConfigHostGroup.select()
        for config in host_group_query:
            host_group_target_df = get_host_group_target_list(config.host_group_id)
            if not host_group_target_df.empty:
                target_list = host_group_target_df['target_id'].values
                total_target_list.extend(target_list)
                group_df = config_serving_df[config_serving_df['target_id'].isin(target_list)]
                for target_id in target_list:
                    if target_id in config_serving_df['target_id'].values:
                        if config.host_group_id not in host_group_dict.keys():
                            host_group_dict[config.host_group_id] = {
                                'name': config.host_group_name,
                                'group_id': config.host_group_id,
                                'service_on_boot': False if False in group_df['service_on_boot'].values else True,
                                'confirm_process': all(
                                    item in redis_serving_targets.keys() for item in group_df['serving_name'].values) if redis_serving_targets is not None else False,
                                'serving_name': None
                            }
        # 미분류 타겟
        host_group_dict = process_unclassified_group('os',
                                                     total_target_list,
                                                     config_serving_df,
                                                     redis_serving_targets,
                                                     host_group_dict)
    except Exception:
        tb = traceback.format_exc()
        print(f"select_config_host_group_dict Exception: {tb}")

    return host_group_dict


def select_config_service_group_dict(config_serving_df: pd.DataFrame, redis_serving_targets: dict) -> dict:
    """
    AI서비스의 service타입에 맵핑된 그룹 정보를 조회

    :param config_serving_df: ai_config_serving 테이블을 조회한 데이터프레임
    :param redis_serving_targets: redis-server에 저장된 서빙 대상
    :return service_group_dict: service타입에 맵핑된 그룹 정보
    """
    db.connect(reuse_if_open=True)
    total_target_list = []
    service_group_dict = {}
    try:
        service_group_query = XaiopsConfigServiceGroup.select()
        for config in service_group_query:
            service_group_target_df = get_service_group_target_list(config.service_group_id)
            if not service_group_target_df.empty:
                target_list = service_group_target_df['tx_code'].values
                total_target_list.extend(target_list)
                group_df = config_serving_df[config_serving_df['target_id'].isin(target_list)]
                for target_id in target_list:
                    if target_id in config_serving_df['target_id'].values:
                        if config.service_group_id not in service_group_dict.keys():
                            service_group_dict[config.service_group_id] = {
                                'name': config.biz_name,
                                'group_id': config.service_group_id,
                                'service_on_boot': False if False in group_df['service_on_boot'].values else True,
                                'confirm_process': all(
                                    item in redis_serving_targets.keys() for item in group_df['serving_name'].values) if redis_serving_targets is not None else False,
                                'serving_name': None
                            }
        # 미분류 타겟
        service_group_dict = process_unclassified_group('service',
                                                        total_target_list,
                                                        config_serving_df,
                                                        redis_serving_targets,
                                                        service_group_dict)
    except Exception:
        tb = traceback.format_exc()
        print(f"select_config_service_group_dict Exception: {tb}")

    return service_group_dict


def select_network_group_dict(config_serving_df, redis_serving_targets):
    """
    AI서비스의 network타입에 맵핑된 그룹 정보를 조회

    :param config_serving_df: ai_config_serving 테이블을 조회한 데이터프레임
    :param redis_serving_targets: redis-server에 저장된 서빙 대상
    :return network_group_dict: network타입에 맵핑된 그룹 정보
    """
    db.connect(reuse_if_open=True)
    network_group_dict = {}
    try:
        network_query = XaiopsConfigNetwork.select().where(XaiopsConfigNetwork.enable == True)
        query_result = list(network_query.dicts())
        network_df = pd.DataFrame(query_result)
        if not network_df.empty:
            target_list = network_df['target_id'].values
            group_df = config_serving_df[config_serving_df['target_id'].isin(target_list)]
            network_group_dict[-1] = {
                'name': '미분류',
                'group_id': -1,
                'service_on_boot': False if False in group_df['service_on_boot'].values else True,
                'confirm_process': all(item in redis_serving_targets.keys() for item in group_df['serving_name'].values) if redis_serving_targets is not None else False,
                'serving_name': None
            }
    except Exception:
        tb = traceback.format_exc()
        print(f"select_network_group_dict Exception: {tb}")

    return network_group_dict


def process_group_exem_aiops_load_fcst(config_serving_df: pd.DataFrame, redis_serving_targets: dict) -> dict:
    """
    부하예측(system) 기능의 그룹 목록 데이터를 조회

    :param config_serving_df: ai_config_serving 테이블을 조회한 데이터프레임
    :param redis_serving_targets: redis-server에 저장된 서빙 대상
    :return result_group_dict: 부하예측(system) 기능의 그룹 정보 데이터
    """
    result_group_dict = {}
    result_group_dict[config_serving_df['target_id'].values[0]] = {
        'name': config_serving_df['target_id'].values[0],
        'group_id': None,
        'service_on_boot': config_serving_df['service_on_boot'].values[0].item(),
        'confirm_process': config_serving_df['serving_name'].values[0] in redis_serving_targets.keys() if redis_serving_targets is not None else False,
        'serving_name': config_serving_df['serving_name'].values[0]
    }
    return result_group_dict


def process_group_exem_aiops_event_fcst(config_serving_df: pd.DataFrame, redis_serving_targets: dict, inst_type: str) -> dict:
    """
    이슈예측 기능의 그룹 목록 데이터를 조회

    :param config_serving_df: ai_config_serving 테이블을 조회한 데이터프레임
    :param redis_serving_targets: redis-server에 저장된 서빙 대상
    :param inst_type: ex) 'was'
    :return result_group_dict: 이슈 예측 기능의 그룹 정보 데이터
    """
    result_group_dict = {}
    try:
        if inst_type == 'instanceGroup':
            event_group_df = select_config_inst_group()
            group_id_name = 'inst_group_id'
            group_name = 'inst_group_name'
        elif inst_type == 'hostGroup':
            event_group_df = select_config_host_group()
            group_id_name = 'host_group_id'
            group_name = 'host_group_name'

        for target_id in config_serving_df['target_id'].values:
            group_df = config_serving_df.loc[config_serving_df['target_id'] == target_id]
            result_group_dict[target_id] = {
                'name': event_group_df.loc[event_group_df[group_id_name] == int(target_id)][group_name].values[0],
                'group_id': int(target_id),
                'service_on_boot': group_df['service_on_boot'].values[0].item(),
                'confirm_process': group_df['serving_name'].values[0] in redis_serving_targets.keys() if redis_serving_targets is not None else False,
                'serving_name': group_df['serving_name'].values[0]
            }
    except Exception:
        tb = traceback.format_exc()
        print(f"process_group_exem_aiops_event_fcst Exception: {tb}")

    return result_group_dict


def process_group_default(config_serving_df: pd.DataFrame, redis_serving_targets: dict, inst_type: str, product_type: str) -> dict:
    """
    이상탐지 or 부하예측 AI 서비스의 그룹 목록을 조회

    :param config_serving_df: ai_config_serving 테이블을 조회한 데이터프레임
    :param redis_serving_targets: redis-server에 저장된 서빙 대상
    :param inst_type: ex) 'was'
    :param product_type: ex) 'ORACLE'
    :return group_dict: AI서비스 & 타입에 맵핑된 그룹 리스트
    """
    if inst_type in ['was', 'db', 'web', 'tp']:
        group_dict = select_config_instance_group_dict(config_serving_df, redis_serving_targets, inst_type,
                                                       product_type)
    elif inst_type == 'os':
        group_dict = select_config_host_group_dict(config_serving_df, redis_serving_targets)
    elif inst_type == 'service':
        group_dict = select_config_service_group_dict(config_serving_df, redis_serving_targets)
    elif inst_type == 'network':
        group_dict = select_network_group_dict(config_serving_df, redis_serving_targets)

    return group_dict


def select_group_list(ai_service: str, inst_type: str, product_type: str) -> list:
    """
    설정 > 학습/서비스 > 서빙화면에서 그룹 목록을 리턴

    :param ai_service: ex) 'exem_aiops_anls_inst'
    :param inst_type: ex) 'was'
    :param product_type: ex) 'ORACLE'
    :return group_list: AI서비스 & 타입에 맵핑된 그룹 리스트
    """
    db.connect(reuse_if_open=True)
    group_list = []
    try:
        config_serving_query = AiConfigServing.select().where((AiConfigServing.module == ai_service)
                                                              & (AiConfigServing.inst_type == inst_type))
        query_result = list(config_serving_query.dicts())
        config_serving_df = pd.DataFrame(query_result)
        redis_serving_targets = REDIS.hgetall('RedisServingTargets::mlc')

        if not config_serving_df.empty:
            if ai_service == 'exem_aiops_load_fcst':
                if inst_type == 'db':
                    config_serving_df = config_serving_df.loc[config_serving_df['target_id'] == product_type]
                group_dict = process_group_exem_aiops_load_fcst(config_serving_df, redis_serving_targets)
            elif ai_service == 'exem_aiops_event_fcst':
                group_dict = process_group_exem_aiops_event_fcst(config_serving_df, redis_serving_targets, inst_type)
            else:
                group_dict = process_group_default(config_serving_df, redis_serving_targets, inst_type, product_type)

            for group_id in group_dict.keys():
                group_list.append({
                    'groupName': group_dict[group_id]['name'],
                    'groupId': group_dict[group_id]['group_id'],
                    'confirmProcess': group_dict[group_id]['confirm_process'],
                    'serviceOnBoot': group_dict[group_id]['service_on_boot'],
                    'servingName': group_dict[group_id]['serving_name']
                })
    except Exception:
        tb = traceback.format_exc()
        print(f"select_group_list Exception: {tb}")

    return group_list


def select_ai_config_serving_onboot() -> dict:
    """
    ai_config_serving 테이블의 데이터를 조회
    :return:
    """
    db.connect(reuse_if_open=True)
    serving_targets = {}
    try:
        query = AiConfigServing.select().where(AiConfigServing.service_on_boot == True)
        for config in query:
            serving_name = f"{config.module}_{config.inst_type}_{config.target_id}"
            serving_targets[serving_name] = {
                'service_name': config.serving_name,
                'module': config.module,
                'target_id': config.target_id,
                'type': config.inst_type
            }
    except Exception:
        tb = traceback.format_exc()
        print(f"select_ai_config_serving_onboot Exception: {tb}")

    return serving_targets


def select_ai_config_serving_for_module(module: str) -> dict:
    """
    ai_config_serving 테이블의 부하예측(RMC) or 이슈예측 데이터를 조회

    :param module: XAIOps 기능 명 ex) 'exem_aiops_load_fcst', 'exem_aiops_event_fcst'
    :return: 서빙 대상 정보
    ex) {'exem_aiops_event_fcst_instanceGroup_179': {
                "module":"exem_aiops_event_fcst",
                "target_id":"179",
                "inst_type":"instanceGroup",
                "target_list": {"was": ["1201", "1202", ...,] }
                },
                ...
            }
    """
    db.connect(reuse_if_open=True)
    serving_targets = {}
    try:
        query = AiConfigServing.select().where((AiConfigServing.service_on_boot == True) & (AiConfigServing.module == module))
        for config in query:
            serving_name = f"{config.module}_{config.inst_type}_{config.target_id}"
            serving_targets[serving_name] = {
                'module': config.module,
                'target_id': config.target_id,
                'inst_type': config.inst_type,
                'target_list': config.target_list
            }
    except Exception:
        tb = traceback.format_exc()
        print(f"select_ai_config_serving_for_module Exception: {tb}")

    return serving_targets


def select_ai_config_serving_for_target(module: str, inst_type: str, target_id: str) -> dict:
    """
    ai_config_serving 테이블의 부하예측(RMC) 데이터를 조회

    :param module: XAIOps 기능 명 ex) 'exem_aiops_load_fcst'
    :param inst_type: XAIOps instance type ex) 'was', 'db'
    :param target_id: XAIOps target id ex) 'all' / db타입의 경우 product type ex) 'ORACLE'
    :return: 서빙 대상 정보
    ex) {'exem_aiops_load_fcst_was_all': {
                "module":"exem_aiops_load_fcst",
                "target_id":"all",
                "inst_type":"was",
                "target_list": ["1201", "1202", ...,]
                }
            }
    """
    db.connect(reuse_if_open=True)
    serving_targets = {}
    try:
        query = AiConfigServing.select().where(
            (AiConfigServing.module == module)
            & (AiConfigServing.inst_type == inst_type)
            & (AiConfigServing.target_id == target_id))

        for config in query:
            serving_name = f"{config.module}_{config.inst_type}_{config.target_id}"
            serving_targets[serving_name] = {
                'module': config.module,
                'target_id': config.target_id,
                'inst_type': config.inst_type,
                'target_list': config.target_list
            }
    except Exception:
        tb = traceback.format_exc()
        print(f"select_ai_config_serving_for_target Exception: {tb}")

    return serving_targets


def get_log_regex(target_id: str):
    """
    log regex 정보를 database 에서 조회하여 반환하는 함수
    :param target_id: 업데이트된 로그 타겟
    :return:
    """
    regex_list = []
    delimiters = " "
    db.connect(reuse_if_open=True)
    try:
        query1 = XaiopsConfigLog.select().where(XaiopsConfigLog.target_id == target_id).dicts()
        reg_id = query1[0]['regset_id']
        query2 = AiConfigLogRegex.select().where(AiConfigLogRegex.regset_id == reg_id).dicts()
        query_result = [dict(record) for record in query2]
        if len(query_result) > 0:
            for item in query_result:
                if item["delimiter"]:
                    delimiters = item["regex"]
                else:
                    regex = [item["regex"], item["replace_str"]]
                    regex_list.append(regex)
        else:
            regex_list = basereg.COMMON_REGEX
            delimiters = basereg.COMMON_DELIMITER

    except Exception as ex:
        print(f"unable to get regex from the database : {ex}")

    return regex_list, delimiters


def get_log_params(target_id: str) -> pd.DataFrame:
    """
    log 서빙 관련 파라미터 정보를 database 에서 조회하여 반환하는 함수
    :param target_id: 업데이트 된 로그 타겟
    :return: 해당 타겟의 파라미터 설정 값, 테이블 xaiops_config_log , 테이블 ai_config_serving_log_digcn 의 merge 결과 dataframe
    """
    result = pd.DataFrame()
    db.connect(reuse_if_open=True)
    try:
        query1 = XaiopsConfigLog.select().where(XaiopsConfigLog.target_id == target_id).dicts()
        query2 = AiConfigServingLogDigcn.select().where(AiConfigServingLogDigcn.target_id == target_id).dicts()

        df1 = pd.DataFrame(list(query1))
        df2 = pd.DataFrame(list(query2))
        result = pd.merge(df1, df2)
    except Exception:
        raise Exception("Error during query from database : 'xaiops_config_log', 'ai_config_serving_log_digcn'")

    return result


def get_sparselog_params(target_id: str) -> pd.DataFrame:
    """
    sparse log 서빙 관련 파라미터 정보를 database 에서 조회하여 반환하는 함수
    :param target_id: 업데이트된 로그 타겟 정보
    :return: 테이블 xaiops_config_log, 테이블 ai_config_serving_log_sparse, 테이블 ai_config_serving_log_keyword 의 merge 결과 dataframe
    """
    result = pd.DataFrame()
    db.connect(reuse_if_open=True)
    try:
        query1 = XaiopsConfigLog.select(XaiopsConfigLog.log_id, XaiopsConfigLog.target_id).where(XaiopsConfigLog.target_id == target_id).dicts()
        log_id = query1[0]['log_id']

        query2 = AiConfigSparse.select().where(AiConfigSparse.log_id == log_id).dicts()
        query3 = AiConfigLogKeyword.select().where(AiConfigLogKeyword.log_id == log_id).dicts()  # 하나의 log_id는 여러개의 keyword 를 가질 수 있음
        df2 = pd.DataFrame(list(query2))
        df3 = pd.DataFrame(list(query3))

        if df3.empty:
            result = df2.copy()
            result['keyword_type'] = None
            result['keyword'] = None
        else:
            result = pd.merge(df2, df3, how="outer")

    except Exception:
        raise Exception("Error during query from database : 'xaiops_config_log', 'ai_config_serving_log_sparse', 'ai_config_serving_log_keyword'")

    return result


def get_serving_target_info(module: str, inst_type: str, target_id: str) -> dict:
    """

    :param module: XAIOps 기능명
    :param inst_type : 서빙 대상 타입
    :param target_id: 서빙 대상 타겟 아이디
    :return:
    """
    serving_target = {}
    db.connect(reuse_if_open=True)
    try:
        query = AiConfigServing.select().where(
            (AiConfigServing.inst_type == inst_type) &
            (AiConfigServing.module == module) &
            (AiConfigServing.target_id == target_id)
        )

        for config in query:
            serving_name = f"{config.module}_{config.inst_type}_{config.target_id}"
            serving_target[serving_name] = {
                'module': config.module,
                'target_id': config.target_id,
                'inst_type': config.inst_type,
                'target_list': config.target_list
            }
    except Exception:
        tb = traceback.format_exc()
        print("get_serving_target_info Exception: {tb}")

    return serving_target


def update_service_onboot(update_list: list) -> bool:
    """
    ai_config_serving 테이블의 service_on_boot 컬럼을 업데이트 하는 함수
    :param update_list: 업데이트에 사용될 request body data
    :return: True/False
    """
    db.connect(reuse_if_open=True)
    try:
        with db.atomic():
            for item in update_list:
                query = AiConfigServing.update(service_on_boot=item["service_onboot"]).where(
                    AiConfigServing.serving_name == item["serving_name"]
                )
                query.execute()
        return True

    except Exception as e:
        return False


def update_log_serving(
        update_serving_config_list: list,
        update_log_config_list: list,
        update_log_digcn_list: list,
        update_log_sparse_list: list,
        update_log_exclude_keyword_list: list,
        update_log_include_keyword_list: list
) -> bool:
    """
    로그 서빙 페이지 관련 테이블들 업데이트 하는 함수 (트랜잭션 적용)

    :param update_serving_config_list: ai_config_serving 테이블 업데이트에 사용될 request body data
    :param update_log_config_list: xaiops_config_log 테이블 업데이트에 사용될 request body data
    :param update_log_digcn_list: ai_config_serving_log_digcn 테이블 업데이트에 사용될 request body data
    :param update_log_sparse_list: ai_config_serving_log_sparse 테이블 업데이트에 사용될 request body data
    :param update_log_exclude_keyword_list: ai_config_serving_log_keyword 테이블의 exclude 업데이트에 사용될 request body data
    :param update_log_include_keyword_list: ai_config_serving_log_keyword 테이블의 include 업데이트에 사용될 request body data
    :return: True/False
    """
    db.connect(reuse_if_open=True)
    try:
        with db.atomic():
            # 1) 부팅 시 실행 : ai_config_serving 테이블 업데이트
            for item in update_serving_config_list:
                query = AiConfigServing.update(service_on_boot=item["service_onboot"]).where(
                    AiConfigServing.target_id == item["target_id"]
                )
                query.execute()

            # 2) 이상패턴로그,프리셋 : xaiops_config_log 테이블 업데이트
            for item in update_log_config_list:
                preset_id = AiConfigLogRegexPreset.select(AiConfigLogRegexPreset.regset_id).where(
                    AiConfigLogRegexPreset.set_name == item["preset_name"]
                )
                if preset_id:
                    query1 = XaiopsConfigLog.update(regset_id=preset_id).where(
                        XaiopsConfigLog.target_id == item["target_id"]
                    )
                    query1.execute()
                query2 = XaiopsConfigLog.update(is_service_on=item["is_service_on"]).where(
                    XaiopsConfigLog.target_id == item["target_id"]
                )
                query2.execute()

            # 3) 로그이상탐지(digcn)임계치 설정 : ai_config_serving_log_digcn 테이블 업데이트
            for item in update_log_digcn_list:
                auto_value = json.dumps({"anomaly_threshold": item["passive_anomaly_threshold"]})
                recommend_value = json.dumps({"anomaly_threshold": item["auto_anomaly_threshold"]})
                query = AiConfigServingLogDigcn.update(
                    is_params_auto=item["is_params_auto"],
                    params=auto_value,
                    recommend_param=recommend_value
                ).where(
                    AiConfigServingLogDigcn.target_id == item["target_id"]
                )
                query.execute()

            # 4) 희소로그, 알림기준, 검출상한가 : ai_config_serving_log_sparse 테이블 업데이트
            for item in update_log_sparse_list:
                log_id_query = XaiopsConfigLog.select(XaiopsConfigLog.log_id).where(
                    XaiopsConfigLog.target_id == item["target_id"]
                )
                log_id = log_id_query.scalar()
                query = AiConfigSparse.update(
                    alert_threshold=item["alert_threshold"],
                    rare_rate=item["rare_rate"],
                    is_service_on=item["is_service_on"]
                ).where(
                    AiConfigSparse.log_id == log_id
                )
                query.execute()

            # 5-1) 키워드(제외 키워드) : ai_config_serving_log_keyword
            for item in update_log_exclude_keyword_list:
                keyword_type = 'exclude'
                keyword_list = item["keyword_list"]

                log_id_query = XaiopsConfigLog.select(XaiopsConfigLog.log_id).where(
                    XaiopsConfigLog.target_id == item["target_id"]
                )
                log_id = log_id_query.scalar()

                # 제외 키워드 제거 null 초기화
                if keyword_list is None:
                    # 관련 해당 log_id 기존 레코드 삭제
                    AiConfigLogKeyword.delete().where(
                        (AiConfigLogKeyword.log_id == log_id) &
                        (AiConfigLogKeyword.keyword_type == keyword_type)
                    ).execute()

                # 제외 키워드 존재하는 경우
                else:
                    keyword_list = [item.strip() for item in keyword_list]  # 공백 제거
                    existing_records_query = AiConfigLogKeyword.select().where(
                        (AiConfigLogKeyword.log_id == log_id) &
                        (AiConfigLogKeyword.keyword_type == keyword_type)
                    )

                    existing_keywords = [record.keyword for record in existing_records_query]

                    if not existing_keywords:  # 기존의 레코드 존재하지않는 경우 바로 생성
                        for key in keyword_list:
                            AiConfigLogKeyword.create(log_id=log_id, keyword=key, keyword_type=keyword_type)

                    else:  # 기존의 레코드가 존재하는 경우
                        intersection = set(existing_keywords).intersection(keyword_list)
                        if intersection:
                            keyword_list = [keyword for keyword in keyword_list if keyword not in existing_keywords]
                        else:
                            # 생성하려는 키워드가 기존의 키워드와 중복되지 않는 경우 (기존 제거-> 신규 생성)
                            AiConfigLogKeyword.delete().where(
                                (AiConfigLogKeyword.log_id == log_id) &
                                (AiConfigLogKeyword.keyword_type == keyword_type)
                            ).execute()

                        for key in keyword_list:
                            AiConfigLogKeyword.create(log_id=log_id, keyword=key, keyword_type=keyword_type)

            # 5-2) 키워드(포함 키워드) : ai_config_serving_log_keyword
            for item in update_log_include_keyword_list:
                keyword_type = 'include'
                keyword_list = item["keyword_list"]

                log_id_query = XaiopsConfigLog.select(XaiopsConfigLog.log_id).where(
                    XaiopsConfigLog.target_id == item["target_id"]
                )
                log_id = log_id_query.scalar()

                # 포함 키워드 제거 null 초기화
                if keyword_list is None:
                    # 관련 해당 log_id 기존 레코드 삭제
                    AiConfigLogKeyword.delete().where(
                        (AiConfigLogKeyword.log_id == log_id) &
                        (AiConfigLogKeyword.keyword_type == keyword_type)
                    ).execute()

                # 포함 키워드 존재하는 경우
                else:
                    keyword_list = [item.strip() for item in keyword_list]  # 공백 제거
                    existing_records_query = AiConfigLogKeyword.select().where(
                        (AiConfigLogKeyword.log_id == log_id) &
                        (AiConfigLogKeyword.keyword_type == keyword_type)
                    )

                    existing_keywords = [record.keyword for record in existing_records_query]

                    if not existing_keywords:  # 기존의 레코드 존재하지않는 경우 바로 생성
                        for key in keyword_list:
                            AiConfigLogKeyword.create(log_id=log_id, keyword=key, keyword_type=keyword_type)

                    else:  # 기존의 레코드가 존재하는 경우
                        intersection = set(existing_keywords).intersection(keyword_list)
                        if intersection:
                            keyword_list = [keyword for keyword in keyword_list if
                                            keyword not in existing_keywords]
                        else:
                            # 생성하려는 키워드가 기존의 키워드와 중복되지 않는 경우 (기존 제거-> 신규 생성)
                            AiConfigLogKeyword.delete().where(
                                (AiConfigLogKeyword.log_id == log_id) &
                                (AiConfigLogKeyword.keyword_type == keyword_type)
                            ).execute()

                        for key in keyword_list:
                            AiConfigLogKeyword.create(log_id=log_id, keyword=key, keyword_type=keyword_type)
        return True
    except Exception as e:
        return False
