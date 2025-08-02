"""
服務註冊模塊

定義所有服務的註冊邏輯，包括依賴關係和生命週期管理。
"""

import tkinter as tk
from typing import Dict, Any

from .service_container import ServiceContainer
from core.services import (
    FileService,
    TranslationService,
    HighlightingService,
    ProjectService,
)
from core.services.theme_service import ThemeService
from core.state import AppStateManager
from ui.main_window import MainWindow
from ui.event_handlers import EventHandlers


class ServiceRegistration:
    """服務註冊器 - 負責註冊所有應用服務"""

    def __init__(self, container: ServiceContainer):
        self.container = container

    def register_all_services(self, root: tk.Tk, config: Dict[str, Any] = None):
        """
        註冊所有應用服務

        Args:
            root: Tkinter根窗口
            config: 配置字典
        """
        if config is None:
            config = {}

        # 1. 註冊根窗口實例
        self.container.register_instance(tk.Tk, root)

        # 2. 註冊核心服務（單例）
        self._register_core_services(config)

        # 3. 註冊狀態管理器（單例）
        self._register_state_manager(config)

        # 4. 註冊UI組件（單例）
        self._register_ui_components()

        # 5. 註冊事件處理器（單例）
        self._register_event_handlers()

    def _register_core_services(self, config: Dict[str, Any]):
        """註冊核心服務"""

        # FileService - 文件操作服務
        self.container.register_singleton(FileService, lambda: FileService())

        # TranslationService - 翻譯服務
        def create_translation_service():
            service = TranslationService()
            # 從配置中設置並發數
            if "max_concurrent_requests" in config:
                service.set_max_concurrent_requests(config["max_concurrent_requests"])
            return service

        self.container.register_singleton(
            TranslationService, create_translation_service
        )

        # HighlightingService - 高亮服務
        def create_highlighting_service():
            enabled = config.get("highlighting_enabled", True)
            return HighlightingService(enabled=enabled)

        self.container.register_singleton(
            HighlightingService, create_highlighting_service
        )

        # ProjectService - 項目服務
        self.container.register_singleton(ProjectService, lambda: ProjectService())
        
        # ThemeService - 主題服務
        def create_theme_service():
            root = self.container.resolve(tk.Tk)
            return ThemeService(root)
        
        self.container.register_singleton(ThemeService, create_theme_service)

    def _register_state_manager(self, config: Dict[str, Any]):
        """註冊狀態管理器"""
        self.container.register_singleton(AppStateManager, lambda: AppStateManager())

    def _register_ui_components(self):
        """註冊UI組件"""

        def create_main_window():
            root = self.container.resolve(tk.Tk)
            return MainWindow(root)

        self.container.register_singleton(MainWindow, create_main_window)

    def _register_event_handlers(self):
        """註冊事件處理器"""

        def create_event_handlers():
            root = self.container.resolve(tk.Tk)
            ui = self.container.resolve(MainWindow)
            state_manager = self.container.resolve(AppStateManager)
            file_service = self.container.resolve(FileService)
            translation_service = self.container.resolve(TranslationService)
            highlighting_service = self.container.resolve(HighlightingService)
            project_service = self.container.resolve(ProjectService)

            return EventHandlers(
                root=root,
                ui=ui,
                state_manager=state_manager,
                file_service=file_service,
                translation_service=translation_service,
                highlighting_service=highlighting_service,
                project_service=project_service,
            )

        self.container.register_singleton(EventHandlers, create_event_handlers)


def register_default_services(
    container: ServiceContainer, root: tk.Tk, config: Dict[str, Any] = None
) -> ServiceContainer:
    """
    註冊默認服務配置

    Args:
        container: 服務容器
        root: Tkinter根窗口
        config: 配置字典

    Returns:
        配置好的服務容器
    """
    registration = ServiceRegistration(container)
    registration.register_all_services(root, config)
    return container
