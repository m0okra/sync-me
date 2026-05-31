import subprocess
import os
from modules.logger import logger, error_log
from config import SYNCTHING_CONFIG_PATH, TEXT_EDITOR_PATH


class ConfigEditor:
    """配置文件编辑器"""

    def __init__(self, state_manager):
        self.state_manager = state_manager

    def open_config(self) -> bool:
        """
        使用文本编辑器打开Syncthing配置文件

        返回:
            是否成功打开
        """
        if not os.path.exists(SYNCTHING_CONFIG_PATH):
            logger.error(f"[config_editor] 配置文件不存在: {SYNCTHING_CONFIG_PATH}")
            self.state_manager.set_status_text("配置文件不存在")
            return False

        try:
            subprocess.Popen(
                args=[TEXT_EDITOR_PATH, SYNCTHING_CONFIG_PATH],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            logger.info(f"[config_editor] 已使用 {TEXT_EDITOR_PATH} 打开配置文件")
            self.state_manager.set_status_text("已打开配置文件")
            return True
        except FileNotFoundError:
            logger.error(f"[config_editor] 文本编辑器不存在: {TEXT_EDITOR_PATH}")
            self.state_manager.set_status_text("文本编辑器不存在")
            return False
        except Exception as e:
            logger.error(f"[config_editor] 打开配置文件失败: {error_log(e)}")
            self.state_manager.set_status_text("打开配置文件失败")
            return False

    def get_config_path(self) -> str:
        """获取配置文件路径"""
        return SYNCTHING_CONFIG_PATH
