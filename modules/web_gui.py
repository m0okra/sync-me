import xml.etree.ElementTree as ET
import webbrowser
from modules.logger import logger, error_log
from config import SYNCTHING_CONFIG_PATH


class WebGUI:
    """Web GUI管理器"""

    def __init__(self, state_manager):
        self.state_manager = state_manager
        self.gui_url = None

    def get_gui_url(self) -> str | None:
        """
        从Syncthing配置文件中获取Web GUI地址

        返回:
            Web GUI的URL地址，如 http://127.0.0.1:8384
        """
        if self.gui_url:
            return self.gui_url

        try:
            tree = ET.parse(SYNCTHING_CONFIG_PATH)
            root = tree.getroot()

            gui_element = root.find(".//gui")
            if gui_element is None:
                logger.error("[web_gui] 配置文件中未找到gui元素")
                return None

            address = gui_element.get("address", "127.0.0.1")
            port = gui_element.get("port", "8384")

            use_tls = gui_element.get("tls", "false").lower() == "true"
            protocol = "https" if use_tls else "http"

            if ":" in address:
                self.gui_url = f"{protocol}://[{address}]:{port}"
            else:
                self.gui_url = f"{protocol}://{address}:{port}"

            logger.info(f"[web_gui] 获取到Web GUI地址: {self.gui_url}")
            return self.gui_url

        except FileNotFoundError:
            logger.error(f"[web_gui] 配置文件不存在: {SYNCTHING_CONFIG_PATH}")
            return None
        except ET.ParseError as e:
            logger.error(f"[web_gui] 配置文件解析失败: {error_log(e)}")
            return None
        except Exception as e:
            logger.error(f"[web_gui] 获取Web GUI地址失败: {error_log(e)}")
            return None

    def open(self) -> bool:
        """
        打开Web GUI

        返回:
            是否成功打开
        """
        url = self.get_gui_url()
        if not url:
            self.state_manager.set_status_text("无法获取Web GUI地址")
            return False

        try:
            webbrowser.open(url)
            logger.info(f"[web_gui] 已打开Web GUI: {url}")
            self.state_manager.set_status_text("已打开Web GUI")
            return True
        except Exception as e:
            logger.error(f"[web_gui] 打开Web GUI失败: {error_log(e)}")
            self.state_manager.set_status_text("打开Web GUI失败")
            return False
