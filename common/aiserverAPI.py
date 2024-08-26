import json
import sys

import requests

from common import constants


class ServerAPI:
    def __init__(self, config, logger):
        """
        서버와 api 통신을 하기 위한 클래스

        설정 및 데이터 이동 방식
            - 대시보드 UI -> 백엔드 서버 -> 모델링 모듈
        사용자 화면에서 관련 설정을 변경 할 경우 모델링 모듈에서 변경된 설정을 가져옴.

        Parameters
        ----------
        config : 설정
        logger : 로그
        """

        self.config = config
        self.logger = logger

        self.servingServerURL = f"http://{self.config['serving_server']['host']}:{self.config['serving_server']['port']}"

        # 배포 후 학습전 기존 model_config에 host로 저장된 정보 사용을 위해 분기 처리
        if self.config['api_server'] is None:
            self.serverURL = f"http://{self.config['host']}:{self.config['ports']['dashboard']}"
            self.adhocURL = f"http://{self.config['host']}:{self.config['ports']['adhoc']}"

        # adhoc 은 따로 구분없이 사용해도 된다고 확인
        else:
            self.serverURL = f"http://{self.config['api_server']['host']}:{self.config['api_server']['port']}"
            self.adhocURL = f"http://{self.config['api_server']['host']}:{self.config['api_server']['port']}"

    def _request_post(self, url, data, headers=None):
        response = None
        try:
            if headers:
                response = requests.post(url=url, data=data, headers=headers, timeout=10)
            else:
                response = requests.post(url=url, data=data, timeout=10)
        except requests.exceptions.Timeout:
            self.logger.error(f"Request Time Out : {url}")
        except Exception as e:
            self.logger.error(f"{e}")

        return response

    def get_service_parameter(self, sys_id, module_name: str, inst_type, target_id):
        params = {'sysId': sys_id}
        if module_name in str(constants.REQUIRE_SERVICE_API_MODULE_LIST):
            url = (f"{self.servingServerURL}/serving/{sys_id}/log-serving-info")
            try:
                response = requests.get(url, params=params)
            except Exception as e:
                self.logger.exception(f"{e}")
                self.logger.error(f"API server invalid.. {module_name} module service api required.. server down..")
                sys.exit(1)

            if response.json().get("data") is None:
                self._logging_error_result(
                    "get_service_parameter", url, response.json().get("error")
                )
                self.logger.error(f"Service API response format invalid.. inquire backend manager.. server down..")
                sys.exit(1)
            else:
                for data in response.json()["data"]:
                    if data['targetId'] == target_id:
                        return data
        else:
            self.logger.info(f"{module_name} module service api not provided")
            return None

    def _logging_error_result(self, func, json_data, response):
        self.logger.debug(func + f" request data : {json_data}")
        self.logger.error(func + f" response data: {response}")
