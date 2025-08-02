"""
文件操作相關的處理器
負責：加載目錄、保存文件、保存所有文件等文件操作
"""

import os

from .base_handler import BaseHandler
from core.events import (
    StatusBarUpdateEvent,
    InfoDialogEvent,
    ErrorDialogEvent,
    WarningDialogEvent,
)
from core.commands import (
    LoadDirectoryCommand,
    SaveFileCommand,
    SaveAllFilesCommand,
)


class FileOperationHandlers(BaseHandler):
    """處理所有文件操作相關的功能"""

    def register_commands(self, command_invoker):
        """註冊文件操作相關的命令"""
        command_invoker.register_command("load_directory", LoadDirectoryCommand(self))
        command_invoker.register_command("save_file", SaveFileCommand(self))
        command_invoker.register_command("save_all_files", SaveAllFilesCommand(self))

    def on_load_directory(self):
        """處理加載目錄的操作"""
        from core.events import StatusBarUpdateEvent
        
        self.event_system.publish(StatusBarUpdateEvent("正在選擇目錄..."))
        dir_path = self.ui.ask_directory_dialog("選擇包含文件的目錄")
        if not dir_path:
            self.event_system.publish(StatusBarUpdateEvent("已取消選擇目錄"))
            return

        try:
            self.event_system.publish(StatusBarUpdateEvent(f"正在掃描目錄: {dir_path}"))
            # 獲取目錄中按文件類型分組的文件
            files_by_type = self.file_service.get_files_by_type_in_directory(dir_path)

            if not any(files_by_type.values()):
                # 沒有找到任何支持的文件
                from parsers.parser_factory import get_parser_factory

                factory = get_parser_factory()
                supported_exts = ", ".join(factory.get_supported_extensions())
                self.event_system.publish(
                    InfoDialogEvent(
                        "未找到文件",
                        f"在指定目錄中沒有找到可加載的文件。\n\n支持的文件類型: {supported_exts}",
                    )
                )
                return

            # 如果只有一種文件類型且文件數量少於10個，直接加載
            total_files = sum(len(files) for files in files_by_type.values())
            non_empty_types = [
                file_type for file_type, files in files_by_type.items() if files
            ]

            if len(non_empty_types) == 1 and total_files <= 10:
                # 直接加載所有文件
                all_files = []
                for files in files_by_type.values():
                    all_files.extend(files)
                selected_files = all_files
            else:
                # 顯示文件類型選擇對話框
                from ..file_type_selector_dialog import FileTypeSelectorDialog

                dialog = FileTypeSelectorDialog(self.root, dir_path, files_by_type)
                selected_files = dialog.show()

                if not selected_files:
                    return  # 用戶取消了選擇

            # 清空所有舊數據，包括可能存在的工程路徑
            self.event_system.publish(StatusBarUpdateEvent("正在清空舊數據..."))
            self.state_manager.clear_all_data()
            self.ui.clear_tree()

            # 加載選中的文件
            self.event_system.publish(StatusBarUpdateEvent(f"正在加載 {len(selected_files)} 個文件..."))
            loaded_files_data = self.file_service.load_selected_files(selected_files)

            if not loaded_files_data:
                self.event_system.publish(
                    InfoDialogEvent("加載失敗", "選中的文件無法加載或不包含有效內容。")
                )
                return

            # 使用狀態管理器設置數據
            self.event_system.publish(StatusBarUpdateEvent("正在設置數據狀態..."))
            self.state_manager.set_files_data(loaded_files_data)

            self.event_system.publish(StatusBarUpdateEvent("正在創建標籤頁..."))
            for filepath, data in loaded_files_data.items():
                self.ui.add_file_tab(filepath, data)
                # 注意：_bind_tab_events 需要在協調器中處理

            # 觸發標籤頁變化事件（需要通過協調器）
            # self.on_tab_changed()

            # 發布狀態欄更新事件
            self.event_system.publish(
                StatusBarUpdateEvent(
                    f"成功從 {dir_path} 加載了 {len(loaded_files_data)} 個文件。"
                )
            )

        except Exception as e:
            # 發布錯誤對話框事件
            self.event_system.publish(
                ErrorDialogEvent("加載失敗", f"加載目錄時出錯: {e}")
            )

    def on_save_file(self):
        """處理保存當前文件的操作"""
        filepath = self.ui.get_current_filepath()
        data = self._get_current_data()

        if not filepath or not data:
            self.event_system.publish(
                WarningDialogEvent("無數據", "沒有可保存的數據。")
            )
            return

        try:
            backup_path, count = self.file_service.save_file(filepath, data)
            self.event_system.publish(
                InfoDialogEvent(
                    "保存成功",
                    f"文件 '{os.path.basename(filepath)}' 已成功保存！\n共更新 {count} 個字符串。\n備份文件位於: {backup_path}",
                )
            )
        except RuntimeError as e:
            if "No parser available" in str(e):
                self.event_system.publish(
                    WarningDialogEvent(
                        "無法保存",
                        f"無法保存文件 '{os.path.basename(filepath)}'。\n\n"
                        f"這可能是因為：\n"
                        f"1. 數據是從項目文件加載的，原始 .class 文件不存在\n"
                        f"2. 文件路徑已經改變\n\n"
                        f"請嘗試：\n"
                        f"- 重新加載原始 .class 文件目錄\n"
                        f"- 或者使用『保存工程...』保存翻譯進度",
                    )
                )
            else:
                self.event_system.publish(
                    ErrorDialogEvent("保存失敗", f"保存文件時出錯: {e}")
                )
        except Exception as e:
            self.event_system.publish(
                ErrorDialogEvent("保存失敗", f"保存文件時出錯: {e}")
            )

    def on_save_all_files(self):
        """處理保存所有文件的操作"""
        files_data = self.state_manager.open_files_data
        if not files_data:
            self.event_system.publish(
                WarningDialogEvent("無數據", "沒有可保存的數據。")
            )
            return

        total_updates = 0
        total_files = 0
        failed_files = []

        for filepath, data in files_data.items():
            try:
                _, count = self.file_service.save_file(filepath, data)
                if count > 0:
                    total_updates += count
                    total_files += 1
            except RuntimeError as e:
                if "No parser available" in str(e):
                    failed_files.append(os.path.basename(filepath))
                else:
                    self.event_system.publish(
                        ErrorDialogEvent("保存失敗", f"保存文件 {filepath} 時出錯: {e}")
                    )
                    return
            except Exception as e:
                self.event_system.publish(
                    ErrorDialogEvent("保存失敗", f"保存文件 {filepath} 時出錯: {e}")
                )
                return

        # 構建結果消息
        if failed_files:
            if total_files == 0:
                # 所有文件都失敗
                self.event_system.publish(
                    WarningDialogEvent(
                        "無法保存",
                        "無法保存任何文件。\n\n"
                        "失敗的文件：\n"
                        + "\n".join(f"- {name}" for name in failed_files[:5])
                        + (
                            f"\n... 及其他 {len(failed_files) - 5} 個文件"
                            if len(failed_files) > 5
                            else ""
                        )
                        + "\n\n這可能是因為數據是從項目文件加載的。\n請嘗試重新加載原始文件目錄。",
                    )
                )
            else:
                # 部分成功
                self.event_system.publish(
                    InfoDialogEvent(
                        "部分保存成功",
                        f"成功保存 {total_files} 個文件，共更新 {total_updates} 個字符串。\n\n"
                        f"但有 {len(failed_files)} 個文件無法保存：\n"
                        + "\n".join(f"- {name}" for name in failed_files[:3])
                        + (
                            f"\n... 及其他 {len(failed_files) - 3} 個文件"
                            if len(failed_files) > 3
                            else ""
                        ),
                    )
                )
        else:
            # 全部成功
            self.event_system.publish(
                InfoDialogEvent(
                    "全部保存成功",
                    f"成功保存 {total_files} 個文件，共更新 {total_updates} 個字符串。",
                )
            )
