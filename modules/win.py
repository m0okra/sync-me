import subprocess
import psutil
from modules.timer import Timer
from typing import Union
from threading import Thread, Event
from modules.logger import logger, error_log
from config import PROCESS_TERM_WAIT, CMD_STREAM_TIMEOUT, CMD_CHECK_TIMEOUT_INTERVAL
from config import CMD_ENCODING

import win32gui
import win32api
import win32process
import win32con
import ctypes

# 获取系统API
user32 = ctypes.WinDLL("user32")


def window_hide(hwnd: int | None = None):
    if hwnd is None:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd and win32gui.IsWindow(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        user32.ShowWindow(hwnd, win32con.SW_HIDE)
    logger.info(f"[win] 将窗口最小化到托盘。句柄：{hwnd}")


def window_show(hwnd: int | None = None):
    if hwnd is None:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd and win32gui.IsWindow(hwnd):
        user32.ShowWindow(hwnd, win32con.SW_SHOW)
        win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
    logger.info(f"[win] 正常显示窗口。句柄：{hwnd}")


def _handle_stream(stream, logger_method, ignore_event, stop_event):
    for line in iter(stream.readline, ""):
        logger_method(line.rstrip("\n"))
    stream.close()


def run_cmd(
    command: str,
    cwd: str | None = None,
    timeout: float | None = None,
    handle_stream=_handle_stream,
    stop_check=None,
) -> bool:
    """可以控制返回值的run_cmd，用于精细判断脚本是否运行成功"""
    process = subprocess.Popen(
        args=command,
        cwd=cwd,
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding=CMD_ENCODING,
        errors="replace",
    )
    # 使用事件来通知是否需要终止或忽略错误
    stop_event = Event()
    ignore_event = Event()
    # 传递process和stop_event给handle_stream
    stdout_thread = Thread(
        target=handle_stream,
        daemon=True,
        args=(process.stdout, logger.info, ignore_event, stop_event),
    )
    stderr_thread = Thread(
        target=handle_stream,
        daemon=True,
        args=(process.stderr, logger.debug, ignore_event, stop_event),
    )
    # 启动
    stdout_thread.start()
    stderr_thread.start()
    timeout_occurred = False
    try:
        timer = Timer()
        while process.poll() is None:
            if timeout and timer.count() > timeout:
                timeout_occurred = True
                break
            # 检查外部stop_check函数是否返回True，若返回True则终止进程
            if stop_check is not None and stop_check():
                logger.info("[cmd] 检测到外部终止信号，已强制终止进程")
                process.kill()
                return False
            timer.sleep(CMD_CHECK_TIMEOUT_INTERVAL)
        if timeout_occurred:
            logger.error("[cmd] 超时！已强制终止进程")
            process.kill()
            return False
    except Exception as e:
        logger.error(f"[cmd] 任务执行错误！已强制终止进程：{error_log(e)}")
        process.kill()
        return False
    finally:
        if stdout_thread and stdout_thread.is_alive():
            stdout_thread.join(timeout=CMD_STREAM_TIMEOUT)
        if stderr_thread and stderr_thread.is_alive():
            stderr_thread.join(timeout=CMD_STREAM_TIMEOUT)
        # 确保进程被清理
        if process and process.poll() is None:
            process.terminate()
            process.wait(timeout=CMD_STREAM_TIMEOUT)
    # 如果检测到终止条件，返回False
    if stop_event.is_set():
        logger.warning("[cmd] 达成终止条件，视为未成功运行")
        return False
    if ignore_event.is_set():
        logger.warning("[cmd] 达成忽略错误条件，视为成功运行")
        return True
    # 否则返回process是否正常退出
    return process.returncode == 0


def independent_popen(args: Union[list[str], str]) -> subprocess.Popen[str]:
    if isinstance(args, list):
        command: list[str] | str = args
    elif isinstance(args, str):
        command = args
    else:
        raise TypeError("[win] Invalid argument type.")
    # 由于使用independent_process的地方无需返回值，故DEVNULL
    process = subprocess.Popen(
        args=command,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        encoding=CMD_ENCODING,
    )
    return process


class Independent_Process:
    __slots__ = ("args", "process", "pid")

    def __init__(self, args):
        self.args = args
        self.process = independent_popen(self.args)
        self.pid = self.process.pid

    def poll(self):
        return self.process.poll()

    def kill(self):
        return self.process.kill()

    def terminate(self):
        return self.process.terminate()


# 使用psutil实现的功能，用在模拟器已经打开的情况
def is_process_running(executable_path: str) -> bool:
    for proc in psutil.process_iter(["pid", "name", "exe"]):
        try:
            # 检查进程的可执行文件路径是否与给定路径匹配
            if proc.info["exe"] == executable_path:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def kill_process_entire_family(pid: int, timeout: float = PROCESS_TERM_WAIT) -> bool:
    try:
        process = psutil.Process(pid)
        for child in process.children(recursive=True):
            child.kill()  # 强制终止子孙进程
        process.kill()  # 强制终止目标进程
        process.wait(timeout=timeout)
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
        return False


def get_foreground_window_hwnd() -> int | None:
    """获取当前系统处于焦点的窗口句柄，失败返回None。"""
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            logger.info(f"[win] 获取前台窗口句柄: {hwnd}")
            return int(hwnd)
        return None
    except Exception as e:
        logger.warning(f"[win] 获取前台窗口句柄失败: {error_log(e)}")
        return None


def set_focus_to_hwnd(hwnd: int) -> bool:
    """将输入焦点设置到指定窗口句柄的窗口

    实现思路：使用 AttachThreadInput 将当前线程与目标窗口线程附加，
    然后调用 SetActiveWindow / SetFocus 来切换焦点，最后分离输入队列。
    返回 True 表示操作成功（或已尝试），False 表示发生异常或参数无效。
    """
    try:
        if not hwnd or not win32gui.IsWindow(hwnd):
            logger.warning(f"[win] 无效的窗口句柄: {hwnd}")
            return False
        current_thread = win32api.GetCurrentThreadId()
        target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)
        # 附加输入队列以允许跨线程设置焦点
        attached = False
        try:
            win32process.AttachThreadInput(current_thread, target_thread, True)
            attached = True
        except Exception as e:
            logger.info(
                f"[win] 线程附加失败 [{hwnd}] ({current_thread}, {target_thread}): {e}"
            )
        try:
            try:
                win32gui.BringWindowToTop(hwnd)
            except Exception:
                pass
            try:
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                pass
            try:
                win32gui.SetActiveWindow(hwnd)
            except Exception:
                pass
            try:
                win32gui.SetFocus(hwnd)
            except Exception:
                pass
        finally:
            if attached:
                win32process.AttachThreadInput(current_thread, target_thread, False)
        logger.info(f"[win] 设置窗口焦点: {hwnd}")
        return True
    except Exception as e:
        logger.warning(f"[win] 设置窗口焦点失败 ({hwnd}): {error_log(e)}")
        return False


if __name__ == "__main__":
    timer = Timer()
    timer.sleep(5)
    hwnd = get_foreground_window_hwnd()
    timer.sleep(5)
    if hwnd is not None:
        set_focus_to_hwnd(hwnd)
