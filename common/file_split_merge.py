import enum
import pprint
import shutil
from pathlib import Path

from fsplit.filesplit import Filesplit


# Enum for size units
class SIZE_UNIT(enum.Enum):
    BYTES = 1
    KB = 2
    MB = 3
    GB = 4


KB_SIZE = 1024
MB_SIZE = 1024 * 1024
GB_SIZE = 1024 * 1024 * 1024


def convert_unit(size_in_bytes, unit):
    """Convert the size from bytes to other units like KB, MB or GB"""
    if unit == SIZE_UNIT.KB:
        return size_in_bytes / KB_SIZE
    elif unit == SIZE_UNIT.MB:
        return size_in_bytes / MB_SIZE
    elif unit == SIZE_UNIT.GB:
        return size_in_bytes / GB_SIZE
    else:
        return size_in_bytes


class Logger:
    def info(self, text):
        pprint.pprint(text)


class FileSplitMerge:
    def __init__(
        self,
        model_path: Path,
        logger=None,
        prefix: str = "split_",
        max_file_size: int = GB_SIZE,
    ):
        """
        크기가 큰 파일을 여러 개의 파일로 쪼개서 저장하기 위한 클래스

        How to use
        1. ---------- 추천
        with FileSplitMerge(model_path="/your/model/path", max_file_size=5000000):
            what_to_do()

        2. ----------
        filesplitmerge = FileSplitMerge(model_path="/your/model/path", max_file_size=5000000)
        try:
            filesplitmerge.split_file()
            what_to_do()
        except Exception as e:
            self.logger.info("Exception : {e}")
        finally:
            filesplitmerge.merge_file()

        Parameters
        ----------
        model_path : 나누거나 합칠 파일 폴더
        logger : 로거 없을 시에 print 출력
        prefix : 나눌 폴더의 prefix 이름 ex) split_XXX.pkl
        max_file_size : 최대 파일 크기. 이 크기 이상일 경우 나누기함
        """
        self.fs = Filesplit()
        self.MAX_FILE_SIZE = max_file_size
        self.prefix = prefix
        self.logger = logger if logger is not None else Logger()

        self.model_path = model_path
        self.is_model_path_currect = True
        if type(model_path) == str:
            self.model_path = Path(model_path)

        if not self.model_path.exists():
            self.logger.info(f"model_path is not exists : {self.model_path}")
            self.is_model_path_currect = False
        if self.model_path.is_file():
            self.logger.info(f"model_path is file : {self.model_path}")
            self.is_model_path_currect = False

        self.logger.info(f"[{type(self).__name__}] model_path : {self.model_path}")
        self.logger.info(f"[{type(self).__name__}] is_model_path_currect : {self.is_model_path_currect}")

    def split_file(self):
        """
        특정 폴더를 일정 크기 만큼 나눔

        result : 2G 용량 파일을 1G 로 나누는 경우
         - before
           - test.h5
         - after
           - split_test_h5
             - test_1.h5
             - test_2.h5

        Returns
        -------

        """
        if not self.is_model_path_currect:
            self.logger.info("invalid path !!")
            return

        # model_path 아래의 모들 파일을 리스트로 가져옴
        model_path_list = list(self.model_path.glob("**/*"))
        for path_itr in model_path_list:
            # 파일 요량 체크
            file_size = path_itr.stat().st_size
            if file_size < self.MAX_FILE_SIZE:
                continue
            self.logger.info(
                f"{str(path_itr)} : {convert_unit(file_size, SIZE_UNIT.MB):.2f} MB"
            )
            # your/model/path/split_test_h5
            output_dir = (
                path_itr.parent / f"{self.prefix}{path_itr.stem}_{path_itr.suffix[1:]}"
            )
            # 분할 경로 생성
            output_dir.mkdir(exist_ok=True, parents=True)
            self.fs.split(
                file=path_itr,
                split_size=self.MAX_FILE_SIZE,
                output_dir=output_dir,
                callback=FileSplitMerge.split_cb,
            )
            # 파일 삭제
            path_itr.unlink()

    def merge_file(self):
        """
        나눠진 파일을 다시 합침.

        result : 2G 용량 파일을 1G 로 나누는 경우
         - before
           - split_test_h5
             - test_1.h5
             - test_2.h5
         - after
           - test.h5

        Returns
        -------

        """
        if not self.is_model_path_currect:
            self.logger.info("invalid path !!")
            return

        model_path_list = list(self.model_path.glob("**/*"))
        for path_itr in model_path_list:
            if (
                not path_itr.exists()
                or path_itr.is_file()
                or not self.prefix in str(path_itr)
            ):
                continue
            self.fs.merge(input_dir=path_itr, callback=FileSplitMerge.merge_cb)

            # 폴더 이름을 파일 이름으로 변경
            # split_test_h5 -> test.h5
            output_split_folder = Path(str(path_itr).replace(f"{self.prefix}", ""))
            ext_text = str(output_split_folder.stem).split("_")[-1]
            file_name = str(output_split_folder.stem)[: -(len(ext_text) + 1)]
            file_name = f"{file_name}.{ext_text}"

            # 파일 복사
            self.logger.info(
                f"copy {path_itr / file_name} -> {path_itr.parent / file_name}"
            )
            shutil.copy2(path_itr / file_name, path_itr.parent / file_name)

            # 분할했던 폴더 삭제
            shutil.rmtree(path_itr)

    def __enter__(self):
        self.split_file()

    def __exit__(self, *args, **kwargs):
        self.merge_file()

    @staticmethod
    def split_cb(f, s):
        print(f"file: {f}, size: {convert_unit(s, SIZE_UNIT.MB)}")

    @staticmethod
    def merge_cb(f, s):
        print(f"file: {f}, size: {convert_unit(s, SIZE_UNIT.MB)}")
