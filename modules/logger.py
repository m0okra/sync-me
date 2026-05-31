import logging
import logging.config
import datetime
import traceback
import atexit
from config import PROJECT_NAME, ROOT, LOG_PATH
from config import FILE_ENCODING

timestamp = datetime.datetime.now().strftime("%Y%m%d")
log_filename = f"{ROOT}{LOG_PATH}{PROJECT_NAME}_{timestamp}.log"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            # 'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            "format": "%(asctime)s [%(levelname)s] %(message)s"
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": log_filename,
            "formatter": "standard",
            "encoding": FILE_ENCODING,
        },
    },
    "loggers": {
        "": {"handlers": ["console", "file"], "level": "INFO", "propagate": True},
    },
}

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(PROJECT_NAME)
atexit.register(logging.shutdown)


def error_log(e: BaseException) -> str:
    """
    错误日志格式化函数

    参数:
        e: 要处理的异常对象

    返回:
        格式化后的错误字符串，包含异常信息和堆栈跟踪
        即使在出错情况下也会返回一个有用的错误字符串
    """
    try:
        # 安全获取repr信息
        try:
            e_repr = repr(e)
            if not isinstance(e_repr, str):
                e_repr = str(e_repr)
        except Exception as repr_error:
            e_repr = f"<Exception repr failed: {type(repr_error).__name__}>"

        # 安全获取堆栈信息
        try:
            stack_trace = traceback.format_exc()
            if not stack_trace or stack_trace == "None\n":
                # 如果format_exc()无效，手动格式化
                stack_trace = "".join(
                    traceback.format_exception(type(e), e, e.__traceback__)
                )
        except Exception as trace_error:
            stack_trace = (
                f"<Traceback generation failed: {type(trace_error).__name__}>\n"
            )

        return e_repr + "\n" + stack_trace
    except Exception as fatal_error:
        # 如果连这个函数都出错了，返回最基本的错误信息
        return f"<Fatal error in error_log: {type(fatal_error).__name__}, original exception: {type(e).__name__}>"


def error_log_simple(e: BaseException) -> str:
    """
    错误日志格式化函数简单版

    参数:
        e: 要处理的异常对象

    返回:
        格式化后的错误字符串，仅包含异常信息
        即使在出错情况下也会返回一个有用的错误字符串
    """
    try:
        # 安全获取repr信息
        try:
            e_repr = repr(e)
            if not isinstance(e_repr, str):
                e_repr = str(e_repr)
        except Exception as repr_error:
            e_repr = f"<Exception repr failed: {type(repr_error).__name__}>"
        return e_repr
    except Exception as fatal_error:
        # 如果连这个函数都出错了，返回最基本的错误信息
        return f"<Fatal error in error_log_simple: {type(fatal_error).__name__}, original exception: {type(e).__name__}>"
