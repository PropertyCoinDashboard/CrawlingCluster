import logging


def log(name: str, log_location: str):
    """
    로그 생성
    """
    logger = logging.getLogger(name)

    # 로그의 출력 기준 설정
    logger.setLevel(logging.INFO)

    # log 출력 형식
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # log 출력
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # log 를 파일에 출력
    file_handler = logging.FileHandler(log_location)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
