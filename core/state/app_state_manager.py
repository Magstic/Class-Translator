"""
應用狀態管理器 - 集中管理應用的所有狀態數據
實現觀察者模式，支持狀態變化通知
"""

import logging
from typing import Dict, List, Callable, Any, Optional
from core.models import StringEntry


class AppStateManager:
    """集中管理應用狀態的核心類"""

    def __init__(self):
        # 核心數據狀態
        self._open_files_data: Dict[str, List[StringEntry]] = {}
        self._current_selected_file: Optional[str] = None
        self._current_project_path: Optional[str] = None
        self._current_selected_entry_id: Optional[int] = None

        # 觀察者列表 - 用於通知狀態變化
        self._observers: Dict[str, List[Callable]] = {
            "files_loaded": [],
            "file_data_changed": [],
            "selection_changed": [],
            "entry_modified": [],
            "files_cleared": [],
        }

        logging.info("AppStateManager initialized")

    # ==================== 數據訪問方法 ====================

    @property
    def open_files_data(self) -> Dict[str, List[StringEntry]]:
        """獲取所有打開文件的數據"""
        return self._open_files_data.copy()

    @property
    def current_project_path(self) -> Optional[str]:
        """獲取當前工程文件路徑"""
        return self._current_project_path

    @property
    def current_selected_file(self) -> Optional[str]:
        """獲取當前選中的文件路徑"""
        return self._current_selected_file

    @property
    def current_selected_entry_id(self) -> Optional[int]:
        """獲取當前選中的條目ID"""
        return self._current_selected_entry_id

    def get_file_data(self, filepath: str) -> Optional[List[StringEntry]]:
        """獲取指定文件的數據"""
        return self._open_files_data.get(filepath)

    def get_current_file_data(self) -> Optional[List[StringEntry]]:
        """獲取當前選中文件的數據"""
        if self._current_selected_file:
            return self._open_files_data.get(self._current_selected_file)
        return None

    def set_project_path(self, path: Optional[str]):
        """設置當前工程文件路徑"""
        self._current_project_path = path
        logging.info(f"Current project path set to: {path}")

    def get_selected_entry(self) -> Optional[StringEntry]:
        """獲取當前選中的條目"""
        current_data = self.get_current_file_data()
        if not current_data or self._current_selected_entry_id is None:
            return None

        for entry in current_data:
            if entry.id == self._current_selected_entry_id:
                return entry
        return None

    def get_all_entries(self) -> List[StringEntry]:
        """獲取所有文件的所有條目"""
        all_entries = []
        for file_data in self._open_files_data.values():
            all_entries.extend(file_data)
        return all_entries

    # ==================== 狀態修改方法 ====================

    def set_files_data(self, files_data: Dict[str, List[StringEntry]]):
        """設置文件數據（通常用於加載文件或項目）"""
        self._open_files_data = files_data.copy()
        self._current_selected_file = None
        self._current_selected_entry_id = None

        logging.info(f"Files data set: {len(files_data)} files loaded")
        self._notify_observers("files_loaded", files_data)

    def add_file_data(self, filepath: str, data: List[StringEntry]):
        """添加單個文件的數據"""
        self._open_files_data[filepath] = data
        logging.info(f"File data added: {filepath}")
        self._notify_observers(
            "file_data_changed", {"filepath": filepath, "data": data, "action": "added"}
        )

    def remove_file_data(self, filepath: str):
        """移除文件數據"""
        if filepath in self._open_files_data:
            del self._open_files_data[filepath]

            # 如果移除的是當前選中的文件，清除選中狀態
            if self._current_selected_file == filepath:
                self._current_selected_file = None
                self._current_selected_entry_id = None
                self._notify_observers(
                    "selection_changed", {"file": None, "entry_id": None}
                )

            logging.info(f"File data removed: {filepath}")
            self._notify_observers(
                "file_data_changed", {"filepath": filepath, "action": "removed"}
            )

    def clear_all_data(self):
        """清空所有數據，包括文件和工程路徑"""
        self._open_files_data.clear()
        self._current_selected_file = None
        self._current_project_path = None
        self._current_selected_entry_id = None

        logging.info("All application state data cleared")
        self._notify_observers("files_cleared", {})

    def set_current_selection(
        self, filepath: Optional[str], entry_id: Optional[int] = None
    ):
        """設置當前選中的文件和條目"""
        old_file = self._current_selected_file
        old_entry_id = self._current_selected_entry_id

        self._current_selected_file = filepath
        self._current_selected_entry_id = entry_id

        # 只有當選擇真正改變時才通知
        if old_file != filepath or old_entry_id != entry_id:
            logging.debug(f"Selection changed: file={filepath}, entry_id={entry_id}")
            self._notify_observers(
                "selection_changed",
                {
                    "file": filepath,
                    "entry_id": entry_id,
                    "old_file": old_file,
                    "old_entry_id": old_entry_id,
                },
            )

    def update_entry_translation(self, entry_id: int, new_translation: str) -> bool:
        """更新條目的翻譯內容"""
        current_data = self.get_current_file_data()
        if not current_data:
            return False

        for entry in current_data:
            if entry.id == entry_id:
                old_translation = entry.translated
                entry.translated = new_translation

                logging.debug(f"Entry {entry_id} translation updated")
                self._notify_observers(
                    "entry_modified",
                    {
                        "entry_id": entry_id,
                        "old_translation": old_translation,
                        "new_translation": new_translation,
                        "entry": entry,
                    },
                )
                return True
        return False

    # ==================== 觀察者模式實現 ====================

    def subscribe(self, event_type: str, callback: Callable):
        """訂閱狀態變化事件"""
        if event_type in self._observers:
            self._observers[event_type].append(callback)
            logging.debug(f"Observer subscribed to {event_type}")
        else:
            logging.warning(f"Unknown event type: {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable):
        """取消訂閱狀態變化事件"""
        if event_type in self._observers and callback in self._observers[event_type]:
            self._observers[event_type].remove(callback)
            logging.debug(f"Observer unsubscribed from {event_type}")

    def _notify_observers(self, event_type: str, data: Any):
        """通知所有訂閱者"""
        if event_type in self._observers:
            for callback in self._observers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logging.error(f"Error in observer callback for {event_type}: {e}")

    # ==================== 統計和查詢方法 ====================

    def has_open_files(self) -> bool:
        """檢查是否有打開的文件"""
        return len(self._open_files_data) > 0

    def get_statistics(self) -> Dict[str, Any]:
        """獲取應用狀態統計信息"""
        total_entries = sum(len(data) for data in self._open_files_data.values())
        file_types = {}

        for data in self._open_files_data.values():
            for entry in data:
                file_type = entry.file_type
                file_types[file_type] = file_types.get(file_type, 0) + 1

        return {
            "total_files": len(self._open_files_data),
            "total_entries": total_entries,
            "file_types": file_types,
            "current_file": self._current_selected_file,
            "current_entry_id": self._current_selected_entry_id,
        }
