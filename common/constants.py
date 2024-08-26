####################### 공통 #######################
INPUT_DATE_FORMAT = "%Y-%m-%d"
INPUT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

INPUT_DATE_YMD = "%Y%m%d"
INPUT_DATE_YMDHMS = "%Y%m%d%H%M%S"

# 분석 inst_type
INST_TYPE_E2E = "e2e"
INST_TYPE_2TIER = "2-tier"
INST_TYPE_DB = "db"
INST_TYPE_WAS = "was"
INST_TYPE_OS = "os"
INST_TYPE_TXN = "txn"
INST_TYPE_CODE = "code"
INST_TYPE_SERVICE = "service"

# 이상탐지 알고리즘
ANOMALY_TYPE_DBSLN = "dbsln"
ANOMALY_TYPE_RAE = "rae"

# 알고리즘 네이밍
MODEL_S_DBSLN = "dbsln"
MODEL_S_FBSLN = "fbsln"
MODEL_S_DNN = "dnn"
MODEL_S_RAE = "rae"
MODEL_S_S2S = "seq2seq"
MODEL_S_SEQATTN = 'seqattn'
MODEL_S_LSTM = "lstm"
MODEL_S_GRU = "gru"
MODEL_S_GAM = "gam"
MODEL_S_LOGSEQ = 'logseq'
MODEL_S_DIGCN = 'digcn'
MODEL_S_SPARSELOG = 'sparselog'
MODEL_S_ABNORMAL_CLUSTERING = "kmeans"
MODEL_S_TADGAN = 'tadgan'
MODEL_S_NSFORMERS = 'nsformers'
MODEL_S_LOADFCST = "load_forecast"
MODEL_S_GDN = "gdn"
MODEL_S_TSMIXER = "tsmixer"

# 이상탐지 / 부하예측에 사용되는 알고리즘 리스트
ANOMALY_TYPE_ALGO_LIST = [MODEL_S_DBSLN, MODEL_S_GDN, MODEL_S_SEQATTN]

# XAIOps 전체에서 사용하는 알고리즘 리스트
TOTAL_ALGO_LIST = [MODEL_S_DBSLN, MODEL_S_RAE, MODEL_S_FBSLN,
                   MODEL_S_SEQATTN, MODEL_S_S2S, MODEL_S_LSTM, MODEL_S_GRU, MODEL_S_GAM, MODEL_S_TADGAN, MODEL_S_TSMIXER] # MODEL_S_DNN

# 서빙 서버로 기동되는 모듈명 리스트 (모델파일 동기화)
EXEM_AIOPS_ANLS_SYS = 'exem_aiops_anls_sys'
EXEM_AIOPS_ANLS_INST = 'exem_aiops_anls_inst'
EXEM_AIOPS_LOAD_FCST = 'exem_aiops_load_fcst'
EXEM_AIOPS_EVENT_FCST = 'exem_aiops_event_fcst'
EXEM_AIOPS_ANLS_LOG = 'exem_aiops_anls_log'
EXEM_AIOPS_ANLS_SERVICE = 'exem_aiops_anls_service'
EXEM_AIOPS_FCST_TSMIXER = 'exem_aiops_fcst_tsmixer'

SERVING_MUDULE_LIST = [EXEM_AIOPS_ANLS_SYS, EXEM_AIOPS_ANLS_INST,
                       EXEM_AIOPS_EVENT_FCST, EXEM_AIOPS_ANLS_LOG, EXEM_AIOPS_ANLS_SERVICE, EXEM_AIOPS_FCST_TSMIXER]

REQUIRE_SERVICE_API_MODULE_LIST = [EXEM_AIOPS_ANLS_INST, EXEM_AIOPS_ANLS_LOG]

# 변경된 학습데이터 구조 적용 모듈 (single target 모듈)
TRAINING_MODULE_LIST = [EXEM_AIOPS_ANLS_INST, EXEM_AIOPS_ANLS_LOG, EXEM_AIOPS_ANLS_SERVICE, EXEM_AIOPS_FCST_TSMIXER]

# multi target 일반화 모듈
MULTI_TARGET_TRAINING_MODULE_LIST = [EXEM_AIOPS_LOAD_FCST]

# 분석 모듈 리스트
ANALYZER_MODULE_LIST = ['exem_aiops_lngtrm_fcst', 'exem_aiops_future_fcst', 'exem_aiops_wclst',
                       'exem_aiops_correlation', 'exem_aiops_causality', 'exem_aiops_event_pattern']

# 알고리즘별 모듈명, 클래스명 정보 저장 (inst_multi.py에서 loading 할 때 사용)
ALGO_MODULE_CLASS_NAME = {
    MODEL_S_DBSLN  : {'module_name' : 'dynamic_baseline',
                      'class_name' : 'DynamicBaseline'},
    MODEL_S_DNN: {'module_name' : 'dnn',
                      'class_name' : 'DNNRegressor'},
    MODEL_S_RAE : {'module_name' : 'robust_autoencoder',
                      'class_name' : 'RAEAnomalyDetection'},
    MODEL_S_S2S: {'module_name' : 's2s_attn_forecast',
                      'class_name' : 'S2SAttnForecast'},
    MODEL_S_LSTM : {'module_name' : 'lstm',
                      'class_name' : 'LSTM'},
    MODEL_S_GRU : {'module_name' : 'gru',
                      'class_name' : 'GRU'},
    MODEL_S_GAM : {'module_name' : 'gam',
                      'class_name' : 'GAM'},
    MODEL_S_SEQATTN : {'module_name' : 's2s_attn_detect',
                      'class_name' : 'S2SAttnDetect'},
    MODEL_S_TADGAN: {'module_name': 'tadgan_anomaly_detector',
                     'class_name': 'TadGANAnomalyDetection'},
    MODEL_S_LOADFCST: {'module_name': 'load_forecast',
                       'class_name': 'LoadForecast'},
    MODEL_S_GDN: {'module_name': 'graph_detection_network',
                  'class_name': 'GraphDetectionNetwork'},
    MODEL_S_TSMIXER: {'module_name': 'tsmixer',
                  'class_name': 'TSMixer'}
}
MODEL_B_DBSLN = "DBSLN"
MODEL_B_DNN = "DNN"
MODEL_B_RAE = "RAE"
MODEL_B_S2S = "SEQ2SEQ"
MODEL_B_SEQATTN = 'SEQATTN'
MODEL_B_LSTM = "LSTM"
MODEL_B_GRU = "GRU"
MODEL_B_GAM = "GAM"
MODEL_B_LOGSEQ = "LOGSEQ"
MODEL_B_TADGAN = "TADGAN"
MODEL_B_TSMIXER = "TSMIXER"

MODEL_F_DBSLN = "Dynamic Baseline"
MODEL_F_DNN = "Deep Neural Network"
MODEL_F_RAE = "Robust AutoEncoder"
MODEL_F_S2S = "Sequence-to-Sequence"
MODEL_F_LSTM = "Long Short-Term Memory"
MODEL_F_GRU = "Gated Recurrent Units"
MODEL_F_GAM = "Generalized Additive Model"
MODEL_F_LOGSEQ = "Log Sequence"
MODEL_F_TADGAN = "Time Series Anomaly Detection with Generative Adversarial Networks"
MODEL_F_DBSLN_XCODE = "dynamic baseline(xcode)"
MODEL_F_DBSLN_FOR_SERVICE = "dynamic baseline for service"
MODEL_F_TSMIXER = "tsmixer"

####################### 학습/분석/서빙 #######################
# 이상탐지 알고리즘 사용 여부
USE_SEQATTN = True
USE_GDN = True

# 학습 모드
TRAINING_MODE_INIT = -2  # 초기값
TRAINING_MODE_ERROR = -1  # 데이터의 일수가 부족해서 트레이닝 모드 설정 불가
TRAINING_MODE_DAILY = 0  # 요일을 구분하지 않고 하루 단위로 통계 계산 (최소 3일 이상의 학습 데이터 필요)
TRAINING_MODE_WORKINGDAY = 1  # 요일은 구분하지 않지만, 주중과 주말은 따로 집계 (최소 1주 이상의 학습 데이터 필요)
TRAINING_MODE_WEEKDAY = 2  # 요일을 구분해서 요일 별로 따로 통계 계산 (최소 2주 이상의 학습 데이터 필요)
TRAINING_MODE_BIZDAY = 3  # 비즈니스 캘린더를 감안한 계산 (최소 2개월 이상의 학습 데이터 필요)

# 각 학습 모드에 따른 요일 맵
TRAINING_WDAY_MAP = {
    TRAINING_MODE_DAILY: [0, 0, 0, 0, 0, 0, 0],
    TRAINING_MODE_WORKINGDAY: [0, 0, 0, 0, 0, 5, 5],
    TRAINING_MODE_WEEKDAY: [0, 1, 2, 3, 4, 5, 6],
    TRAINING_MODE_BIZDAY: [0, 1, 2, 3, 4, 5, 6],
}

# 비즈니스데이 전체 학습 결과 정리
NO_BIZDAY_TRAINED = 0  # 학습된 비즈니스 데이가 없는 경우
ANY_BIZDAY_TRAINED = 1  # 학습된 비즈니스데이가 있는 경우
INSUFFICIENT_DATA_TO_TRAIN_BIZDAY = 2  # 비즈니스데이 학습모드가 요구하는 데이터 양보다 적은 경우

# 개별 비즈니스데이 학습 결과 정리
BIZDAY_TRAINED = 1  # 학습 완료된 비즈니스데이
BIZDAY_LESS_THAN_TWO_DAYS = 0  # 이틀 미만이어서 학습되지 않은 비즈니스데이
BIZDAY_NOT_IN_DATA = -1  # 학습 데이터에 존재하지 않는 비즈니스 데이

# 기본 상수 정의
DBSLN_WDAY_MAX = 7  # 요일에 대한 최대 값
DBSLN_DMIN_MAX = 1440  # 분으로 표시한 하루의 시간 최대 값

# 계산 설정 값
DBSLN_N_WINDOW = 10  # Moving Average 계산할 때의 분 단위 구간
OUTLIER_N_WINDOW = 20  # Outlier 처리시 분 단위

# Outlier 탐지시 설정 값
SIGMA = 1.5  # dbsln, dnn Outlier 탐지 관련 parameter
FBSLN_SIGMA = 3.0  # fbsln Outlier 탐지 관련 parameter
LOAD_PRED_SIGMA = 2.0  # LSTM, seq2seq, GRU Outlier 탐지 관련 parameter

# UI에서는 upper 이상인 경우엔 무조건 이상으로 그리기 때문에 맞추기 위해서 0.0 -> 0.1로 변경.
DBSLN_CHECK_MIN = 0.1

# 부하예측
FCST_TIME_INTERVAL = [1, 5, 10, 20, 30]  # 1분, 5분, 10분, 20분, 30분

# 이벤트 예측 DB
DB_KEY_MAPPING = {
    'T': 'TIBERO',
    'P': 'POSTGRES',
    'Y': 'MYSQL'
}

# e2e, was_txn 분석
COMPARE_BEFORE_DAYS = 7
TXN_TOP_N = 100
TEMP_FILE_WAIT_TIME = 1

# GAM 학습 파라미터
# t distribution value based on confidence level
gam_band_width = {
    1: 1.64, # 0.95,
    2: 3.09, # 0.999,
    3: 4.77, # 0.999999,
    4: 10,  # 0.9999999999999999,
    5: 14 # inf
    }

# degree of freedom
gam_band_complexity = {
    1: 24,
    2: 120,
    3: 160,
    4: 260,
    5: 360
    }

FAIL_TYPE_TOTAL = "total"
FAIL_TYPE_TOP_TXN = "top"
FAIL_TYPE_ETC_TXN = "etc"

# AutoEncoder
AUTOENCODER_ANOMALY_THRESHOLD = 99  # [10, 20, 30 ... 90, 91, 92, ... 99]
AUTOENCODER_ANOMALY_JSON_FILENAME = "auto_encoder_config.pkl"
ROBUST_AUTOENCODER_ANOMALY_JSON_FILENAME = "robust_auto_encoder_config.pkl"

# 이벤트 예측
THRESHOLD_AUTO_CALC_DATA_MONTH = 1  # 단위 : 월(month)
THRESHOLD_AUTO_CALC_PERIOD = 7  # 단위 : 일(day)

# 유사 이벤트 패턴 분석 타입
ANLS_TYPE_FAILURE = "anls_sys"
ANLS_TYPE_PRIDICT = "predict"

# 유사 이벤트 패턴 분석 알고리즘
COSINE_SIMILARITY = "cosine"
INTERSECTIONRATE = "intersection"

# 모델 경로
PRE_MODEL_PATH = "prev"
NEW_MODEL_PATH = "new"

# 배포 정책
DEPLOY_AUTO_LATEST = 0  # 0(Default): 항상 최신 자동 업데이트
DEPLOY_AUTO_PERF = 1  # 1: 성능 비교 자동 업데이트
DEPLOY_USER = 2  # 2: 사용자 선택 배포

# 수동 배포 정책
DEPLOY_USER_PREV = 0  # 이전 모델 선택
DEPLOY_USER_NEW = 1  # 신규 모델 선택

# 로그이상탐지 학습 metric value
MSG = "msg"

# 로그이상탐지 LOGSEQ 기본 window_size
LOGSEQ_N_WINDOW = 30
DEFAULT_N_TOP_K = 5

# 로그이상탐지 tok_k values
LOGSEQ_TOP_K_VALUES = [1, 3, 5, 10, 20]

# 이상탐지 res key prefix
ANOMALY_RES_KEY_PREFIX = "detect_"

# 학습 module status
PROCESS_TRAIN_DATA = "process train data"
PROGRESS = "progress"
DURATION_TIME = "duration_time"

class SystemConstants:
    # os 환경 변수
    AIMODULE_HOME = "AIMODULE_HOME"
    AIMODULE_LOG_PATH = "AIMODULE_LOG_PATH"
    AIMODULE_PATH = "AIMODULE_PATH"
    AIMODULE_SERVER_ENV = "AIMODULE_SERVER_ENV"
    AIMODULE_LOGGER_ENV = "AIMODULE_LOGGER_ENV"
    MLOPS_SERVER_ENV = "MLOPS_SERVER_ENV"
    GPU_MIG = "GPU_MIG"

    # module process
    SERVING = "serving"
    TRAIN = "train"

    # config 파일 path
    CONFIG_FILE_PATH = "/resources/config/"

    # config.json configKey
    POSTGRES = "postgres"
    API_SERVER = "api_server"
    MODULE_API_SERVER = "module_api_server"
    SERVING_FLASK = "serving_flask"

    # env 별 config 파일 이름 prefix, suffix
    CONFIG_FILE_PREFIX = "config-"
    CONFIG_FILE_SUFFIX = ".json"

    # logger 설정 파일 path
    LOGGER_FILE_PATH = "/resources/logger/"

    # env 별 logger 파일 이름 prefix, suffix
    LOGGER_FILE_PREFIX = "logger-"
    LOGGER_FILE_SUFFIX = ".json"

    # error log default path
    ERROR_LOG_DEFAULT_PATH = "module_error"

    # MULTI ANALYZER
    EXEM_AIOPS_ANLS_INST_MULTI = "exem_aiops_anls_inst_multi"
    EXEM_AIOPS_ANLS_LOG_MULTI = "exem_aiops_anls_log_multi"
    EXEM_AIOPS_EVENT_FCST_MULTI = "exem_aiops_event_fcst_multi"
    EXEM_AIOPS_LOAD_FCST_MULTI = "exem_aiops_load_fcst_multi"
    EXEM_AIOPS_FCST_TSMIXER_MULTI = "exem_aiops_fcst_tsmixer_multi"

    # uvicorn logger config file name
    UVICORN_LOGGER_CONFIG_FILE = "uvicorn_logger.json"

    # server env
    SERVER_ENV_LOCAL = "local"
    SERVER_ENV_DEV = "dev"
    SERVER_ENV_PROD = "prod"
    MASTER = "master"
    SLAVE = "slave"


class MLControllerConstants:
    # 서빙 모듈별 사용할 포트 대역
    PORT_MAPPING_RULE = {
        "exem_aiops_anls_inst": list(range(19701, 19800)),
        "exem_aiops_anls_log": list(range(19800, 19900)),
        "exem_aiops_event_fcst": list(range(19400, 19500)),
        "exem_aiops_anls_service": list(range(19501, 19700)),
        "exem_aiops_fcst_tsmixer": list(range(19901, 20000)),
        "multi": 19000,
        "nginx": 17777
    }

    # 서빙 모듈별 생명주기 방식 (B.E rule)
    DMMP = ["exem_aiops_anls_log"]
    MULTI = ["exem_aiops_anls_inst", "exem_aiops_anls_service", "exem_aiops_event_fcst", "exem_aiops_fcst_txmixer"]

    # MLC 최초 부팅 플래그
    ON_BOOT_FLAG = {"multiworker": False,
                    "multiport": False}

    # 서빙중인 타겟 정보
    SERVING_INFO = {}
    # default_params
    default_params = {
        "exem_aiops_anls_inst_multi": {
            "trained_module": "exem_aiops_anls_inst",
            "type_list": ["tp", "was", "os", "code", "db", "web", "network"],
            "target_info": {
              "tp": [],
              "was": [],
              "os": [],
              "code": [],
              "db": [],
              "web": [],
              "network": []
            }
        },
        "exem_aiops_event_fcst_multi": {
            "trained_module": "exem_aiops_event_fcst",
            "type_list": ["instanceGroup", "hostGroup", "codeGroup"],
            "target_info": {
                "instanceGroup": [],
                "hostGroup": [],
                "codeGroup": []
            }
        },
        "exem_aiops_anls_service_multi": {
            "trained_module": "exem_aiops_anls_service",
            "type_list": ["service"],
            "target_info": {
              "service": []
            }
        },
        "exem_aiops_anls_log_multi": {
            "trained_module": "exem_aiops_anls_log",
            "type_list": ["log"],
            "target_info": {
                "log": []
            }
        },
        "exem_aiops_load_fcst_multi": {
            "trained_module": "exem_aiops_load_fcst",
            "type_list": ["was", "db", "os", "web", "tp", "network", "service"],
            "target_info": {"was": [],
                            "os": [],
                            "db": [],
                            "tp": [],
                            "web": [],
                            "network": [],
                            "service": []}
        },
        "exem_aiops_fcst_tsmixer_multi": {
            "trained_module": "exem_aiops_fcst_tsmixer",
            "type_list": ["was", "db", "os", "web", "tp", "network", "service"],
            "target_info": {"was": [],
                            "os": [],
                            "db": [],
                            "tp": [],
                            "web": [],
                            "network": [],
                            "service": []
                            }
        }
    }

    # ML Controller Logger
    MLC = "mlc"
    LOGGER_FILE_NAME = "controller"
