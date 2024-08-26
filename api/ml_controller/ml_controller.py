import json
import time
import traceback
import argparse

from pathlib import Path as Path_
from typing import List
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request, Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from orm.main import *
from api.ml_controller.ml_model_manager import ModelManager
from api.ml_controller.ml_utils import InitAPI, RunUtils, make_log_serving_response, ServingModule, LogServingModule
from api.model.serving_model import UpdateConfigRequestModel, GroupMenuItem, TargetMenuItem, TargetLogItem, GroupOnOffItem, TargetOnOffItem
from api.model.response_model import ResponseModel

from common.constants import MLControllerConstants as mc
from common.constants import SystemConstants as sc
from common.redisai import REDISAI, REDIS
from common.system_util import SystemUtil
from resources.logger_manager import Logger

##########################################################
#                    Uvicorn Fast API                    #
##########################################################
app = FastAPI(title="XAIOps MLC-api")
app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

os_env = SystemUtil.get_environment_variable()
py_path, py_config, log_path = RunUtils.get_server_run_configuration()


# 추후 삭제
@app.post("/mlc/serving/init",
          status_code=200,
          tags=["MLC"],
          summary="초기 서빙을 위한 mlops system 구성 준비 요청 #현재 미사용",
          include_in_schema=False,
          responses={400: {"description": "mlops system error"}, 409: {"description": "Duplicate request error"},
                     500: {"description": "Unknown error"}})
def init_serving():
    return "[INITIAL] Ready to take serving requests"


def redis_store():
    """
        최초 mlc 기동 시 self initializing
        1) redis connection health check
        2) local model file -> redis-ai 업로드
    :return: 없음
    """
    try:
        retry_count = 5
        host = py_config['redis_server']['master']['host']
        port = int(py_config['redis_server']['master']['port'])
        # redis health check
        for i in range(retry_count):
            redis_status = REDISAI.check_redis_health(host, port)
            if redis_status:
                break
            else:
                time.sleep(1)

        if redis_status:
            # model store to redis
            logger.info("[============== Start Redis ModelStore ==============]")
            ModelManager.load_model()
            logger.info("[============== End of Redis ModelStore ==============]")
        else:
            logger.warning(f"[redis status : {redis_status}. check for redis-ai ip, port configuration]")
            # sys.exit(1)

    except Exception:
        tb = traceback.format_exc()
        logger.info(f"redis_store Exception: {tb}")
        # sys.exit(1) # process 강종


@app.patch("/mlc/model/{sys_id}/{module_name}/{inst_type}/{target_id}",
           tags=["MLC"],
           summary="모델 업데이트에 대한 요청 #tsa -> mlc",
           responses={404: {"description": "model update Failure"}})
async def reload(sys_id: str, module_name: str, inst_type: str, target_id: str):
    try:
        if inst_type == "syslog" or inst_type == "filelog":
            inst_type = "log"

        modelmanager = ModelManager()
        model_default_path = modelmanager.get_server_run_configuration()
        model_path = Path_(model_default_path) / sys_id / module_name / inst_type / target_id
        modelmanager.load_model(path=model_path, reload=True)
        logger.info(f"[RELOAD]{sys_id}_{module_name}_{inst_type}_{target_id} Done")

        if module_name in ["exem_aiops_anls_inst", "exem_aiops_anls_log", "exem_aiops_fcst_tsmixer"]:
            response = REDIS.update_serving_target(module_name, inst_type, target_id)
            logger.info(response)
        elif module_name in ["exem_aiops_load_fcst", "exem_aiops_event_fcst"]:
            target_info = get_serving_target_info(module_name, inst_type, target_id)
            response = REDIS.update_serving_group(module_name, inst_type, target_id, target_info)
            logger.info(response)

        return f"[RELOAD]{sys_id}_{module_name}_{inst_type}_{target_id} Done"
    except Exception as e:
        tb = traceback.format_exc()
        logger.info(f"reload Exception: {tb}")
        raise HTTPException(status_code=404, detail=f"model update Failure : {e}")


@app.post("/mlc/config/update",
          tags=["MLC"],
          summary="타겟 서빙 config 업데이트 #현재미사용",
          include_in_schema=False)
def config_update(requestparam: UpdateConfigRequestModel):
    sys_id = requestparam.sys_id
    inst_type = requestparam.inst_type
    target_id = requestparam.target_id
    module_name = 'exem_aiops_anls_inst'
    logger.info(f"[/mlc/config/update API] {sys_id}_{module_name}_{inst_type}_{target_id} update start")
    model_config_path = str(
        Path_(os_env[sc.AIMODULE_HOME]) / "model" / f"{sys_id}" / f"{module_name}" / f"{inst_type}" / f"{target_id}")
    model_config_key = REDISAI.make_redis_model_key(f"{model_config_path}/model_config", "")

    try:
        model_config = REDISAI.inference_json(model_config_key)
        with open(f'{model_config_path}/model_config.json', 'w') as f:
            json.dump(model_config, f)

        return f"[UPDATE]{sys_id}_{module_name}_{inst_type}_{target_id} Done"
    except Exception as e:
        tb = traceback.format_exc()
        logger.info(f"config_update Exception: {tb}")
        raise HTTPException(status_code=404, detail=f"fail to update config : {e}")


@app.patch("/mlc/rsa/update/parameter/{module_name}/{inst_type}/{target_id}",
           tags=["RSA"],
           summary="로그 서빙 파라미터 업데이트 #BE java api -> mlc",
           responses={404: {"description": "log parameter update Failure"}})
async def update_log_params(module_name: str, inst_type: str, target_id: str):
    f"""
    로그 서빙프로세스 화면에서 파라미터 업데이트 요청 시 호출되는 함수
    요청받은 로그 대상을 기준으로 DB 조회하여 파라미터 값을 redis-ai 에 직접 업데이트함
    redis-ai 키 종류
    - key_prefix/parameter 

    :param module_name: exem_aiops_anls_log
    :param inst_type: log
    :param target_id: ex) os.log.1234
    """
    sys_id = py_config['sys_id']
    inst_type = 'log'
    key_prefix = f"{sys_id}/{module_name}/{inst_type}/{target_id}"
    try:
        log_params = get_log_params(target_id)
        sparse_params = get_sparselog_params(target_id)
        parameter = make_log_serving_response(log_params, sparse_params)
        REDISAI.set(f"{key_prefix}/parameter", parameter)
        logger.info(f"[update_log_params] {key_prefix}/parameter successfully updated")

        regex_list, delimiters = get_log_regex(target_id)
        REDISAI.set(f"{key_prefix}/regex_list", regex_list)
        REDISAI.set(f"{key_prefix}/delimiters", delimiters)
        logger.info(f"[update_log_params] {key_prefix}/regex_list successfully updated")
        logger.info(f"[update_log_params] {key_prefix}/delimiters successfully updated")

    except Exception as e:
        tb = traceback.format_exc()
        logger.info(f"update_log_params Exception: {tb}")
        raise HTTPException(status_code=404, detail=f"log parameter update Failure : {str(e)}")

    return f"[UPDATE]{sys_id}_{module_name}_{inst_type}_{target_id} Done"


##########################################################
#                        서빙  API                        #
##########################################################


@app.get("/mlc/rsa/status",
         tags=["RSA"],
         summary="현재 서빙중인 전체 대상 정보를 제공",
         responses={404: {"description": "no serving status"}})
async def serving_status():
    try:
        targets = REDIS.hgetall('RedisServingTargets::mlc')

    except Exception as e:
        logger.warning("조회할 서빙 status 가 없습니다.")
        raise HTTPException(status_code=404, detail="no serving status")
    return targets


@app.get("/mlc/serving/service/{service_id}/type/{type_}/group-list",
        tags=["RSA (FE)"],
        summary="설정>학습/서비스>서빙 화면에서 AI서비스 & 타입 선택 시 그룹 목록을 리턴",
        response_model=ResponseModel)
async def serving_group_list(
    service_id: ServingModule = Path(..., description="AI 서비스 명"),
    type_: str = Path(..., description="인스턴스 타입, DB타입의 경우 product_type, ex) 'was', 'ORACLE', 'os'")
    ):
    try:
        if type_ in ["ORACLE", "TIBERO", "POSTGRES"]:
            inst_type = "db"
            product_type = type_
        else:
            inst_type = type_
            product_type = None

        group_list = select_group_list(service_id, inst_type, product_type)
        response = ResponseModel(success=True, message=None, total=len(group_list), data=group_list)
        return response
    except Exception:
        tb = traceback.format_exc()
        response = ResponseModel(success=False, message="unknown error", total=0, data=None)
        logger.error(f"[/mlc/rsa/serving/group] Exception: {tb}")
        return JSONResponse(status_code=400, content=response.dict())


@app.get("/mlc/serving/service/{service_id}/type/{type_}/target-list",
         tags=["RSA (FE)"],
         summary="설정>학습/서비스>서빙 화면에서 로그이상탐지 AI 서비스 선택 시 타겟 목록을 리턴 // 로그 AI 서비스 전용",
         response_model=ResponseModel)
async def log_serv_target_list(
    service_id: LogServingModule = Path(..., description="로그 AI 서비스 명 ex) exem_aiops_anls_log"),
    type_: str = Path(..., description="로그 AI 서비스의 log_type ex) 'syslog', 'filelog'")
    ):
    try:
        log_type = type_
        target_list = select_log_service_list(service_id, log_type)
        response = ResponseModel(success=True, message=None, total=len(target_list), data=target_list)
        return response
    except Exception:
        tb = traceback.format_exc()
        response = ResponseModel(success=False, message="unknown error", total=0, data=None)
        logger.error(f"[/mlc/rsa/serving/target] Exception: {tb}")
        return JSONResponse(status_code=400, content=response.dict())


@app.get("/mlc/serving/service/{service_id}/type/{type_}/group/{group_id}/target-list",
         tags=["RSA (FE)"],
         summary="설정>학습/서비스>서빙 화면에서 특정 그룹 선택 시 타겟 목록을 리턴 // 로그를 제외한 AI 서비스 대상",
         response_model=ResponseModel)
async def serving_target_list(
    service_id: ServingModule = Path(..., description="AI 서비스 명"),
    type_: str = Path(..., description="인스턴스 타입, DB타입의 경우 product_type ex) 'was', 'ORACLE', 'os'"),
    group_id: int = Path(..., description="그룹 아이디 ex) 175")
    ):
    try:
        if type_ in ["ORACLE", "TIBERO", "POSTGRES"]:
            inst_type = "db"
            product_type = type_
        else:
            inst_type = type_
            product_type = None

        target_list = select_group_target_list(service_id, inst_type, product_type, group_id)
        response = ResponseModel(success=True, message=None, total=len(target_list), data=target_list)
        return response
    except Exception:
        tb = traceback.format_exc()
        response = ResponseModel(success=False, message="unknown error", total=0, data=None)
        logger.error(f"[/mlc/rsa/serving/target] Exception: {tb}")
        return JSONResponse(status_code=400, content=response.dict())


@app.put("/mlc/serving/group/param/update", tags=["RSA (FE)"],
           summary="[서빙] 화면에서 [서빙그룹목록]의 파라미터 업데이트 요청  (로그가 아닌 기본적인 AI서비스들)",
           response_model=ResponseModel)
async def update_group_serving_params(
        request: List[GroupMenuItem]
):
    try:
        if not request:
            response = ResponseModel(success=False, message="request is empty.", total=0, data=None)
            return JSONResponse(status_code=400, content=response.dict())

        update_lists = []
        for item in request:
            ai_service = item.service
            type_ = item.type
            serving_name = item.servingName
            service_onboot = item.serviceOnBoot
            group_id = item.groupId

            if type_ in ["ORACLE", "TIBERO", "POSTGRES"]:
                inst_type = "db"
                product_type = type_
            else:
                inst_type = type_
                product_type = None
            # 그룹단위로 관리되는 경우
            if ai_service in ["exem_aiops_event_fcst", "exem_aiops_load_fcst"]:
                update_lists.append({
                    'serving_name': serving_name,  # 예시 exem_aiops_load_fcst_was_all
                    'service_onboot': service_onboot
                })
            # 타겟단위로 관리되는 경우
            else:
                group_target_list = select_group_target_list(ai_service, inst_type, product_type, group_id)
                for target in group_target_list:
                    update_lists.append({
                        'serving_name': target['servingName'],
                        'service_onboot': service_onboot
                    })

        query_status = update_service_onboot(update_lists)
        if query_status:  # 정상 처리
            response = ResponseModel(success=True, message=None, total=0, data=None)
            return response
        else:  # 실패 처리
            response = ResponseModel(success=False, message="update failed", total=0, data=None)
            return JSONResponse(status_code=400, content=response.dict())

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"[/mlc/serving/group/param/update] Exception: {tb}")
        response = ResponseModel(success=False, message="unknown error", total=0, data=None)
        return JSONResponse(status_code=500, content=response.dict())


@app.patch("/mlc/serving/target/param/update", tags=["RSA (FE)"],
           summary="[서빙] - [특정 서빙그룹] 에서의 [개별 타겟] 의 파라미터 업데이트 요청  (로그가 아닌 기본적인 AI서비스들)",
           response_model=ResponseModel)
async def update_target_serving_params(
        request: List[TargetMenuItem]
):
    try:
        if not request:
            response = ResponseModel(success=False, message="No request information", total=0, data=None)
            return JSONResponse(status_code=400, content=response.dict())

        update_list = []
        for item in request:
            ai_service = item.service
            if ai_service in ["exem_aiops_event_fcst", "exem_aiops_load_fcst"]:
                response = ResponseModel(success=False,
                                         message=f"Invalid ai_service for individual target updates :{ai_service}",
                                         total=0, data=None)
                return JSONResponse(status_code=400, content=response.dict())
            serving_name = item.servingName
            service_onboot = item.serviceOnBoot
            update_list.append({
                'serving_name': serving_name,
                'service_onboot': service_onboot
            })
        query_status = update_service_onboot(update_list)
        if query_status:  # 정상 처리
            response = ResponseModel(success=True, message=None, total=0, data=None)
            return response
        else:  # 실패 처리
            response = ResponseModel(success=False, message="update failed", total=0, data=None)
            return JSONResponse(status_code=400, content=response.dict())

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"[/mlc/serving/target/param/update] Exception: {tb}")
        response = ResponseModel(success=False, message="unknown error", total=0, data=None)
        return JSONResponse(status_code=500, content=response.dict())


@app.patch("/mlc/serving/log/param/update", tags=["RSA (FE)"],
           summary="[서빙] - [로그 이상탐지] AI서비스에서 [개별 타겟] 의 파라미터 업데이트 요청 ",
           response_model=ResponseModel)
async def update_serving_params_log(request: List[TargetLogItem]):
    try:
        if not request:
            response = ResponseModel(success=False, message="No request information", total=0, data=None)
            return JSONResponse(status_code=400, content=response.dict())

        update_serving_config_list = []  # ai_config_serving
        update_log_config_list = []      # xaiops_config_log
        update_log_digcn_list = []       # ai_config_serving_log_digcn
        update_log_sparse_list = []      # ai_config_serving_log_sparse
        update_log_exclude_keyword_list = []     # ai_config_log_keyword (exclude)
        update_log_include_keyword_list = []     # ai_config_log_keyword (include)
        for item in request:
            target_id = item.targetId
            service_onboot = item.serviceOnBoot
            exclude_keywords = item.excludeKeywords
            include_keywords = item.userKeywords
            is_param_auto = item.isParamAuto
            auto_anomaly_threshold = item.autoAnomalyThreshold  # recommand
            passive_anomaly_threshold = item.anomalyThreshold  # params
            set_name = item.setName
            is_log_service_on = item.isLogServiceOn
            alert_threshold = item.alertThreshold
            rare_rate = item.rareRate
            is_sparse_service_on = item.isSparseServiceOn

            update_serving_config_list.append({
                'target_id': target_id,
                'service_onboot': service_onboot
            })
            update_log_config_list.append({
                'target_id': target_id,
                'preset_name': set_name,
                'is_service_on': is_log_service_on,
            })
            update_log_digcn_list.append({
                'target_id': target_id,
                'is_params_auto': is_param_auto,
                'auto_anomaly_threshold': auto_anomaly_threshold,
                'passive_anomaly_threshold': passive_anomaly_threshold,
            })
            update_log_sparse_list.append({
                'target_id': target_id,
                'alert_threshold': alert_threshold,
                'rare_rate': rare_rate,
                'is_service_on': is_sparse_service_on,
            })
            if exclude_keywords:
                update_log_exclude_keyword_list.append({
                    'target_id': target_id,
                    'keyword_type': 'exclude',
                    'keyword_list': exclude_keywords
                })
            else:
                update_log_exclude_keyword_list.append({
                    'target_id': target_id,
                    'keyword_type': None,
                    'keyword_list': None
                })
            if include_keywords:
                update_log_include_keyword_list.append({
                    'target_id': target_id,
                    'keyword_type': 'include',
                    'keyword_list': include_keywords
                })
            else:
                update_log_include_keyword_list.append({
                    'target_id': target_id,
                    'keyword_type': None,
                    'keyword_list': None
                })

        query_status = update_log_serving(
            update_serving_config_list, update_log_config_list, update_log_digcn_list, update_log_sparse_list,
            update_log_exclude_keyword_list, update_log_include_keyword_list
        )
        if query_status:  # 정상 처리
            response = ResponseModel(success=True, message=None, total=0, data=None)
            return response
        else:  # 실패 처리
            response = ResponseModel(success=False, message="update failed", total=0, data=None)
            return JSONResponse(status_code=400, content=response.dict())

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"[/mlc/serving/log/param/update] Exception: {tb}")
        response = ResponseModel(success=False, message="unknown error", total=0, data=None)
        return JSONResponse(status_code=500, content=response.dict())


async def on_serving_target(ai_service, inst_type, target_id):
    try:
        serving_name = f"{ai_service}_{inst_type}_{target_id}"
        serving_targets = {}
        serving_targets[serving_name] = {
            'service_name': serving_name,
            'module': ai_service,
            'target_id': target_id,
            'type': inst_type
        }
        REDIS.hset(serving_targets)

        if ai_service == 'exem_aiops_load_fcst':
            loadfcst_targets = select_ai_config_serving_for_target('exem_aiops_load_fcst', inst_type, target_id)
            REDIS.loadfcst_set(loadfcst_targets)
        if ai_service == 'exem_aiops_event_fcst':
            eventfcst_targets = select_ai_config_serving_for_target('exem_aiops_event_fcst', inst_type, target_id)
            REDIS.eventfcst_set(eventfcst_targets)
        return True
    except Exception:
        tb = traceback.format_exc()
        logger.info(f"on_serving_target Exception: {tb}")
        return False


async def off_serving_target(ai_service, inst_type, target_id):
    try:
        serving_name = f"{ai_service}_{inst_type}_{target_id}"
        REDIS.hdel(serving_name)

        if ai_service == 'exem_aiops_load_fcst':
            REDIS.loadfcst_del(inst_type, target_id)
        if ai_service == 'exem_aiops_event_fcst':
            REDIS.eventfcst_del(inst_type, target_id, ai_service)
        return True
    except Exception:
        tb = traceback.format_exc()
        logger.info(f"off_serving_target Exception: {tb}")
        return False


@app.put("/mlc/serving/group/on-off", tags=["RSA (FE)"],
         summary="[그룹]에 대한 서빙 활성화 or 비활성화 요청",
         response_model=ResponseModel)
async def on_off_serving_group(
        request: List[GroupOnOffItem]
):
    try:
        if not request:
            response = ResponseModel(success=False, message="No request information", total=0, data=None)
            return JSONResponse(status_code=400, content=response.dict())

        for item in request:
            onOff_flag = item.onOff
            ai_service = item.service
            type_ = item.type
            group_id = item.groupId
            if type_ in ["ORACLE", "TIBERO", "POSTGRES"]:
                inst_type = "db"
                product_type = type_
            else:
                inst_type = type_
                product_type = None

            if onOff_flag:  # 서빙 활성화
                if ai_service == "exem_aiops_event_fcst":
                    await on_serving_target(ai_service, inst_type, group_id)
                elif ai_service == "exem_aiops_load_fcst":
                    if inst_type == 'db':
                        target_id = product_type
                    else:
                        target_id = "all"

                    await on_serving_target(ai_service, inst_type, target_id)
                else:
                    if ai_service == 'exem_aiops_anls_log':
                        target_list = select_log_service_list(ai_service, inst_type)
                    else:
                        target_list = select_group_target_list(ai_service, inst_type, product_type, group_id)
                    for target in target_list:
                        await on_serving_target(ai_service, inst_type, target['targetId'])
            else:  # 서빙 비활성화
                if ai_service == "exem_aiops_event_fcst":
                    await off_serving_target(ai_service, inst_type, group_id)
                elif ai_service == "exem_aiops_load_fcst":
                    if inst_type == 'db':
                        target_id = product_type
                    else:
                        target_id = "all"
                    await off_serving_target(ai_service, inst_type, target_id)
                else:
                    if ai_service == 'exem_aiops_anls_log':
                        target_list = select_log_service_list(ai_service, inst_type)
                    else:
                        target_list = select_group_target_list(ai_service, inst_type, product_type, group_id)
                    for target in target_list:
                        await off_serving_target(ai_service, inst_type, target['targetId'])

        response = ResponseModel(success=True, message=None, total=0, data=None)
        return response

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"[/mlc/serving/group/on-off] Exception: {tb}")
        response = ResponseModel(success=False, message="unknown error", total=0, data=None)
        return JSONResponse(status_code=400, content=response.dict())


@app.patch("/mlc/serving/target/on-off",
           tags=["RSA (FE)"],
           summary="[개별 타겟]에 대한 서빙 활성화 or 비활성화 요청",
           response_model=ResponseModel)
async def on_off_serving_target(
        request: List[TargetOnOffItem]
):
    try:
        if not request:
            response = ResponseModel(success=False, message="No request information", total=0, data=None)
            return JSONResponse(status_code=400, content=response.dict())

        for item in request:
            onOff_flag = item.onOff
            ai_service = item.service
            serving_name = item.servingName
            type_ = item.type
            if type_ in ["ORACLE", "TIBERO", "POSTGRES"]:
                inst_type = "db"
            else:
                inst_type = type_
            target_id = item.targetId

            if onOff_flag:  # 서빙 활성화
                await on_serving_target(ai_service, inst_type, target_id)
                logger.info(f"[/mlc/serving/target/on-off] success {serving_name}")
            else:  # 서빙 비활성화
                await off_serving_target(ai_service, inst_type, target_id)
                logger.info(f"[/mlc/serving/target/on-off] success {serving_name}")
        response = ResponseModel(success=True, message=None, total=0, data=None)
        return response
    except Exception:
        tb = traceback.format_exc()
        logger.error(f"[/mlc/serving/target/on-off] Exception: {tb}")
        response = ResponseModel(success=False, message="target on-off failed", total=0, data=None)
        return JSONResponse(status_code=400, content=response.dict())


@app.patch("/mlc/rsa/delete/{inst_type}/{target_id}",
           tags=["RSA"],
           summary="시스템 설정에서 대상이 제거된 경우 redis에서 해당 대상 제거",
           responses={404: {"description": "rsa delete Failure"}})
async def delete_serving_target(inst_type: str, target_id: str):
    """
    redis에 서빙 대상 정보를 제거하는 함수 (서빙 delete)

    - **inst_type**: XAIOps instance type ex) 'was', 'db', 'os'
    - **target_id**: XAIOps target id ex) '1201'
    - **return**: None
    """
    try:
        # group delete
        if inst_type in ["instanceGroup", "hostGroup", "codeGroup"]:
            REDIS.eventfcst_del(inst_type, target_id, 'exem_aiops_event_fcst')
        else: # target delete
            key_pattern = f"{inst_type}_{target_id}"
            key_list = REDIS.get_key_from_RedisServingTargets(key_pattern)
            for key in key_list:
                REDIS.hdel(key)
            REDIS.loadfcst_target_remove(inst_type, target_id)
            REDIS.eventfcst_target_remove(inst_type, target_id)
        logger.info(f"[/mlc/rsa/delete] success {inst_type} {target_id}")
    except Exception:
        tb = traceback.format_exc()
        logger.info(f"[/mlc/rsa/delete] Exception: {tb}")
        raise HTTPException(status_code=404, detail=f"[/mlc/rsa/delete] Failure")


@app.get("/mlc/serving/log-serving-info",
         tags=["RSA"],
         summary="로그 기능 서빙 대상 정보를 전달하는 api #log-serving scheduler에서 호출",
         responses={404: {"description": "log-serving-info Failure"}})
async def log_serving_info() -> list:
    """
    log serving parameter 정보 db 에서 조회하고 result 전달
    함수 동작 방식
    - 1) redis 에서 서빙 중인 대상 조회 (log target list)
    - 2) 위에서 서빙 중인 대상들의 parameter 정보 db select
    - 3) 기존 SS 에서 전달하던 json 포맷 형식으로 후처리 후 return

    :param sys_id = 시스템 ID
    :return = dict
    """
    try:
        targets = REDIS.hgetall('RedisServingTargets::mlc')
        log_serving_target_list = [json.loads(value)["target_id"] for key, value in targets.items() if
                                   'exem_aiops_anls_log' in key]
        logger.debug(f"[/mlc/serving/log-serving-info/] successfully return.")
        return log_serving_target_list
    except Exception as e:
        logger.error(f"[/mlc/serving/log-serving-info/] fail to return.")
        raise HTTPException(status_code=404, detail=f"[/mlc/rsa/off] Failure")

@app.on_event("startup")
def startup_event():
    logger.info(f"ml controller server start !!")
    print("UVICORN SERVER START....")
    if args.use_store:
        redis_store()
    else:
        logger.info("[================= Redis-ai caching is not used =================]")
        logger.info("*if you want to use Redis-ai caching, please use the --use-store option.\n"
                    "[Example] : $ python ml_controller.py --use-store")
        logger.info("[================================================================]")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"ml controller server shutdown !!")
    print(f"UVICORN SERVER SHUTDOWN....")


##########################################################
#                   Internal Function                    #
##########################################################


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the MLC with the option of caching the model file to Redis-ai")
    parser.add_argument("--use-store", action="store_true", help="Use Redis caching for model files")
    args = parser.parse_args()

    # 프로젝트 config-**.json 설정 값 가져와 초기 세팅
    py_path, py_config, log_path = RunUtils.get_server_run_configuration()

    error_log_dict = dict()
    error_log_dict["log_dir"] = str(Path_(log_path) / mc.MLC / "Error")
    error_log_dict["file_name"] = mc.LOGGER_FILE_NAME
    # mlc 의 log 설정
    logger = Logger().get_default_logger(logdir=log_path + f"/{mc.MLC}", service_name=mc.LOGGER_FILE_NAME,
                                         error_log_dict=error_log_dict)
    try:
        # mlc log 세부 설정 (formatter, handler,
        log_conf = json.load(open(Path_(py_path + sc.LOGGER_FILE_PATH) / sc.UVICORN_LOGGER_CONFIG_FILE))
    except Exception:
        tb = traceback.format_exc()
        print(f"log_config Exception: {tb}")

    try:
        logger.info("init redis serving targets")
        REDIS.init_serving_targets()  # 초기화
        logger.info("----------- onboot default serving list ----------- ")
        serving_targets = select_ai_config_serving_onboot()
        REDIS.hset(serving_targets)
        logger.info(serving_targets)

        logger.info("----------- onboot load-fcst group list ----------- ")
        loadfcst_targets = select_ai_config_serving_for_module('exem_aiops_load_fcst')
        REDIS.loadfcst_set(loadfcst_targets)
        logger.info(loadfcst_targets)

        logger.info("----------- onboot event-fcst group list ----------- ")
        eventfcst_targets = select_ai_config_serving_for_module('exem_aiops_event_fcst')
        REDIS.eventfcst_set(eventfcst_targets)
        logger.info(eventfcst_targets)

    except Exception:
        tb = traceback.format_exc()
        logger.info(f"select_ai_config_serving & redis save Exception: {tb}")

    print(f"host={py_config['module_api_server']['host']}, port={py_config['module_api_server']['port']}")
    uvicorn.run(
        app,
        host=py_config['module_api_server']['host'],
        port=py_config['module_api_server']['port'],
        access_log=True,
        reload=False,
        log_level="info",
        log_config=log_conf,
        workers=1,
        # factory=True
    )
