"""
UI接口抽象 - 定義MainWindow的操作契約
讓EventHandlers依賴接口而非具體實現，提升解耦度和可測試性
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any
from core.models import StringEntry


class IMainWindow(ABC):
    """MainWindow的抽象接口，定義所有UI操作的契約"""

    # ==================== 數據展示相關 ====================

    @abstractmethod
    def clear_tree(self) -> None:
        """清空所有樹狀視圖內容"""
        pass

    @abstractmethod
    def add_file_tab(self, filepath: str, data: List[StringEntry]) -> Any:
        """添加文件標籤頁並返回樹狀視圖控件"""
        pass

    @abstractmethod
    def get_tree_for_file(self, filepath: str) -> Any:
        """獲取指定文件的樹狀視圖控件"""
        pass

    @abstractmethod
    def update_tree_item(self, item_id: int, translated_text: str) -> None:
        """更新樹狀視圖中指定項目的翻譯文本"""
        pass

    @abstractmethod
    def select_tree_items(self, item_ids: List[int]) -> None:
        """選中樹狀視圖中的指定項目列表"""
        pass

    # ==================== 編輯器相關 ====================

    @abstractmethod
    def update_editor_text(self, original: str, translated: str) -> None:
        """更新編輯器中的原文和譯文"""
        pass

    @abstractmethod
    def clear_editor_text(self) -> None:
        """清空編輯器中的所有文本"""
        pass

    @abstractmethod
    def get_translated_text(self) -> str:
        """獲取編輯器中的譯文內容"""
        pass

    # ==================== 高亮相關 ====================

    @abstractmethod
    def highlight_tree_row(self, item_id: int, highlight: bool) -> None:
        """設置樹狀視圖行的高亮狀態"""
        pass

    @abstractmethod
    def update_text_highlights(self, ranges: List[tuple[int, int]]) -> None:
        """更新文本編輯器中的高亮範圍"""
        pass

    # ==================== 狀態查詢相關 ====================

    @abstractmethod
    def get_current_filepath(self) -> Optional[str]:
        """獲取當前活動標籤頁的文件路徑"""
        pass

    @abstractmethod
    def get_selected_tree_item_id(self) -> Optional[int]:
        """獲取當前選中的樹狀視圖項目ID"""
        pass

    @abstractmethod
    def get_all_selected_tree_item_ids(self) -> List[int]:
        """獲取所有選中的樹狀視圖項目ID列表"""
        pass

    # ==================== 狀態欄和UI控制 ====================

    @abstractmethod
    def update_status_bar(self, status_data: Any) -> None:
        """更新狀態欄信息"""
        pass

    @abstractmethod
    def enable_file_operations(self) -> None:
        """啟用文件操作相關的UI控件"""
        pass

    @abstractmethod
    def disable_file_operations(self) -> None:
        """禁用文件操作相關的UI控件"""
        pass

    # ==================== 按鈕和控件狀態 ====================

    @abstractmethod
    def set_apply_button_state(self, enabled: bool) -> None:
        """設置應用修改按鈕的啟用狀態"""
        pass

    @abstractmethod
    def get_highlight_enabled(self) -> bool:
        """獲取高亮功能的啟用狀態"""
        pass

    # ==================== 對話框相關 ====================

    @abstractmethod
    def show_info_dialog(self, title: str, message: str) -> None:
        """顯示信息對話框"""
        pass

    @abstractmethod
    def show_warning_dialog(self, title: str, message: str) -> None:
        """顯示警告對話框"""
        pass

    @abstractmethod
    def show_error_dialog(self, title: str, message: str) -> None:
        """顯示錯誤對話框"""
        pass

    @abstractmethod
    def ask_save_file_dialog(
        self, title: str, filetypes: List[tuple[str, str]]
    ) -> Optional[str]:
        """顯示保存文件對話框，返回選中的文件路徑"""
        pass

    @abstractmethod
    def ask_open_file_dialog(
        self, title: str, filetypes: List[tuple[str, str]]
    ) -> Optional[str]:
        """顯示打開文件對話框，返回選中的文件路徑"""
        pass

    @abstractmethod
    def ask_directory_dialog(self, title: str) -> Optional[str]:
        """顯示選擇目錄對話框，返回選中的目錄路徑"""
        pass
