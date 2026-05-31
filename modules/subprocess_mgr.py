import subprocess
from threading import Thread, Event
from modules.logger import logger, error_log
from modules.timer import Timer
from modules.win import kill_process_entire_family
from config import CMD_ENCODING, PROCESS_TERM_WAIT


class Subprocess_Manager:
    """子进程管理器"""

    def __init__(self, state_manager, command: str, cwd: str | None = None):
        self.state_manager = state_manager
        self.command = command
        self.cwd = cwd
        self.process: subprocess.Popen[str] | None = None
        self.stop_event = Event()
        self.stdout_thread: Thread | None = None
        self.stderr_thread: Thread | None = None

    def _handle_stdout(self, stream):
        for line in iter(stream.readline, ""):
            if self.stop_event.is_set():
                break
            line_str = line.rstrip("\n")
            self.state_manager.update_last_output_time()
            logger.info(f"[subprocess] {line_str}")
        stream.close()

    def _handle_stderr(self, stream):
        for line in iter(stream.readline, ""):
            if self.stop_event.is_set():
                break
            line_str = line.rstrip("\n")
            self.state_manager.update_last_output_time()
            logger.warning(f"[subprocess] {line_str}")
        stream.close()

    def start(self) -> bool:
        try:
            self.process = subprocess.Popen(
                args=self.command,
                cwd=self.cwd,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding=CMD_ENCODING,
                errors="replace",
            )

            self.stop_event.clear()

            self.stdout_thread = Thread(
                target=self._handle_stdout, daemon=True, args=(self.process.stdout,)
            )
            self.stderr_thread = Thread(
                target=self._handle_stderr, daemon=True, args=(self.process.stderr,)
            )

            self.stdout_thread.start()
            self.stderr_thread.start()

            logger.info(f"[subprocess] 子进程已启动，PID: {self.process.pid}")
            return True

        except Exception as e:
            logger.error(f"[subprocess] 启动失败: {error_log(e)}")
            return False

    def stop(self) -> bool:
        try:
            self.stop_event.set()

            if self.process and self.process.poll() is None:
                kill_process_entire_family(self.process.pid, timeout=PROCESS_TERM_WAIT)

            if self.stdout_thread and self.stdout_thread.is_alive():
                self.stdout_thread.join(timeout=1)
            if self.stderr_thread and self.stderr_thread.is_alive():
                self.stderr_thread.join(timeout=1)

            logger.info("[subprocess] 子进程已停止")
            return True

        except Exception as e:
            logger.error(f"[subprocess] 停止失败: {error_log(e)}")
            return False

    def restart(self) -> bool:
        logger.info("[subprocess] 正在重启子进程...")

        if not self.stop():
            return False

        timer = Timer()
        timer.sleep(2)

        return self.start()

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def wait(self):
        if self.process:
            self.process.wait()
