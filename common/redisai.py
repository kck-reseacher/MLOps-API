import json
import os
import re
import pickle
import threading
import numpy as np
from io import BytesIO

import joblib
import ml2rt
import redis
from gensim.models.doc2vec import Doc2Vec
import redisai
import rejson

from common.system_util import SystemUtil
from common.constants import SystemConstants as sc
from resources.config_manager import Config

os_env = SystemUtil.get_environment_variable()
py_config = Config(os_env[sc.AIMODULE_PATH], os_env[sc.AIMODULE_SERVER_ENV]).get_config()

redisai_clients, redisjson_clients = {}, {}
'''
이중화 서버를 사용하고 현 서버가 slave 서버가 아닌 경우
redis client는 local과 slave 정보를 둘다 가지고 있어야함.
그 외의 경우에는 local 정보만 가지고 있으면 됨.
'''

if py_config["use_slave_server"]:
    server_keys = [sc.MASTER, sc.SLAVE] if os_env[sc.MLOPS_SERVER_ENV] == sc.MASTER else [sc.SLAVE]
else:
    server_keys=[sc.MASTER]

for keys, info in py_config["redis_server"].items():
    redisai_clients[keys] = redisai.Client(host=py_config["redis_server"][keys]["host"], port=int(py_config["redis_server"][keys]["port"]))
    redisjson_clients[keys] = rejson.Client(host=py_config["redis_server"][keys]["host"],
                                     port=int(py_config["redis_server"][keys]["port"]), decode_responses=True)

redis_clients = redis.Redis(host=py_config["be_redis"]["host"], port=int(py_config["be_redis"]["port"]))

if not py_config["use_slave_server"]:
    del redisai_clients[sc.SLAVE]
    del redisjson_clients[sc.SLAVE]

print(f"REDIS CONNECTION {redisai_clients}")


class REDISAI:
    @staticmethod
    def check_redis_health(redis_ip: str, redis_port: int):
        """
            redis-server 상태 헬스체크하는 함수

        :param redis_ip: redis 접속 ip ex) 10.10.48.94
        :param redis_port: redis 접속 port ex) 17778
        :return: (ping O) True / (ping X) False
        """
        client = redis.StrictRedis(host=redis_ip, port=redis_port)
        try:
            res = client.ping()
            if res:
                return True
            else:
                return False
        except redis.ConnectionError:
            return False
        finally:
            client.close()

    @staticmethod
    def exist_key(key):
        if redisai_clients[server_keys[0]].exists(key) == 0:
            return False
        return True

    @staticmethod
    def _set(server, key, data):
        redisai_clients[server].set(key, data)

    @staticmethod
    def _modelstore(server, key, backend, device, data, timestamp):
        redisai_clients[server].modelstore(key, backend, device, data, tag=timestamp)

    ##############
    # model save #
    ##############
    @staticmethod
    def check_model_key(model_key):
        res = redisjson_clients[server_keys[0]].exists(model_key)
        return res

    @staticmethod
    def set_rejson(key, dbsln_model):
        """
            훈련되어 저장된 dbsln (pickle) 분해하여 redis key-value 형태로 저장
            예시) was_1201 -> tps, cpu, mem, ... 지표단위로 분리 -> 각 지표별 요일 정보로 분리 day0, day1, day2, ...
               key: was_1201_tps_day0 , was_1201_tps_day1 , ... , was_1201_mem_day7
               value: 0 ~ 1440 인덱스의 기초통계값
        """
        for feat in dbsln_model.keys():
            df = dbsln_model[feat]
            for idx in df.columns:
                suffix = f"day{idx}"
                obj = df[idx]
                redisjson_clients[server_keys[0]].jsonset(
                    f"{key}_{feat}_{suffix}", rejson.Path.rootPath(), json.loads(obj.to_json(orient='index'))
                )

    @staticmethod
    def save_onnx_to_redis(onnx_model_path, reload=False):
        """
            onnx file redis write
        """
        model_key = REDISAI.make_redis_model_key(onnx_model_path, ".onnx")
        if model_needs_update(onnx_model_path, model_key, reload):
            model_data = ml2rt.load_model(onnx_model_path)
            model_timestamp = os.path.getmtime(onnx_model_path)

            # threads = []
            for server_key in server_keys:
                thread = threading.Thread(target=REDISAI._modelstore, args=(server_key, model_key, 'ONNX', 'CPU', model_data, model_timestamp))
                thread.start()
                # threads.append(thread)
            # for thread in threads:
            #     thread.join()

            return model_key
        else:
            return f"[exist] {model_key}"

    @staticmethod
    def save_pickle_to_redis(pickle_model_path):
        """
            pickle file redis write
        """
        with open(pickle_model_path, "rb") as p:
            model_data = p.read() # bytes 로 저장.

        model_key = REDISAI.make_redis_model_key(pickle_model_path, ".pkl")

        # threads = []
        for server_key in server_keys:
            thread = threading.Thread(target=REDISAI._set, args=(server_key, model_key, model_data))
            thread.start()
           # threads.append(thread)
        # for thread in threads:
        #     thread.join()

        return model_key # service_1_target

    @staticmethod
    def save_service_to_redis(logger, root_path, pickle_file_list, reload=False):
        for file in pickle_file_list:
            pickle_model_path = os.path.join(root_path, file)

            with open(pickle_model_path, "rb") as f:
                model_dict = pickle.load(f)

            model_key = re.sub(r'/model/\d+/', '/model/', pickle_model_path).split("/model/")[1].replace(".pkl", "")
            if reload:
                REDISAI.set_rejson(model_key, model_dict)
                logger.info(f"RedisJSON set model_key: {model_key}")
            else:
                res = REDISAI.check_model_key(model_key)
                if res == 1:
                    logger.info(f"[exist]: {model_key}")
                else:
                    REDISAI.set_rejson(model_key, model_dict)
                    logger.info(f"RedisJSON set model_key: {model_key}")

    @staticmethod
    def save_json_to_redis(json_file_path):
        """
            json file (model_config) 를 redis write
        """
        with open(json_file_path, "rb") as f:
            json_data = f.read()

        if 'exem_aiops_anls_service' in json_file_path:
            json_key = re.sub(r'/model/\d+/', '/model/', json_file_path).split("/model/")[1].replace(".json", "")
        else:
            json_key = REDISAI.make_redis_model_key(json_file_path, ".json")

        # threads = []
        for server_key in server_keys:
            thread = threading.Thread(target=REDISAI._set, args=(server_key, json_key, json_data))
            thread.start()
            # threads.append(thread)
        # for thread in threads:
        #     thread.join()

        return json_key

    @staticmethod
    def save_joblib_to_redis(joblib_file_path):
        """
            joblib 로 압축된 pickle file redis write
        """
        with open(joblib_file_path, "rb") as f:
            joblib_data = f.read()

        joblib_key = REDISAI.make_redis_model_key(joblib_file_path, ".pkl")

        # threads = []
        for server_key in server_keys:
            thread = threading.Thread(target=REDISAI._set, args=(server_key, joblib_key, joblib_data))
            thread.start()
        #     threads.append(thread)
        # for thread in threads:
        #     thread.join()

        return joblib_key

    @staticmethod
    def save_3_dbsln_to_redis(dbsln_file_path):
        """
            이상탐지/부하예측 dbsln 3회 dump 된 pickle file redis write
        """
        with open(dbsln_file_path, 'rb') as f:
            training_mode = pickle.load(f)
            biz_status = pickle.load(f)
            biz_status = pickle.dumps(biz_status)
            dbsln_model = pickle.load(f)
            dbsln_model = pickle.dumps(dbsln_model)

        training_mode_key = REDISAI.make_redis_model_key(dbsln_file_path,".pkl")+"_training_mode"
        biz_status_key = REDISAI.make_redis_model_key(dbsln_file_path,".pkl")+"_biz_status"
        dbsln_model_key = REDISAI.make_redis_model_key(dbsln_file_path,".pkl")

        # threads = []
        for server_key in server_keys:
            thread1 = threading.Thread(target=REDISAI._set, args=(server_key, training_mode_key, training_mode))
            thread2 = threading.Thread(target=REDISAI._set, args=(server_key, biz_status_key, biz_status))
            thread3 = threading.Thread(target=REDISAI._set, args=(server_key, dbsln_model_key, dbsln_model))

            thread1.start()
            thread2.start()
            thread3.start()
        #     threads.extend([thread1,thread2,thread3])
        # for thread in threads:
        #     thread.join()

        return training_mode_key, biz_status_key, dbsln_model_key

    @staticmethod
    def save_mem_to_redis(json_key, json_data):
        """
            메모리에 로드된 json 를 redis write
        """
        for key, redisai_client in redisai_clients.items():
            redisai_client.set(json_key, json_data)

        return json_key

    @staticmethod
    def save_body_to_redis(body_key, data):
        """
            event_fcst serving data redis write
        """
        serialized_df = pickle.dumps(data)
        for key, redisai_client in redisai_clients.items():
            res = redisai_client.set(body_key, serialized_df)
        return body_key

    @staticmethod
    def save_log_model_to_redis(model_path):
        """
            pickle file redis write
        """
        model_data = Doc2Vec.load(model_path)
        model_data = pickle.dumps(model_data)
        model_key = REDISAI.make_redis_model_key(model_path, ".model")

        for server_key in server_keys:
            thread = threading.Thread(target=REDISAI._set, args=(server_key, model_key, model_data))
            thread.start()
        return model_key

    ##############
    ###  추 론  ###
    ##############
    @staticmethod
    def get_rejson(key_list, minute, wday):
        values = redisjson_clients[server_keys[0]].jsonmget(rejson.Path(f".{minute}.{wday}"), *[key for key in key_list])
        return values

    @staticmethod
    def inference(model_key, input_data, data_type='float'):
        """
            input_data: serving data

            input_name : input_data의 unique id
            ex) {algo}_input_{feat}
            SeqAttn_input_tps
            SeqAttn_input_response_time
            ...
            S2S_Attn_input_tps
            S@S_Attn_input_response_time

            output_name : 모델 추론 값의 unique id
            ex) {algo}_output_{feat}
            SeqAttn_output_tps
            SeqAttn_output_response_time
            ...
            S2S_Attn_output_tps
            S@S_Attn_output_response_time
        """
        input_name = f"{model_key}/in"
        output_name = f"{model_key}/out"
        redisai_clients[server_keys[0]].tensorset(input_name, input_data, dtype=data_type)
        redisai_clients[server_keys[0]].modelrun(model_key, inputs=[input_name], outputs=[output_name])
        preds = []
        pred = redisai_clients[server_keys[0]].tensorget(output_name)
        preds.append(pred)

        return preds

    @staticmethod
    def inference_gdn(model_key, input_data, data_type='float'):
        input_name = f"{model_key}/in"
        output_pred = f"{model_key}/out1"
        output_attn = f"{model_key}/out2"
        output_edge = f"{model_key}/out3"

        redisai_clients[server_keys[0]].tensorset(input_name, input_data, dtype="float")
        redisai_clients[server_keys[0]].modelrun(model_key,
                                                 inputs=[input_name],
                                                 outputs=[output_pred,output_attn,output_edge])
        predicate = redisai_clients[server_keys[0]].tensorget(output_pred)
        attention_weight = redisai_clients[server_keys[0]].tensorget(output_attn)
        edge_index = redisai_clients[server_keys[0]].tensorget(output_edge)

        return predicate, attention_weight, edge_index

    @staticmethod
    def inference_digcn(model_key, input_data):
        input_name_1 = f"{model_key}/in_x"
        input_name_2 = f"{model_key}/in_egde_index"
        input_name_3 = f"{model_key}/in_edge_attr"
        input_name_4 = f"{model_key}/in_node_list"
        output_name = f"{model_key}/out"

        redisai_clients[server_keys[0]].tensorset(input_name_1, input_data.x.numpy(), dtype="float")
        redisai_clients[server_keys[0]].tensorset(input_name_2, input_data.edge_index.numpy(), dtype="float")
        redisai_clients[server_keys[0]].tensorset(input_name_3, input_data.edge_attr.numpy(), dtype="float")
        redisai_clients[server_keys[0]].tensorset(input_name_4, input_data.batch.numpy(), dtype="float")

        redisai_clients[server_keys[0]].modelrun(model_key, inputs=[input_name_1, input_name_2, input_name_3, input_name_4], outputs=[output_name])

        pred = redisai_clients[server_keys[0]].tensorget(output_name)

        return pred

    @staticmethod
    def event_cpd_inference(model_key, input_data, x_mark_data, y_mark_data):
        input_name = f"{model_key}/in"
        x_mark_name = f"{model_key}/x_mark"
        y_mark_name = f"{model_key}/y_mark"
        output_name = f"{model_key}/out"

        redisai_clients[server_keys[0]].tensorset(input_name, input_data, dtype="float")
        redisai_clients[server_keys[0]].tensorset(x_mark_name, x_mark_data, dtype="float")
        redisai_clients[server_keys[0]].tensorset(y_mark_name, y_mark_data, dtype="float")

        redisai_clients[server_keys[0]].modelrun(model_key,
                                          inputs=[input_name, x_mark_name, y_mark_name],
                                          outputs=[output_name])
        pred = redisai_clients[server_keys[0]].tensorget(output_name)

        return pred

    @staticmethod
    def event_clf_inference(model_key, input_data):
        input_name = f"{model_key}/in"
        output_name = f"{model_key}/out"

        redisai_clients[server_keys[0]].tensorset(input_name, input_data, dtype="float")
        redisai_clients[server_keys[0]].modelrun(model_key, inputs=input_name, outputs=[f'{output_name}1', f'{output_name}2'])
        pred = redisai_clients[server_keys[0]].tensorget(f'{output_name}1')
        recon = redisai_clients[server_keys[0]].tensorget(f'{output_name}2')

        return pred, recon

    @staticmethod
    def inference_pickle(model_key):
        pickled_data = redisai_clients[server_keys[0]].get(model_key)
        model_object = pickle.loads(pickled_data)
        return model_object

    @staticmethod
    def inference_json(model_key):
        json_data = redisai_clients[server_keys[0]].get(model_key)
        model_object = json.loads(json_data)
        return model_object

    @staticmethod
    def inference_joblib(model_key):
        json_data = redisai_clients[server_keys[0]].get(model_key)
        buffer = BytesIO(json_data)
        model_object = joblib.load(buffer)
        return model_object

    @staticmethod
    def inference_log_model(model_key):
        pickled_data = redisai_clients[server_keys[0]].get(model_key)
        model_object = pickle.loads(pickled_data)
        return model_object

    @staticmethod
    def get(model_key):
        try:
            object = redisai_clients[server_keys[0]].get(model_key)
            if type(object) is bytes:
                object = object.decode()
            return object
        except:
            raise print("no model key in redis")

    @staticmethod
    def set(key, value):
        if type(value) is dict or list:
            value = json.dumps(value, cls=NumpyEncoder)
        elif type(value) is bool:
            value = int(value)

        for _, redisai_client in redisai_clients.items():
            redisai_client.set(key, value)

    @staticmethod
    def make_redis_model_key(path, suffix=''):
        return path.split("/model/")[1].replace(suffix,"")


class REDIS:
    @staticmethod
    def update_serving_target(module_name, inst_type, target_id):
        key = f"{module_name}_{inst_type}_{target_id}"
        # 현재 서빙 상태 조회
        serve_list = list(REDIS.hgetall('RedisServingTargets::mlc'))
        if key in serve_list:
            return f"{key} is already serving."
        else:
            serving_target = {
                key: {
                    'service_name': key,
                    'module': module_name,
                    'target_id': target_id,
                    'type': inst_type
                }
            }

            REDIS.hset(serving_target)
            return f"{key} is registered in redis (RedisServingTargets::mlc)"

    @staticmethod
    def update_serving_group(module_name, inst_type, target_id, target_info):
        key = f"{module_name}_{inst_type}_{target_id}"
        # 현재 서빙 상태 조회
        serve_list = list(REDIS.hgetall('RedisServingTargets::mlc'))
        if key in serve_list:  # 이미 서빙 중이고, 내부 타겟 업데이트만
            pass
        else:  # 신규 서빙 대상 등록
            serving_target = {
                key: {
                    'service_name': key,
                    'module': module_name,
                    'target_id': target_id,
                    'type': inst_type
                }
            }
            REDIS.hset(serving_target)

        # 내부 타겟 리스트 업데이트
        if module_name == "exem_aiops_load_fcst":
            REDIS.loadfcst_set(target_info)
        elif module_name == "exem_aiops_event_fcst":
            REDIS.eventfcst_set(target_info)

        return f"{key} is registered in redis (RedisServingTargets::mlc, GroupTargetlist)"

    @staticmethod
    def init_serving_targets(key: str = "RedisServingTargets::mlc") -> None:
        """
        서빙 대상 정보를 관리하는 redis hash key "RedisServingTargets::mlc", "Collect::TargetGroups, Collect::LoadFcstTargetList" 를 초기화함
        추후 다른 redis key 운용 예정이라면 파라미터 전달 방식으로 호출해서 key 변수 값 이용

        :param key : 초기화할 redis key
        """
        redis_clients.delete("RedisServingTargets::mlc")
        group_keys = redis_clients.keys("Collect::*")
        if group_keys:
            redis_clients.delete(*group_keys)

    @staticmethod
    def hset(serving_targets: dict):
        """
        서빙 대상 정보를 redis에 hash 타입으로 저장하는 함수

        :param serving_targets: 서빙 대상
        ex) {'exem_aiops_anls_inst_was_3502': {
                "service_name":"exem_aiops_anls_inst_was_102_3502",
                "module":"exem_aiops_anls_inst",
                "target_id":"3502",
                "type":"was"
                },
                ...
            }
        """
        for key, value in serving_targets.items():
            redis_clients.hset('RedisServingTargets::mlc', key, json.dumps(value))

    @staticmethod
    def hdel(key):
        redis_clients.hdel('RedisServingTargets::mlc', key)

    @staticmethod
    def hgetall(key: str) -> dict:
        """
        redis 등록된 서빙 대상 정보를 반환하는 함수

        :param key = redis key name
        :return = redis 등록된 서빙 대상 정보
        """
        hash_data = redis_clients.hgetall(key)
        if hash_data:
            data = {key.decode('utf-8'): value.decode('utf-8') for key, value in hash_data.items()}
            return data
        else:
            return None

    @staticmethod
    def get_key_from_RedisServingTargets(key_pattern):
        all_fields = redis_clients.hkeys('RedisServingTargets::mlc')
        key_list = [field for field in all_fields if key_pattern in field.decode('utf-8')]

        return key_list

    @staticmethod
    def loadfcst_set(serving_targets: dict):
        """
        부하예측(RMC) 서빙 대상 정보를 redis에 String 타입으로 저장하는 함수

        :param serving_targets: 서빙 대상
        ex) {'exem_aiops_load_fcst_was_all': {
                "module":"exem_aiops_load_fcst",
                "target_id":"all",
                "inst_type":"was",
                "target_list": ["1201", "1202", ...,]
                },
                ...
            }
        :return:
        """
        for key, value in serving_targets.items():
            redis_clients.set(
                f"Collect::LoadFcstTargetList:{value['inst_type']}:{value['target_id']}",
                json.dumps(eval(value['target_list'])))

    @staticmethod
    def eventfcst_set(serving_targets: dict):
        """
        이슈예측(group) 서빙 대상 정보를 redis에 String 타입으로 저장하는 함수

        :param serving_targets: 서빙 대상
        ex) {'exem_aiops_event_fcst_instanceGroup_179': {
                "module":"exem_aiops_event_fcst",
                "target_id":"179",
                "inst_type":"instanceGroup",
                "target_list": {"was": ["1201", "1202", ...,] }
                },
                ...
            }
        :return:
        """
        for key, value in serving_targets.items():
            redis_clients.set(
                f"Collect::TargetGroups::{value['inst_type']}:{value['target_id']}:{value['module']}",
                json.dumps(eval(value['target_list'])))

    @staticmethod
    def eventfcst_del(inst_type, target_id, module):
        """
        이슈예측 특정 그룹의 서빙 대상 정보를 제거하는 함수

        :param inst_type: XAIOps group type ex) 'instanceGroup', 'hostGroup'
        :param target_id: 이슈예측 그룹의 target_id ex) '179'
        :param module: ex) 'exem_aiops_event_fcst'
        :return:
        """
        redis_clients.delete(f"Collect::TargetGroups::{inst_type}:{target_id}:{module}")

    @staticmethod
    def loadfcst_del(inst_type, target_id):
        """
        부하예측(RMC)의 서빙 대상 정보를 제거하는 함수

        :param inst_type: XAIOps instance type ex) 'was', 'db', 'os'
        :param target_id: XAIOps target id ex) 'all'

        :return:
        """
        redis_clients.delete(f"Collect::LoadFcstTargetList:{inst_type}:{target_id}")

    @staticmethod
    def loadfcst_target_remove(inst_type, target_id):
        """
        부하예측(RMC)의 서빙 대상 정보(타겟)를 제거하는 함수

        :param inst_type: XAIOps instance type ex) 'was', 'db', 'os'
        :param target_id: XAIOps target id ex) '1201'
        :return:
        """
        key_list = redis_clients.keys(f"Collect::LoadFcstTargetList:*")
        loadfcst_keylist = [key.decode('utf-8') for key in key_list]
        for redis_key in loadfcst_keylist:
            if inst_type in redis_key:
                value = redis_clients.get(redis_key)
                if value:
                    target_list = json.loads(value.decode('utf-8'))
                    if target_id in target_list:
                        target_list.remove(target_id)
                        redis_clients.set(redis_key, json.dumps(target_list))

    @staticmethod
    def eventfcst_target_remove(inst_type, target_id):
        """
        이슈예측 특정 그룹의 서빙 대상 정보(타겟)를 제거하는 함수

        :param inst_type: XAIOps instance type ex) 'was', 'db', 'os'
        :param target_id: XAIOps target id ex) '1201'
        :return:
        """
        key_list = redis_clients.keys(f"Collect::TargetGroups::*")
        eventfcst_keylist = [key.decode('utf-8') for key in key_list]

        for key in eventfcst_keylist:
            value = redis_clients.get(key)
            if value:
                target_dict = json.loads(value.decode('utf-8'))
                if inst_type in target_dict:
                    target_list = target_dict[inst_type]
                    if target_id in target_list:
                        target_list.remove(target_id)
                        target_dict[inst_type] = target_list
                        redis_clients.set(key, json.dumps(target_dict))

def model_needs_update(path, model_key, reload=False):
    if reload:
        return True
    if any(redisai_clients[server_key].exists(model_key) == 0 for server_key in server_keys):
        return True
    else:
        redisai_model_info = redisai_clients[server_keys[0]].modelget(model_key)
        directory_model_timestamp = os.path.getmtime(path)
        redisai_model_timestamp = redisai_model_info['tag']
        if str(directory_model_timestamp) != redisai_model_timestamp:
            return True
    return False

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)
