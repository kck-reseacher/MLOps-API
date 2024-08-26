import json
import subprocess
from copy import deepcopy

import numpy as np
import pandas as pd
import psycopg2 as pg2
import psycopg2.extras
from enum import Enum

import algorithms.logseq.config.default_regex as basereg
from common.base64_util import Base64Util
from common.constants import MLControllerConstants as mc
from common.constants import SystemConstants as sc
from common.system_util import SystemUtil
from resources.config_manager import Config


class RunUtils:
    # <-status 리턴해주는 메서드 "/mlc/serving/status" ->
    @staticmethod
    def get_server_run_configuration():
        # get environment_variable (AIMODULE_HOME, AIMODULE_PATH)
        os_env = SystemUtil.get_environment_variable()
        py_config = Config(os_env[sc.AIMODULE_PATH], os_env[sc.AIMODULE_SERVER_ENV]).get_config()

        return os_env[sc.AIMODULE_PATH], py_config, os_env[sc.AIMODULE_LOG_PATH]


class ServingModule(str, Enum):
    exem_aiops_anls_inst = "exem_aiops_anls_inst"
    exem_aiops_anls_service = "exem_aiops_anls_service"
    exem_aiops_load_fcst = "exem_aiops_load_fcst"
    exem_aiops_event_fcst = "exem_aiops_event_fcst"
    exem_aiops_fcst_tsmixer = "exem_aiops_fcst_tsmixer"


class LogServingModule(str, Enum):
    exem_aiops_anls_log = "exem_aiops_anls_log"


class InstanceType(str, Enum):
    was = "was"
    db = "db"
    os = "os"
    service = "service"
    web = "web"
    tp = "tp"
    network = "network"
    instanceGroup = "instanceGroup"
    hostGroup = "hostGroup"

class InitAPI:
    db_conn_str = None
    module_port_info = None
    serving_proc_count = None
    port_mapping_rule = None

    def __init__(self):
        self.db_conn_str = self.get_database_connection()

    @staticmethod
    def get_database_connection():
        py_path, py_config, log_path = RunUtils.get_server_run_configuration()

        try:
            pg_decode_config = Base64Util.get_config_decode_value(py_config[sc.POSTGRES])
        except Exception as e:
            print('base64 decode error, config: ' + str(py_config[sc.POSTGRES]))
            pg_decode_config = py_config[sc.POSTGRES]

        db_conn_str = (
            f"host={pg_decode_config['host']} "
            f"port={pg_decode_config['port']} "
            f"dbname={pg_decode_config['database']} "
            f"user={pg_decode_config['id']} "
            f"password={pg_decode_config['password']}"
        )

        return db_conn_str

    def _execute_query(self, query, logger):
        conn = None
        cursor = None
        df = None

        try:
            with pg2.connect(self.db_conn_str) as conn:
                with conn.cursor(cursor_factory=pg2.extras.DictCursor) as cursor:
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    column_names = [desc[0] for desc in cursor.description]
                    df = pd.DataFrame(rows, columns=column_names)
        except Exception as exception:
            logger.info(f"Exception: {exception}")
        return df

    def get_preset_from_pg(self, target_id):
        conn, cursor = None, None
        regex_list, delimiters = [], " "
        try:
            conn = pg2.connect(self.db_conn_str)
            cursor = conn.cursor(cursor_factory=pg2.extras.RealDictCursor)

            query = "select re.regset_id, re.delimiter, re.regex, re.replace_str " \
                    "from ai_config_log_regex re left join xaiops_config_log xl " \
                    "on re.regset_id = xl.regset_id " \
                    "where xl.target_id = %s"
            cursor.execute(query, (target_id,))
            query_result = [dict(record) for record in cursor]
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
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return regex_list, delimiters


def make_log_serving_response(log_df: pd.DataFrame, slog_df: pd.DataFrame) -> dict:
    """
    :param log_df: 로그예측 관련 테이블 조회 결과 dataframe
    :param slog_df: 희소로그 관련 테이블 조회 결과 dataframe
    :return: 가공된 사전
    """
    record1 = log_df
    record2 = slog_df

    info = {
            "targetId": record1["target_id"].values[0],
            "digcn": {
                "threshold": json.loads(record1["recommend_param"].values[0] if record1["is_params_auto"].values[0] == True else record1["params"].values[0]),
                "use": record1["is_service_on"].values[0],
                "preset_id": record1["regset_id"].values[0] if record1["regset_id"].isna().values[0] == False else None
            },
            "sparselog": {
                "rare_rate": record2["rare_rate"].values[0] / 100,
                "use": record2["is_service_on"].values[0],
                "alert_threshold": record2["alert_threshold"].values[0],
                "include_keyword": [keyword for keyword, keyword_type in zip(record2['keyword'].values, record2["keyword_type"].values) if keyword_type == "include"],
                "exclude_keyword": [keyword for keyword, keyword_type in zip(record2['keyword'].values, record2["keyword_type"].values) if keyword_type == "exclude"]
            }
        }

    return info
