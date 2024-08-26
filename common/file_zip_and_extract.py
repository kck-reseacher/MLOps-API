import pprint
import shutil
import zipfile
import os
from pathlib import Path


class Logger:
    def info(self, text):
        pprint.pprint(text)


class FileZipExtract:
    def __init__(
        self,
        zip_path: Path,
        logger=None,
        prefix: str = "compressed_",
    ):
        """
        여러 폴더를 하나의 파일로 압축 및 해제 하는 모듈

        How to use
        1. ---------- 추천
        with FileZipExtract(zip_path="/your/model/path"):
            what_to_do()

        2. ----------
        file_zip_extract = FileZipExtract(zip_path="/your/model/path")
        try:
            file_zip_extract.zip()
            what_to_do()
        except Exception as e:
            self.logger.info("Exception : {e}")
        finally:
            file_zip_extract.extract()

        Parameters
        ----------
        zip_path : 압축할 파일이나 경로
        logger : 로거 없을 시에 print 출력
        """
        self.prefix = prefix
        self.logger = logger if logger is not None else Logger()

        self.zip_path = Path(zip_path)
        self.learning_server_zip = (
            self.zip_path.parent / f"{self.prefix}{self.zip_path.stem}.zip"
        )
        self.serving_server_zip = (
            self.zip_path.parent / f"{self.prefix}{self.zip_path.stem}_serving_server.zip"
        )
        self.model_bak_path = self.zip_path.parent.parent / "backup"

        if type(zip_path) == str:
            self.zip_path = Path(zip_path)
        if type(self.model_bak_path) == str:
            self.model_bak_path = Path(self.model_bak_path)

        self.logger.info(f"[{type(self).__name__}] zip_path : {self.zip_path}")
        self.logger.info(f"[{type(self).__name__}] target_zip_file : {self.learning_server_zip}")
        self.logger.info(f"[{type(self).__name__}] target_zip_file_serving_server : {self.serving_server_zip}")
        self.logger.info(f"[{type(self).__name__}] model_bak_path : {self.model_bak_path}")

    def zip(self):
        """
        특정 폴더나 파일을 압축함.
        Returns
        -------
        """
        if self.zip_path.is_file():
            with zipfile.ZipFile(self.learning_server_zip, "w") as zip_fd:
                zip_fd.write(self.zip_path)
            # 파일 삭제
            self.zip_path.unlink()
        else:
            # zip_path 아래의 모들 파일을 리스트로 가져옴
            zip_path_list = list(self.zip_path.glob("**/*"))
            with zipfile.ZipFile(self.learning_server_zip, "w") as zip_fd:
                for path_itr in zip_path_list:
                    zip_fd.write(path_itr)
            # 폴더 삭제
            if os.path.isdir(self.zip_path):
                shutil.rmtree(self.zip_path)

    def extract(self):
        """
        압축 파일의 압축 해제
        Returns
        -------

        """
        if os.path.isdir(self.zip_path):
            shutil.rmtree(self.zip_path)

        self.zip_path.mkdir(exist_ok=True, parents=True)

        # 압축 파일 내부의 모델 파일 명을 서빙 서버에 맞게 수정
        # 학습 서버와 서빙 서버의 model 절대경로가 다를 수 있기 때문
        with zipfile.ZipFile(self.learning_server_zip, 'r') as learning_server_zip, \
            zipfile.ZipFile(self.serving_server_zip , 'w') as serving_server_zip:
            path_name_mapper = zip(learning_server_zip.infolist(), learning_server_zip.namelist())
            for path, name in path_name_mapper:
                with learning_server_zip.open(path) as infile:
                    content = infile.read()
                    learn_server_path, model_path = name.split('/model/')
                    new_path = os.environ.get('AIMODULE_HOME') + '/model/' + model_path
                    serving_server_zip.writestr(new_path, content)
            serving_server_zip.extractall('/')
        # 파일 삭제
        self.learning_server_zip.unlink()
        self.serving_server_zip.unlink()

    # 로컬 모델 파일 경로 삭제 후 백업 폴더의 모델파일로 원복
    def rollback_model(self):
        if os.path.isdir(self.zip_path.parent):
            shutil.rmtree(self.zip_path.parent)

        if os.path.isdir(self.model_bak_path):
            shutil.copytree(self.model_bak_path, self.zip_path.parent)

    # 기존 모델 파일 작업 전 백업
    def backup_model(self):
        # backup 폴더 삭제
        if os.path.isdir(self.model_bak_path):
            shutil.rmtree(self.model_bak_path)

        shutil.copytree(self.zip_path.parent, self.model_bak_path)

    def __enter__(self):
        self.zip()

    def __exit__(self, *args, **kwargs):
        self.extract()
