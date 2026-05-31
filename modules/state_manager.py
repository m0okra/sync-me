import pystray
from threading import Thread, Event, RLock
from enum import Enum
import time
from modules.timer import Timer
from modules.logger import logger, error_log
from modules.win import window_hide, window_show
from modules.icon_draw import generate_all_icons
from config import (
    PROJECT_NAME,
    VERSION,
    TRAY_MONITOR_THREAD_TIMEOUT,
    ICON_FLASH_DURATION,
    ICON_REFRESH_WAIT,
    SUBPROCESS_CONFIG,
)


class _TrayIcon(pystray.Icon):
    def _on_notify(self, wparam, lparam):
        if lparam == 0x0203:
            if hasattr(self, "_double_click_cb") and self._double_click_cb:
                self._double_click_cb()
            return
        super()._on_notify(wparam, lparam)


class TrayIcons(Enum):
    EMPTY = 0
    INFO = 1
    WARN = 2
    ERROR = 3


class AlarmLevel(Enum):
    INFO = 0
    WARN = 1
    ERROR = 2


class State_Manager:
    """状态管理器，用于管理托盘图标和程序状态"""

    def __init__(self):
        self.lock = RLock()
        self.thread_stop = Event()
        self.shared_state = {}
        self.syncthing_restart_callback = None
        self.syncthing_pause_resume_callback = None
        self.file_migrate_callback = None
        self.file_migrate_reverse_callback = None
        self.web_gui_callback = None
        self.config_editor_callback = None
        self.subprocess_pause_resume_callback = None
        self.subprocess_restart_callback = None

        init_state = {
            "icon": TrayIcons.INFO.value,
            "alarm_lv": AlarmLevel.INFO.value,
            "status_text": "正在启动...",
            "console_hide": True,
            "flash_state": 0,
            "syncthing_running": False,
            "syncthing_paused": False,
            "subprocess_paused": False,
            "last_output_time": time.time(),
            "initialized": False,
        }
        self.shared_state.update(init_state)

        logger.info("[state_manager] 正在预生成图标缓存...")
        self.all_icons = generate_all_icons()
        logger.info("[state_manager] 图标缓存生成完成")

        self.icon = _TrayIcon(
            name=PROJECT_NAME,
            icon=self.all_icons["normal"][TrayIcons.INFO.value][-1],
            title=PROJECT_NAME + " " + VERSION,
            menu=self._create_menu(init_state),
        )
        self.icon._double_click_cb = lambda: self._open_web_gui(self.icon)

    def set_callbacks(
        self,
        syncthing_restart=None,
        syncthing_pause_resume=None,
        file_migrate=None,
        file_migrate_reverse=None,
        web_gui=None,
        config_editor=None,
        subprocess_pause_resume=None,
        subprocess_restart=None,
    ):
        """设置回调函数"""
        self.syncthing_restart_callback = syncthing_restart
        self.syncthing_pause_resume_callback = syncthing_pause_resume
        self.file_migrate_callback = file_migrate
        self.file_migrate_reverse_callback = file_migrate_reverse
        self.web_gui_callback = web_gui
        self.config_editor_callback = config_editor
        self.subprocess_pause_resume_callback = subprocess_pause_resume
        self.subprocess_restart_callback = subprocess_restart

    def _create_menu(self, current_state: dict):
        """创建动态更新的右键菜单"""
        menu_items = [
            pystray.MenuItem(
                lambda _: (
                    "显示控制台" if current_state["console_hide"] else "隐藏控制台"
                ),
                self._toggle_console,
            )
        ]

        if self.file_migrate_callback:
            menu_items.append(pystray.MenuItem("迁入备份文件夹", self._do_file_migrate))

        if self.file_migrate_reverse_callback:
            menu_items.append(
                pystray.MenuItem("迁回同步文件夹", self._do_file_migrate_reverse)
            )
        menu_items.append(
            pystray.Menu.SEPARATOR,
        )
        if self.web_gui_callback:
            menu_items.append(pystray.MenuItem("打开Web GUI", self._open_web_gui))

        if self.config_editor_callback:
            menu_items.append(pystray.MenuItem("编辑配置文件", self._edit_config))

        menu_items.extend(
            [
                pystray.MenuItem(
                    lambda _: (
                        "继续同步" if current_state["syncthing_paused"] else "暂停同步"
                    ),
                    self._pause_resume_syncthing,
                    enabled=lambda _: current_state["initialized"],
                ),
                pystray.MenuItem(
                    "重启软件",
                    self._restart_syncthing,
                    enabled=lambda _: (
                        current_state["syncthing_running"]
                        and not current_state["syncthing_paused"]
                    ),
                ),
                pystray.Menu.SEPARATOR,
            ]
        )

        if SUBPROCESS_CONFIG["enable"]:
            menu_items.extend(
                [
                    pystray.MenuItem(
                        lambda _: (
                            "开启子进程"
                            if current_state["subprocess_paused"]
                            else "暂停子进程"
                        ),
                        self._pause_resume_subprocess,
                        enabled=lambda _: current_state["initialized"],
                    ),
                    pystray.MenuItem(
                        "重启子进程",
                        self._restart_subprocess,
                        enabled=lambda _: not current_state["subprocess_paused"],
                    ),
                    pystray.Menu.SEPARATOR,
                ]
            )

        menu_items.append(
            pystray.MenuItem(
                "退出", self._quit, enabled=lambda _: current_state["initialized"]
            )
        )

        return pystray.Menu(*menu_items)

    def _set(self, key: str, value, update: bool = True):
        self.shared_state[key] = value
        if update:
            self._update()

    def set_status_text(self, status_text: str):
        """设置状态文本"""
        self._set("status_text", status_text, False)

    def set_alarm_lv(self, alarm_lv: int):
        """设置警告等级"""
        self._set("alarm_lv", alarm_lv, False)

    def set_syncthing_running(self, running: bool):
        """设置Syncthing运行状态"""
        self._set("syncthing_running", running)

    def set_syncthing_paused(self, paused: bool):
        """设置Syncthing暂停状态"""
        self._set("syncthing_paused", paused)

    def update_last_output_time(self):
        """更新最后输出时间"""
        with self.lock:
            self.shared_state["last_output_time"] = time.time()

    def finish_init(self):
        self._set("initialized", True)

    def _toggle_console(self, icon):
        """切换控制台显示"""
        with self.lock:
            console_should_hide = not self.shared_state["console_hide"]
            self.shared_state["console_hide"] = console_should_hide
        if console_should_hide:
            window_hide()
        else:
            window_show()
        self._update()

    def _restart_syncthing(self, icon):
        """重启Syncthing"""
        if self.syncthing_restart_callback:
            self.syncthing_restart_callback()

    def _pause_resume_syncthing(self, icon):
        """暂停/继续同步"""
        if self.syncthing_pause_resume_callback:
            self.syncthing_pause_resume_callback()

    def _do_file_migrate(self, icon):
        """执行文件迁移（同步文件夹到备份文件夹）"""
        if self.file_migrate_callback:
            self.file_migrate_callback()

    def _do_file_migrate_reverse(self, icon):
        """执行反向文件迁移（备份文件夹到同步文件夹）"""
        if self.file_migrate_reverse_callback:
            self.file_migrate_reverse_callback()

    def _open_web_gui(self, icon):
        """打开Web GUI"""
        if self.web_gui_callback:
            self.web_gui_callback()

    def _edit_config(self, icon):
        """编辑配置文件"""
        if self.config_editor_callback:
            self.config_editor_callback()

    def _pause_resume_subprocess(self, icon):
        """暂停/开启子进程"""
        if self.subprocess_pause_resume_callback:
            self.subprocess_pause_resume_callback()

    def _restart_subprocess(self, icon):
        """重启子进程"""
        if self.subprocess_restart_callback:
            self.subprocess_restart_callback()

    def set_subprocess_paused(self, paused: bool):
        """设置子进程暂停状态"""
        self._set("subprocess_paused", paused)

    def _quit(self, icon):
        """点击退出按钮"""
        self.thread_stop.set()
        if hasattr(self, "monitor_thread"):
            self.monitor_thread.join(timeout=TRAY_MONITOR_THREAD_TIMEOUT)
        icon.stop()

    def quit(self):
        """调用该方法退出托盘管理程序"""
        self._quit(self.icon)

    def _update(self, current_state: dict | None = None, refresh_light: bool = False):
        """更新托盘图标"""
        if current_state is None:
            with self.lock:
                current_state = dict(self.shared_state)
        try:
            tooltip = current_state["status_text"]

            icon_index = TrayIcons.INFO.value
            if current_state["alarm_lv"] == AlarmLevel.WARN.value:
                icon_index = TrayIcons.WARN.value
            elif current_state["alarm_lv"] == AlarmLevel.ERROR.value:
                icon_index = TrayIcons.ERROR.value

            title_list = [PROJECT_NAME + " " + VERSION, tooltip]
            self.icon.title = "\n".join(title_list)

            is_paused = current_state["syncthing_paused"]
            icon_type = "paused" if is_paused else "normal"

            if refresh_light:
                time_since_last_output = time.time() - current_state["last_output_time"]
                should_flash = time_since_last_output < ICON_FLASH_DURATION

                if should_flash:
                    with self.lock:
                        flash_state = self.shared_state["flash_state"]
                        flash_state = (flash_state + 1) % 6
                        self.shared_state["flash_state"] = flash_state
                else:
                    with self.lock:
                        self.shared_state["flash_state"] = 0
                        flash_state = -1

                self.icon.icon = self.all_icons[icon_type][icon_index][flash_state]
            else:
                self.icon.icon = self.all_icons[icon_type][icon_index][-1]

            self.icon.menu = self._create_menu(current_state)
            self.icon.update_menu()
        except OSError as e:
            if getattr(e, "winerror", None) == 1402:
                pass
            else:
                raise

    def run(self):
        """启动托盘图标"""

        def monitor_changes():
            timer = Timer()
            last_state = None
            while not self.thread_stop.is_set():
                try:
                    with self.lock:
                        current_state = dict(self.shared_state)
                    if current_state != last_state:
                        self._update(current_state, refresh_light=True)
                        last_state = current_state
                    timer.sleep(ICON_REFRESH_WAIT)
                except Exception as e:
                    logger.error(f"[state_manager] 监控线程异常：{error_log(e)}")
                    timer.sleep(ICON_REFRESH_WAIT)

        self.monitor_thread = Thread(target=monitor_changes, daemon=True)
        self.monitor_thread.start()
        self.icon.run()
