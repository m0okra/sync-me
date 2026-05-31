import sys
import os
import atexit
from threading import Thread

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.logger import logger
from modules.state_manager import State_Manager
from modules.syncthing import Syncthing_Manager
from modules.subprocess_mgr import Subprocess_Manager
from modules.file_migrate import FileMigrator
from modules.web_gui import WebGUI
from modules.config_editor import ConfigEditor
from modules.win import window_hide
from config import CONSOLE_START_HIDE, SUBPROCESS_CONFIG


class SyncMe:
    """主程序类"""

    def __init__(self):
        self.state_manager = None
        self.syncthing_manager = None
        self.file_migrator = None
        self.web_gui = None
        self.config_editor = None
        self.tray_thread = None
        self.subprocess_manager = None

    def init(self):
        """初始化所有组件"""
        logger.info("[main] 正在初始化...")

        self.state_manager = State_Manager()

        self.syncthing_manager = Syncthing_Manager(self.state_manager)
        self.file_migrator = FileMigrator(self.state_manager)
        self.web_gui = WebGUI(self.state_manager)
        self.config_editor = ConfigEditor(self.state_manager)

        if SUBPROCESS_CONFIG["enable"]:
            self.subprocess_manager = Subprocess_Manager(
                self.state_manager,
                SUBPROCESS_CONFIG["command"],
                SUBPROCESS_CONFIG.get("cwd"),
            )

        self.state_manager.set_callbacks(
            syncthing_restart=self._on_restart_syncthing,
            syncthing_pause_resume=self._on_pause_resume_syncthing,
            file_migrate=self._on_file_migrate,
            file_migrate_reverse=self._on_file_migrate_reverse,
            web_gui=self._on_open_web_gui,
            config_editor=self._on_edit_config,
            subprocess_pause_resume=self._on_pause_resume_subprocess,
            subprocess_restart=self._on_restart_subprocess,
        )

        atexit.register(self.cleanup)

        logger.info("[main] 初始化完成")

    def _on_restart_syncthing(self):
        """Syncthing重启回调"""

        def restart_thread():
            self.syncthing_manager.restart()

        Thread(target=restart_thread, daemon=True).start()

    def _on_pause_resume_syncthing(self):
        """暂停/继续同步回调"""

        def pause_resume_thread():
            with self.state_manager.lock:
                is_paused = self.state_manager.shared_state.get(
                    "syncthing_paused", False
                )

            if is_paused:
                logger.info("[main] 继续同步...")
                self.state_manager.set_status_text("正在启动Syncthing...")
                if self.syncthing_manager.start():
                    self.state_manager.set_syncthing_paused(False)
                    self.state_manager.set_status_text("Syncthing运行中")
                else:
                    self.state_manager.set_status_text("Syncthing启动失败")
            else:
                logger.info("[main] 暂停同步...")
                self.state_manager.set_status_text("正在停止Syncthing...")
                if self.syncthing_manager.stop():
                    self.state_manager.set_syncthing_paused(True)
                    self.state_manager.set_status_text("同步已暂停")
                else:
                    self.state_manager.set_status_text("Syncthing停止失败")

        Thread(target=pause_resume_thread, daemon=True).start()

    def _on_file_migrate(self):
        """文件迁移回调（A到B）"""

        def migrate_thread():
            self.file_migrator.migrate(reverse=False)

        Thread(target=migrate_thread, daemon=True).start()

    def _on_file_migrate_reverse(self):
        """文件迁移回调（B到A）"""

        def migrate_thread():
            self.file_migrator.migrate(reverse=True)

        Thread(target=migrate_thread, daemon=True).start()

    def _on_open_web_gui(self):
        """打开Web GUI回调"""
        self.web_gui.open()

    def _on_edit_config(self):
        """编辑配置文件回调"""
        self.config_editor.open_config()

    def _on_restart_subprocess(self):
        """重启子进程回调"""

        def restart_thread():
            if self.subprocess_manager:
                self.subprocess_manager.restart()
                self.state_manager.set_subprocess_paused(False)
                self.state_manager.set_status_text("子进程运行中")

        Thread(target=restart_thread, daemon=True).start()

    def _on_pause_resume_subprocess(self):
        """暂停/开启子进程回调"""

        def pause_resume_thread():
            if not self.subprocess_manager:
                return
            with self.state_manager.lock:
                is_paused = self.state_manager.shared_state.get(
                    "subprocess_paused", False
                )

            if is_paused:
                logger.info("[main] 开启子进程...")
                self.state_manager.set_status_text("正在启动子进程...")
                if self.subprocess_manager.start():
                    self.state_manager.set_subprocess_paused(False)
                    self.state_manager.set_status_text("子进程运行中")
                else:
                    self.state_manager.set_status_text("子进程启动失败")
            else:
                logger.info("[main] 暂停子进程...")
                self.state_manager.set_status_text("正在停止子进程...")
                if self.subprocess_manager.stop():
                    self.state_manager.set_subprocess_paused(True)
                    self.state_manager.set_status_text("子进程已暂停")
                else:
                    self.state_manager.set_status_text("子进程停止失败")

        Thread(target=pause_resume_thread, daemon=True).start()

    def cleanup(self):
        """清理资源"""
        logger.info("[main] 正在清理资源...")
        if self.syncthing_manager:
            self.syncthing_manager.stop()
        if self.subprocess_manager:
            self.subprocess_manager.stop()
        logger.info("[main] 资源清理完成")

    def run(self):
        """运行主程序"""
        logger.info("[main] 程序启动")

        if CONSOLE_START_HIDE:
            window_hide()

        if not self.syncthing_manager.start():
            logger.error("[main] Syncthing启动失败，程序退出")
            return

        if self.subprocess_manager:
            if self.subprocess_manager.start():
                self.state_manager.set_status_text("子进程运行中")
            else:
                self.state_manager.set_subprocess_paused(True)
                self.state_manager.set_status_text("子进程启动失败")

        self.state_manager.finish_init()

        self.state_manager.run()

        logger.info("[main] 程序退出")


def main():
    app = SyncMe()
    app.init()
    app.run()


if __name__ == "__main__":
    main()
