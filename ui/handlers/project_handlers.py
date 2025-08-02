"""
項目管理相關的處理器
負責：保存工程、加載工程、重建解析器等項目管理功能
"""

import os
import logging

from .base_handler import BaseHandler
from core.events import (
    StatusBarUpdateEvent,
    InfoDialogEvent,
    ErrorDialogEvent,
    WarningDialogEvent,
)
from core.commands import (
    SaveProjectCommand,
    LoadProjectCommand,
)


class ProjectHandlers(BaseHandler):
    """處理所有項目管理相關的功能"""

    def register_commands(self, command_invoker):
        """註冊項目管理相關的命令"""
        command_invoker.register_command("save_project", SaveProjectCommand(self))
        command_invoker.register_command("load_project", LoadProjectCommand(self))

    def on_save_project(self):
        """處理保存工程文件的操作"""
        files_data = self.state_manager.open_files_data
        if not files_data:
            self.event_system.publish(
                WarningDialogEvent("無數據", "沒有可保存的工程數據。")
            )
            return

        file_path = self.state_manager.current_project_path

        # 如果沒有打開的工程，則彈出“另存為”對話框
        if not file_path:
            file_path = self.ui.ask_save_file_dialog(
                "保存工程文件", [("Class Editor Projects", "*.cep"), ("All Files", "*.*")]
            )

        if not file_path:
            return

        # 收集所有條目
        all_entries = []
        for file_data in files_data.values():
            all_entries.extend(file_data)

        try:
            success, message = self.project_service.save_project(file_path, all_entries)
            if success:
                # 更新狀態欄，而不是彈出對話框
                self.event_system.publish(StatusBarUpdateEvent(message))
                # 確保在“另存為”新工程後，更新當前的工程路徑
                if self.state_manager.current_project_path != file_path:
                    self.state_manager.set_project_path(file_path)
            else:
                self.event_system.publish(ErrorDialogEvent("保存失敗", message))
        except Exception as e:
            logging.error(f"Failed to save project: {e}", exc_info=True)
            self.event_system.publish(
                ErrorDialogEvent("保存失敗", f"保存工程文件時出錯: {e}")
            )

    def on_load_project(self):
        """處理加載工程文件的操作"""
        file_path = self.ui.ask_open_file_dialog(
            "加載工程文件", [("Class Editor Projects", "*.cep"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            # 清空所有舊數據，包括可能存在的工程路徑
            self.state_manager.clear_all_data()
            self.ui.clear_tree()
            string_data, metadata = self.project_service.load_project(file_path)
            if string_data is None:
                self.event_system.publish(
                    StatusBarUpdateEvent("加載失敗: 無法加載或解析工程文件。")
                )
                return

            # 重新組織數據結構
            loaded_files_data = {}
            for entry in string_data:
                if entry.file_name not in loaded_files_data:
                    loaded_files_data[entry.file_name] = []
                loaded_files_data[entry.file_name].append(entry)

            # 使用狀態管理器設置數據
            self.state_manager.set_files_data(loaded_files_data)

            # 重建解析器（對於.class文件）
            self._rebuild_parsers_for_loaded_data(loaded_files_data)

            # 重新創建標籤頁
            for filepath, data in loaded_files_data.items():
                self.ui.add_file_tab(filepath, data)
                # 注意：_bind_tab_events 需要在協調器中處理

            # 觸發標籤頁變化事件（需要通過協調器）
            # self.on_tab_changed()

            # 更新狀態欄
            self.event_system.publish(
                StatusBarUpdateEvent(
                    f"成功從 {os.path.basename(file_path)} 加載了 {metadata.get('total_entries', 'N/A')} 個條目。"
                )
            )

            # 設置當前工程路徑
            self.state_manager.set_project_path(file_path)

            # 設置當前工程路徑
            self.state_manager.set_project_path(file_path)

        except Exception as e:
            logging.error(f"Failed to load project: {e}", exc_info=True)
            self.event_system.publish(
                StatusBarUpdateEvent(f"加載失敗: {e}")
            )

    def _rebuild_parsers_for_loaded_data(self, loaded_files_data):
        """重建從項目文件加載的數據的 parser 引用"""
        from parsers import ClassParser

        failed_files = []
        success_count = 0

        for filepath, entries in loaded_files_data.items():
            if not entries:
                continue

            # 只處理 .class 文件
            if entries[0].file_type == ".class":
                try:
                    # 檢查文件是否存在
                    if not os.path.exists(filepath):
                        failed_files.append((filepath, f"文件不存在: {filepath}"))
                        continue

                    # 為此文件創建新的 parser
                    parser = ClassParser(filepath)

                    # 將 parser 引用注入到所有相關的 StringEntry 中
                    for entry in entries:
                        entry.parser_ref = parser

                    # 在 FileService 中註冊 parser
                    self.file_service.parsers[filepath] = parser

                    success_count += 1
                    logging.info(f"Successfully rebuilt parser for {filepath}")

                except Exception as e:
                    failed_files.append((filepath, str(e)))
                    logging.error(f"Failed to rebuild parser for {filepath}: {e}")

        # 只在有失敗時才顯示警告
        if failed_files:
            if success_count == 0:
                # 所有文件都失敗
                self.ui.show_warning_dialog(
                    "無法重建 Parser",
                    "無法為任何文件重建 parser。這些文件將無法保存。\n\n"
                    "可能原因：\n"
                    "- 原始 .class 文件已被移動或刪除\n"
                    "- 文件路徑已經改變\n\n"
                    "請嘗試重新加載原始文件目錄。",
                )
            else:
                # 部分失敗
                failed_names = [os.path.basename(fp) for fp, _ in failed_files[:3]]
                message = "部分文件無法重建 parser：\n\n"
                message += "\n".join(f"- {name}" for name in failed_names)
                if len(failed_files) > 3:
                    message += f"\n... 及其他 {len(failed_files) - 3} 個文件"
                message += f"\n\n成功: {success_count} 個文件\n失敗: {len(failed_files)} 個文件"

                logging.warning(message)
        else:
            logging.info(f"Successfully rebuilt parsers for all {success_count} files")
