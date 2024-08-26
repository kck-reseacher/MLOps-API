import os
import re
import multiprocessing
from pathlib import Path

from common.redisai import REDISAI
from common.system_util import SystemUtil
from common.constants import SystemConstants as sc
from resources.logger_manager import Logger


class ModelManager:

    @staticmethod
    def get_server_run_configuration():
        # get environment_variable (AIMODULE_HOME, AIMODULE_PATH)
        os_env = SystemUtil.get_environment_variable()
        model_path = Path(os_env[sc.AIMODULE_HOME]) / "model"

        return model_path

    @staticmethod
    def get_logger():
        os_env = SystemUtil.get_environment_variable()
        error_log_dict = dict()
        error_log_dict["log_dir"] = str(Path(os_env[sc.AIMODULE_LOG_PATH]) / 'modelmanager')
        error_log_dict["file_name"] = 'error'
        logger = Logger().get_default_logger(logdir=os_env[sc.AIMODULE_LOG_PATH] + f"/modelmanager", service_name='modelmanager',
                                             error_log_dict=error_log_dict)
        return logger, os_env[sc.MLOPS_SERVER_ENV]

    @staticmethod
    def load_model(path=None, reload=False):
        '''

        Parameters
        ----------
        path 특정 경로의 파일
        파일 분류
            onnx: onnx model file
            json: model config file
			normal_pickle: anls_inst 다른 알고리즘 pickle파일 & anls_service /dbsln
			dbsln_pickle: anls_inst /dbsln (3중 pickle file)
			joblib_pickle: anls_inst /seq2seq /seqattn
			trash: 과거 dbsln feature 별 pickle파일 & backup파일 & lock파일 & h5파일 & anls_inst 타 알고리즘 pickle파일
        '''

        logger, mlops_server_env = ModelManager.get_logger()
        if path is None:
            model_path = ModelManager.get_server_run_configuration()
        else:
            model_path = path
        logger.info("[============== Start Redis ModelStore ==============]")
        if not os.path.exists(model_path):
            raise Exception("invalid model path")
        if mlops_server_env == sc.MASTER:
            for root, _, files in os.walk(model_path):
                for file in files:
                    if re.search('/backup|/chat', root) or file.endswith('.lock') or file.endswith('.h5'):
                        logger.debug(f'[SKIP] trash - {os.path.join(root, file)}')
                    elif file.endswith('.json'):
                        REDISAI.save_json_to_redis(os.path.join(root, file))
                        logger.info(f'[DONE] json - {os.path.join(root, file)}')
                    elif file.endswith('.onnx'):
                        REDISAI.save_onnx_to_redis(os.path.join(root, file), reload)
                        logger.info(f'[DONE] onnx - {os.path.join(root, file)}')
                    elif file.endswith('.pkl'):
                        if re.search('/exem_aiops_anls_service', root):
                            if file == 'train_result.pkl':
                                REDISAI.save_pickle_to_redis(os.path.join(root, file))
                            logger.info(f'[DONE] normal pickle - {os.path.join(root, file)}')
                        elif re.search('/exem_aiops_anls_log', root):
                            if re.search('dbsln', root):
                                logger.info(f'[SKIP] old file - {os.path.join(root, file)}')
                            else:
                                REDISAI.save_joblib_to_redis(os.path.join(root, file))
                                logger.info(f'[DONE] joblib pickle - {os.path.join(root, file)}')
                        elif re.search('/exem_aiops_event_fcst', root):
                            if re.search('/mean_std|/scalers', root):
                                REDISAI.save_joblib_to_redis(os.path.join(root, file))
                                logger.info(f'[DONE] joblib pickle - {os.path.join(root, file)}')
                            else:
                                REDISAI.save_pickle_to_redis(os.path.join(root, file))
                                logger.info(f'[DONE] normal pickle - {os.path.join(root, file)}')
                        elif re.search('/exem_aiops_load_fcst', root):
                            res = REDISAI.save_joblib_to_redis(os.path.join(root, file))
                            logger.info(f'[DONE] joblib pickle - {res}')
                        elif re.search('/exem_aiops_fcst_tsmixer', root):
                            res = REDISAI.save_joblib_to_redis(os.path.join(root, file))
                            logger.info(f'[DONE] joblib pickle - {res}')
                        elif (re.search('/exem_aiops_anls_inst', root) or re.search('/exem_aiops_fcst', root)):
                            if re.search('/dbsln', root):
                                try:
                                    REDISAI.save_3_dbsln_to_redis(os.path.join(root, file))
                                    logger.info(f'[DONE] dbsln pickle - {os.path.join(root, file)}')
                                except Exception as e: # 미적용
                                    logger.info(f'[SKIP] old file - {os.path.join(root, file)}')
                            elif re.search('/seqattn|/seq2seq', root):
                                REDISAI.save_joblib_to_redis(os.path.join(root, file))
                                logger.info(f'[DONE] joblib pickle - {os.path.join(root, file)}')
                            elif re.search('/gdn', root):
                                REDISAI.save_joblib_to_redis(os.path.join(root, file))
                                logger.info(f'[DONE] joblib pickle - {os.path.join(root, file)}')
                            elif re.search('/tsmixer', root):
                                REDISAI.save_joblib_to_redis(os.path.join(root, file))
                                logger.info(f'[DONE] joblib pickle - {os.path.join(root, file)}')
                            elif re.search('/gru|/lstm|/tadgan|/gam|/rae|/dnn', root):
                                logger.debug(f'[SKIP] trash - {os.path.join(root, file)}')
                                pass
                            else:
                                logger.debug(f'[SKIP] trash - {os.path.join(root, file)}')
                        else:
                            logger.debug(f'[SKIP] trash - {os.path.join(root, file)}')
                    elif file.endswith('.model'):
                        REDISAI.save_log_model_to_redis(os.path.join(root, file))
                        logger.info(f'[DONE] json - {os.path.join(root, file)}')
                    else:
                        logger.debug(f'[SKIP] trash - {os.path.join(root, file)}')

            for root, _, files in os.walk(model_path):
                if re.search('/exem_aiops_anls_service', root):
                    files = os.listdir(os.path.join(root))
                    pkl_files = [file for file in files if file.startswith("dbsln") and file.endswith(".pkl")]
                    cores = round(multiprocessing.cpu_count() * 0.9)
                    chunk_size = len(pkl_files) // cores + 1
                    chunks = [pkl_files[i:i + chunk_size] for i in range(0, len(pkl_files), chunk_size)]
                    processes = []
                    for chunk in chunks:
                        process = multiprocessing.Process(target=REDISAI.save_service_to_redis,
                                                          args=(logger, root, chunk, reload,))
                        processes.append(process)
                        process.start()
                    for process in processes:
                        process.join()
        logger.info("[============== End Redis ModelStore ==============]")