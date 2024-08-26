import os
import traceback

from common.constants import SystemConstants as sc
from common.base64_util import Base64Util
from peewee import PostgresqlDatabase


class SystemUtil:
    @staticmethod
    def get_environment_variable():
        os_env = dict()
        # AIMODULE_HOME
        home = os.environ.get(sc.AIMODULE_HOME)
        if home is None:
            print("plz export AIMODULE_HOME")
            home = os.path.dirname(os.path.abspath(__file__))
        else:
            os_env[sc.AIMODULE_HOME] = home

        # AIMODULE_LOG_PATH
        log_path = os.environ.get(sc.AIMODULE_LOG_PATH)
        if log_path is None:
            print("plz export AIMODULE_LOG_PATH")
            log_path = os.path.dirname(os.path.abspath(__file__))
        else:
            os_env[sc.AIMODULE_LOG_PATH] = log_path

        # AIMODULE_PATH
        py_path = os.environ.get(sc.AIMODULE_PATH)
        if py_path is None:
            print("plz export AIMODULE_PATH")
            py_path = os.path.dirname(os.path.abspath(__file__))
        else:
            os_env[sc.AIMODULE_PATH] = py_path

        # AIMODULE_SERVER_ENV
        server_env = os.environ.get(sc.AIMODULE_SERVER_ENV)
        if server_env is None:
            print("plz export AIMODULE_SERVER_ENV")
            py_path = os.path.dirname(os.path.abspath(__file__))
        else:
            os_env[sc.AIMODULE_SERVER_ENV] = server_env

        # MLOPS_SERVER_ENV
        mlops_server_env = os.environ.get(sc.MLOPS_SERVER_ENV)
        if mlops_server_env is None:
            print("plz export MLOPS_SERVER_ENV")
        else:
            os_env[sc.MLOPS_SERVER_ENV] = mlops_server_env.lower()

        # GPU_MIG
        gpu_mig = os.environ.get(sc.GPU_MIG)
        if gpu_mig is None:
            print("plz export GPU_MIG")
        else:
            os_env[sc.GPU_MIG] = gpu_mig.lower() == "true" if gpu_mig else False

        return os_env

    @staticmethod
    def get_orm_db_conn(py_config):

        try:
            pg_decode_config = Base64Util.get_config_decode_value(py_config[sc.POSTGRES])
        except Exception:
            tb = traceback.format_exc()
            print(f'base64 decode error: {tb}')
            pg_decode_config = py_config[sc.POSTGRES]

        # PostgreSQL 데이터베이스 연결 설정
        db = PostgresqlDatabase(
            pg_decode_config['database'],
            user=pg_decode_config['id'],
            password=pg_decode_config['password'],
            host=pg_decode_config['host'],
            port=pg_decode_config['port']
        )
        return db