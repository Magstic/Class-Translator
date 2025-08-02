"""
事件處理器協調器
統一管理所有拆分後的Handler，提供與原EventHandlers相同的接口
"""

import tkinter as tk
import logging

from core.services import (
    FileService,
    TranslationService,
    HighlightingService,
    ProjectService,
)
from core.state import AppStateManager
from ..interfaces.imain_window import IMainWindow
from core.events import get_event_system
from core.commands import CommandInvoker

from .file_operation_handlers import FileOperationHandlers
from .translation_handlers import TranslationHandlers
from .ui_event_handlers import UIEventHandlers
from .project_handlers import ProjectHandlers
from .search_handlers import SearchHandlers
from .config_handlers import ConfigHandlers
from .theme_handlers import ThemeHandlers


class EventHandlerCoordinator:
    """
    事件處理器協調器

    統一管理所有拆分後的Handler，提供與原EventHandlers相同的接口，
    確保向後兼容性，不影響現有功能。
    """

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

        # 初始化命令調用器
        self.command_invoker = CommandInvoker()

        # 創建所有Handler實例
        self._create_handlers()

        # 註冊所有命令
        self._register_all_commands()

        logging.info("EventHandlerCoordinator initialized with all handlers")

    def _create_handlers(self):
        """創建所有Handler實例"""
        common_args = (
            self.root,
            self.ui,
            self.state_manager,
            self.file_service,
            self.translation_service,
            self.highlighting_service,
            self.project_service,
        )

        self.file_handlers = FileOperationHandlers(*common_args)
        self.translation_handlers = TranslationHandlers(*common_args)
        self.ui_handlers = UIEventHandlers(*common_args)
        self.project_handlers = ProjectHandlers(*common_args)
        self.search_handlers = SearchHandlers(*common_args)
        self.config_handlers = ConfigHandlers(*common_args)
        self.theme_handlers = ThemeHandlers(*common_args)

        # 存儲所有Handler的引用，便於統一管理
        self.all_handlers = [
            self.file_handlers,
            self.translation_handlers,
            self.ui_handlers,
            self.project_handlers,
            self.search_handlers,
            self.config_handlers,
            self.theme_handlers,
        ]

    def _register_all_commands(self):
        """註冊所有Handler的命令"""
        for handler in self.all_handlers:
            handler.register_commands(self.command_invoker)

        logging.info(f"Registered commands from {len(self.all_handlers)} handlers")

    def get_command_handler(self, command_name: str):
        """獲取命令處理器，用於UI綁定（保持與原EventHandlers相同的接口）"""
        return self.command_invoker.create_command_handler(command_name)

    def _bind_tab_events(self, tree):
        """綁定特定 treeview 在標籤頁中的事件（統一處理）"""
        logging.info(f"Binding tree events for tree: {tree}")
        tree.bind(
            "<<TreeviewSelect>>",
            lambda event: self.get_command_handler("tree_select")(event),
        )

    # ==================== 向後兼容的方法委託 ====================
    # 這些方法保持與原EventHandlers相同的接口，確保不影響現有功能

    def on_load_directory(self):
        """委託給FileOperationHandlers"""
        result = self.file_handlers.on_load_directory()
        # 處理需要協調器統一處理的後續操作
        self._post_load_directory_actions()
        return result

    def on_save_file(self):
        """委託給FileOperationHandlers"""
        return self.file_handlers.on_save_file()

    def on_save_all_files(self):
        """委託給FileOperationHandlers"""
        return self.file_handlers.on_save_all_files()

    def on_save_project(self):
        """委託給ProjectHandlers"""
        return self.project_handlers.on_save_project()

    def on_load_project(self):
        """委託給ProjectHandlers"""
        result = self.project_handlers.on_load_project()
        # 處理需要協調器統一處理的後續操作
        self._post_load_project_actions()
        return result

    def on_translate(self):
        """委託給TranslationHandlers"""
        return self.translation_handlers.on_translate()

    def on_translate_all(self):
        """委託給TranslationHandlers"""
        return self.translation_handlers.on_translate_all()

    def on_tree_select(self, event=None):
        """委託給UIEventHandlers"""
        return self.ui_handlers.on_tree_select(event)

    def on_tab_changed(self, event=None):
        """委託給UIEventHandlers，並處理協調器特有的邏輯"""
        result = self.ui_handlers.on_tab_changed(event)
        # 更新菜單狀態等協調器特有的邏輯
        self._update_menu_states()
        return result

    def on_text_changed(self, event=None):
        """委託給UIEventHandlers"""
        return self.ui_handlers.on_text_changed(event)

    def on_translated_text_modified(self, event=None):
        """委託給UIEventHandlers"""
        return self.ui_handlers.on_translated_text_modified(event)

    def on_translated_text_changed_realtime(self, event=None):
        """委託給UIEventHandlers"""
        return self.ui_handlers.on_translated_text_changed_realtime(event)

    def on_highlight_toggle(self):
        """委託給UIEventHandlers"""
        return self.ui_handlers.on_highlight_toggle()

    def on_undo(self):
        """委託給UIEventHandlers"""
        return self.ui_handlers.on_undo()

    def show_find_dialog(self):
        """委託給SearchHandlers"""
        return self.search_handlers.show_find_dialog()

    def show_find_replace_dialog(self):
        """委託給SearchHandlers"""
        return self.search_handlers.show_find_replace_dialog()

    def show_translation_settings(self):
        """委託給TranslationHandlers"""
        return self.translation_handlers.show_translation_settings()

    def on_show_file_type_config(self):
        """委託給ConfigHandlers"""
        return self.config_handlers.on_show_file_type_config()

    def show_about(self):
        """委託給ConfigHandlers"""
        return self.config_handlers.show_about()

    # ==================== 協調器特有的邏輯 ====================

    def _post_load_directory_actions(self):
        """加載目錄後的統一處理"""
        # 清空撤回歷史（加載新目錄時）
        self.ui_handlers.clear_undo_history()
        
        # 為所有新創建的標籤頁繫定事件
        files_data = self.state_manager.open_files_data
        logging.info(f"Post-load actions for {len(files_data)} files")
        for filepath, data in files_data.items():
            # 獲取對應的樹狀視圖並繫定事件
            try:
                # 嘗試獲取樹狀視圖並繫定事件
                tree = self.ui.get_tree_for_file(filepath)
                logging.info(f"Got tree for {filepath}: {tree}")
                if tree:
                    self._bind_tab_events(tree)
                else:
                    logging.warning(f"No tree found for {filepath}")
            except AttributeError as e:
                # 如果UI沒有提供get_tree_for_file方法，就跳過
                logging.warning(f"Cannot bind events for {filepath}: {e}")

        # 觸發標籤頁變化事件
        self.on_tab_changed()

    def _post_load_project_actions(self):
        """加載項目後的統一處理"""
        # 清空撤回歷史（加載新項目時）
        self.ui_handlers.clear_undo_history()
        
        # 為所有新創建的標籤頁繫定事件
        # 為所有新創建的標籤頁綁定事件
        files_data = self.state_manager.open_files_data
        for filepath, data in files_data.items():
            # 獲取對應的樹狀視圖並綁定事件
            # 這需要UI提供獲取樹狀視圖的方法
            pass

        # 觸發標籤頁變化事件
        self.on_tab_changed()

    def _update_menu_states(self):
        """更新菜單狀態"""
        has_files = bool(self.state_manager.open_files_data)
        # 這裡可以發布事件來更新菜單狀態
        # 或者直接調用UI方法（如果UI提供了相應的方法）

        # 暫時使用日誌記錄，實際實現時可以根據需要調整
        logging.debug(f"Menu states updated: has_files={has_files}")

    # ==================== 工具方法 ====================

    def _get_current_data(self):
        """獲取當前文件的數據（統一的工具方法）"""
        return self.state_manager.get_current_file_data()

    def _get_selected_entry(self):
        """獲取當前選中的條目（統一的工具方法）"""
        return self.state_manager.get_selected_entry()

    def _get_all_selected_entries(self):
        """獲取所有選中的條目（統一的工具方法）"""
        data = self._get_current_data()
        if not data:
            return []
        selected_ids = self.ui.get_all_selected_tree_item_ids()
        if not selected_ids:
            return []
        return [entry for entry in data if entry.id in selected_ids]
