"""
基礎處理器類，提供所有Handler的共同功能和依賴
"""

import tkinter as tk
from typing import List, Optional
from abc import ABC, abstractmethod

from core.services import (
    FileService,
    TranslationService,
    HighlightingService,
    ProjectService,
)
from core.state import AppStateManager
from core.models import StringEntry
from ..interfaces.imain_window import IMainWindow
from core.events import get_event_system


class BaseHandler(ABC):
    """所有Handler的基礎類，提供共同的依賴和工具方法"""

    def __init__(
        self,
        root: tk.Tk,
        ui: IMainWindow,
        state_manager: AppStateManager,
        file_service: FileService,
        translation_service: TranslationService,
        highlighting_service: HighlightingService,
        project_service: ProjectService,
    ):
        self.root = root
        self.ui = ui
        self.state_manager = state_manager
        self.file_service = file_service
        self.translation_service = translation_service
        self.highlighting_service = highlighting_service
        self.project_service = project_service

        # 初始化事件系統
        self.event_system = get_event_system()

    # 共同的工具方法
    def _get_current_data(self) -> Optional[List[StringEntry]]:
        """獲取當前文件的數據"""
        return self.state_manager.get_current_file_data()

    def _get_selected_entry(self) -> Optional[StringEntry]:
        """獲取當前選中的條目"""
        return self.state_manager.get_selected_entry()

    def _get_all_selected_entries(self) -> List[StringEntry]:
        """獲取所有選中的條目"""
        data = self._get_current_data()
        if not data:
            return []
        selected_ids = self.ui.get_all_selected_tree_item_ids()
        if not selected_ids:
            return []
        return [entry for entry in data if entry.id in selected_ids]

    def _bind_tab_events(self, tree):
        """綁定特定 treeview 在標籤頁中的事件"""
        # 這個方法需要訪問命令處理器，將在EventHandlerCoordinator中實現
        pass

    @abstractmethod
    def register_commands(self, command_invoker):
        """註冊此Handler負責的命令"""
        pass
