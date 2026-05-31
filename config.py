# 配置文件
import os
import json

PROJECT_NAME = "Sync-me"
VERSION = "v1.1"
FILE_ENCODING = "utf-8"
ROOT = os.path.dirname(os.path.abspath(__file__))
SELF_PID = os.getpid()

CONSOLE_START_HIDE = True
CONFIG_PATH = "\\config.json"
SYNCTHING_PATH = "\\bin\\syncthing.exe"
SYNCTHING_CONFIG_PATH = "%LOCALAPPDATA%\\Syncthing\\config.xml"
LOG_PATH = "\\logs\\"
CMD_ENCODING = "utf-8"
CMD_STREAM_TIMEOUT = 0.1
CMD_CHECK_TIMEOUT_INTERVAL = 0.5
PROCESS_TERM_WAIT = 2.0

SUBPROCESS_CONFIG = {"enable": False, "command": "", "cwd": ""}

FILE_MIGRATE_PATHS: dict = {}

# 文本编辑器路径
TEXT_EDITOR_PATH = "notepad.exe"

# 从config.json加载用户配置，覆盖默认值
_json_path = ROOT + CONFIG_PATH
if os.path.exists(_json_path):
    with open(_json_path, "r", encoding=FILE_ENCODING) as _f:
        _json_config = json.load(_f)
    _user_config_keys = [
        "CONSOLE_START_HIDE",
        "SYNCTHING_PATH",
        "SYNCTHING_CONFIG_PATH",
        "LOG_PATH",
        "CMD_ENCODING",
        "CMD_STREAM_TIMEOUT",
        "CMD_CHECK_TIMEOUT_INTERVAL",
        "PROCESS_TERM_WAIT",
        "SUBPROCESS_CONFIG",
        "FILE_MIGRATE_PATHS",
        "TEXT_EDITOR_PATH",
    ]
    for _key in _user_config_keys:
        if _key in _json_config:
            globals()[_key] = _json_config[_key]

# 托盘图标相关设置，不需要修改
ICON_COLOR_EMPTY = (255, 255, 255, 255)  # 灰色填充（RGBA）
ICON_COLOR_INFO = (110, 255, 255, 255)  # 蓝色填充（RGBA）
ICON_COLOR_WARN = (255, 182, 78, 255)  # 橙色填充（RGBA）
ICON_COLOR_ERROR = (255, 79, 79, 255)  # 红色填充（RGBA）
ICON_COLOR_BORDER = (255, 255, 255, 255)  # 浅灰色边框（RGBA）
ICON_COLOR_LINE = (128, 128, 128, 255)  # 灰色线条（RGBA）
ICON_COLOR_PAUSE = (255, 255, 255, 255)  # 暂停符号颜色（RGBA）
ICON_COLOR_PAUSE_BG = (32, 32, 32, 255)  # 暂停符号背景颜色（RGBA）
ICON_SIZE = 100  # 图标大小
ICON_BORDER_WIDTH = 4  # 边框宽度
LINE_WIDTH = 3  # 线宽
ICON_REFRESH_WAIT = 0.1
ICON_FLASH_DURATION = 2.0
TRAY_MONITOR_THREAD_TIMEOUT = 1
LONGITUDES = [-90, -60, -30, 0, 30, 60, 90]

# Syncthing输出监控相关
SYNCTHING_CHECK_INTERVAL = 0.1
# Syncthing日志关键词映射（关键词开头匹配 -> 显示文本）
SYNCTHING_LOG_KEYWORDS = {
    "Synced file": "已同步文件",
    "Ready to synchronize": "准备同步",
    "Completed initial scan": "初始扫描完成",
    "GUI and API listening": "GUI已启动",
    "Established secure connection": "连接已建立",
    "Additional device connection": "设备已连接",
    "Device disconnected": "设备已断开",
    "Failed to parse dialer address": "解析地址失败",
    "Error": "发生错误",
}
# 对于这一类错误，图标始终为INFO级别的颜色，状态文本照常显示
SYNCTHING_IGNORE_KEYWORDS = ["Failed to parse dialer address"]

# 对常量进行预处理
SYNCTHING_CONFIG_PATH = os.path.expandvars(SYNCTHING_CONFIG_PATH)
SYNCTHING_PATH = ROOT + SYNCTHING_PATH
CONFIG_PATH = ROOT + CONFIG_PATH
