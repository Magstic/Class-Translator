import tkinter as tk
import json
import os
from core.container import (
    create_enhanced_container,
    register_default_services,
    ServiceContainer,
)
from ui.main_window import MainWindow
from ui.event_handlers import EventHandlers
from core.services.theme_service import ThemeService


class App:
    """The main application class, acting as a composition root with dependency injection."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Class Editor")
        self.root.geometry("900x600")
        
        # 将应用实例存储到根窗口中，便于其他组件访问
        self.root._app_instance = self

        # 創建增強的服務容器
        self.container = create_enhanced_container()

        # 2. 加載配置
        self.config = self._load_config()

        # 3. 註冊所有服務
        register_default_services(self.container, root, self.config)

        # 3.1 應用默認主題以避免啟動閃爍
        theme_service = self.container.resolve(ThemeService)
        theme_service.apply_theme('light')

        # 4. 解析UI和事件處理器
        self.ui = self.container.resolve(MainWindow)
        self.event_handlers = self.container.resolve(EventHandlers)

        # 5. 連接UI和事件處理器
        self.ui.set_event_handlers(self.event_handlers)
        self.ui.setup_ui()

    def _load_config(self) -> dict:
        """加載配置文件"""
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        default_config = {
            "max_concurrent_requests": 5,
            "highlighting_enabled": True,
            "window_title": "Class Editor",
            "window_geometry": "900x600",
        }

        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    # 合併默認配置
                    default_config.update(config)
            return default_config
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            return default_config

    def get_container(self) -> ServiceContainer:
        """獲取服務容器實例"""
        return self.container
