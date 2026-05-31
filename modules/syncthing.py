import subprocess
import psutil
from threading import Thread, Event
from modules.logger import logger, error_log
from modules.timer import Timer
from modules.win import kill_process_entire_family
from config import (
    SYNCTHING_PATH,
    CMD_ENCODING,
    PROCESS_TERM_WAIT,
    SYNCTHING_LOG_KEYWORDS,
    SYNCTHING_IGNORE_KEYWORDS,
)


class Syncthing_Manager:
    """Syncthing进程管理器"""

    def __init__(self, state_manager):
        self.state_manager = state_manager
        self.process = None
        self.stop_event = Event()
        self.stdout_thread = None
        self.stderr_thread = None

    def _parse_log_level(self, line_str):
        """解析syncthing日志级别，返回(级别字符串, 级别枚举值)"""
        if " INF " in line_str[:30]:
            return "INF", 0
        elif " WRN " in line_str[:30]:
            return "WRN", 1
        elif " ERR " in line_str[:30]:
            return "ERR", 2
        return "INF", 0

    def _extract_core_message(self, line_str):
        """提取syncthing日志的核心信息（移除前24个字符）"""
        if len(line_str) > 24:
            return line_str[24:]
        return line_str

    def _match_keyword(self, core_message):
        """匹配关键词，返回对应的状态文本"""
        for keyword, status_text in SYNCTHING_LOG_KEYWORDS.items():
            if core_message.startswith(keyword):
                return status_text
        return None

    def _should_ignore_alarm(self, core_message):
        """检查是否应该忽略该消息的告警级别（保持INFO颜色）"""
        for keyword in SYNCTHING_IGNORE_KEYWORDS:
            if core_message.startswith(keyword):
                return True
        return False

    def _handle_stdout(self, stream):
        """处理标准输出流"""
        for line in iter(stream.readline, ""):
            if self.stop_event.is_set():
                break
            line_str = line.rstrip("\n")

            log_level_str, alarm_lv = self._parse_log_level(line_str)
            core_message = self._extract_core_message(line_str)

            status_text = self._match_keyword(core_message)
            if status_text:
                self.state_manager.set_status_text(status_text)

            if not self._should_ignore_alarm(core_message):
                self.state_manager.set_alarm_lv(alarm_lv)
            self.state_manager.update_last_output_time()

            if log_level_str == "INF":
                logger.info(f"[syncthing] {core_message}")
            elif log_level_str == "WRN":
                logger.warning(f"[syncthing] {core_message}")
            elif log_level_str == "ERR":
                logger.error(f"[syncthing] {core_message}")
            else:
                logger.info(f"[syncthing] {core_message}")

        stream.close()

    def _handle_stderr(self, stream):
        """处理标准错误流"""
        for line in iter(stream.readline, ""):
            if self.stop_event.is_set():
                break
            line_str = line.rstrip("\n")

            log_level_str, alarm_lv = self._parse_log_level(line_str)
            core_message = self._extract_core_message(line_str)

            status_text = self._match_keyword(core_message)
            if status_text:
                self.state_manager.set_status_text(status_text)

            if not self._should_ignore_alarm(core_message):
                self.state_manager.set_alarm_lv(alarm_lv)
            self.state_manager.update_last_output_time()

            if log_level_str == "ERR":
                logger.error(f"[syncthing] {core_message}")
            else:
                logger.warning(f"[syncthing] {core_message}")
        stream.close()

    def start(self) -> bool:
        """启动Syncthing进程"""
        try:
            self.process = subprocess.Popen(
                args=SYNCTHING_PATH,
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

            self.state_manager.set_syncthing_running(True)
            self.state_manager.set_status_text("Syncthing运行中")
            logger.info(f"[syncthing] Syncthing已启动，PID: {self.process.pid}")
            return True

        except Exception as e:
            logger.error(f"[syncthing] 启动失败: {error_log(e)}")
            self.state_manager.set_syncthing_running(False)
            self.state_manager.set_status_text("Syncthing启动失败")
            return False

    def stop(self) -> bool:
        """停止Syncthing进程"""
        try:
            self.stop_event.set()

            if self.process and self.process.poll() is None:
                kill_process_entire_family(self.process.pid, timeout=PROCESS_TERM_WAIT)

            self._kill_all_syncthing_processes()

            if self.stdout_thread and self.stdout_thread.is_alive():
                self.stdout_thread.join(timeout=1)
            if self.stderr_thread and self.stderr_thread.is_alive():
                self.stderr_thread.join(timeout=1)

            self.state_manager.set_syncthing_running(False)
            self.state_manager.set_status_text("Syncthing已停止")
            logger.info("[syncthing] Syncthing已停止")
            return True

        except Exception as e:
            logger.error(f"[syncthing] 停止失败: {error_log(e)}")
            return False

    def _kill_all_syncthing_processes(self):
        """终止所有syncthing.exe进程"""
        killed_count = 0
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                if proc.info["name"] and proc.info["name"].lower() == "syncthing.exe":
                    proc.kill()
                    killed_count += 1
                    logger.info(f"[syncthing] 终止残留进程 PID: {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        if killed_count > 0:
            logger.info(f"[syncthing] 共终止 {killed_count} 个残留的syncthing.exe进程")

    def restart(self) -> bool:
        """重启Syncthing进程"""
        logger.info("[syncthing] 正在重启Syncthing...")
        self.state_manager.set_status_text("正在重启Syncthing...")

        if not self.stop():
            return False

        timer = Timer()
        timer.sleep(2)

        return self.start()

    def is_running(self) -> bool:
        """检查Syncthing是否正在运行"""
        return self.process is not None and self.process.poll() is None

    def wait(self):
        """等待Syncthing进程结束"""
        if self.process:
            self.process.wait()
