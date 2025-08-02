"""事件處理器 - 重構版本

這個文件現在使用協調器模式來管理拆分後的Handler，
保持與原EventHandlers完全相同的接口，確保向後兼容性。
"""

import os
import re
import tkinter as tk
import logging
import concurrent.futures
from typing import List, Optional

from core.services import (
    FileService,
    TranslationService,
    HighlightingService,
    ProjectService,
)
from core.state import AppStateManager
from core.models import StringEntry
from core.events import (
    EditorTextUpdateEvent,
    StatusBarUpdateEvent,
    InfoDialogEvent,
    ErrorDialogEvent,
    WarningDialogEvent,
    TreeItemUpdateEvent,
    TreeItemHighlightEvent,
    EditorClearEvent,
    ApplyButtonStateEvent,
    TextHighlightUpdateEvent,
    TreeSelectionEvent,
)
from ui.settings_dialog import SettingsDialog
from ui.find_dialog import FindDialog
from ui.find_replace_dialog import FindReplaceDialog
from .interfaces.imain_window import IMainWindow
from .handlers import EventHandlerCoordinator


class EventHandlers:
    """
    事件處理器 - 重構版本

    這個類現在是EventHandlerCoordinator的包裝器，
    保持與原EventHandlers完全相同的接口，確保向後兼容性。

    所有實際的處理邏輯都已經拆分到專門的Handler類中，
    通過協調器統一管理。
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
        # 創建協調器實例，它會管理所有拆分後的Handler
        self._coordinator = EventHandlerCoordinator(
            root,
            ui,
            state_manager,
            file_service,
            translation_service,
            highlighting_service,
            project_service,
        )

        # 為了向後兼容，暴露協調器的屬性
        self.root = self._coordinator.root
        self.ui = self._coordinator.ui
        self.state_manager = self._coordinator.state_manager
        self.file_service = self._coordinator.file_service
        self.translation_service = self._coordinator.translation_service
        self.highlighting_service = self._coordinator.highlighting_service
        self.project_service = self._coordinator.project_service
        self.event_system = self._coordinator.event_system
        self.command_invoker = self._coordinator.command_invoker

        logging.info("EventHandlers initialized using coordinator pattern")

    # ==================== 向後兼容的方法委託 ====================
    # 所有方法都委託給協調器，保持與原EventHandlers相同的接口

    def _register_commands(self):
        """註冊所有UI命令（已由協調器處理）"""
        # 協調器已經處理了命令註冊，這裡不需要做任何事情
        pass

    def get_command_handler(self, command_name: str):
        """獲取命令處理器，用於UI繫定"""
        return self._coordinator.get_command_handler(command_name)

    # set_handlers 方法已移除，不再需要，因為現在使用命令模式

    def _bind_tab_events(self, tree):
        """繫定特定 treeview 在標籤頁中的事件"""
        return self._coordinator._bind_tab_events(tree)

    def _rebuild_parsers_for_loaded_data(self, loaded_files_data):
        """重建從項目文件加載的數據的 parser 引用。"""
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

    def _get_current_data(self) -> Optional[List[StringEntry]]:
        return self.state_manager.get_current_file_data()

    def _get_selected_entry(self) -> Optional[StringEntry]:
        return self.state_manager.get_selected_entry()

    def _get_all_selected_entries(self) -> List[StringEntry]:
        data = self._get_current_data()
        if not data:
            return []
        selected_ids = self.ui.get_all_selected_tree_item_ids()
        if not selected_ids:
            return []
        return [entry for entry in data if entry.id in selected_ids]

    def _update_highlights_for_entry(self, entry: StringEntry):
        if not self.highlighting_service.enabled:
            self.event_system.publish(TextHighlightUpdateEvent([]))
            self.event_system.publish(TreeItemHighlightEvent(entry.id, False))
            return

        is_valid = self.highlighting_service.is_valid(entry.translated)
        ranges = self.highlighting_service.get_invalid_ranges(entry.translated)
        self.event_system.publish(TextHighlightUpdateEvent(ranges))
        self.event_system.publish(TreeItemHighlightEvent(entry.id, not is_valid))

    def _update_all_highlights_for_current_tab(self):
        # 確保狀態管理器有當前標籤頁的信息
        current_filepath = self.ui.get_current_filepath()
        if current_filepath:
            # 更新狀態管理器的當前文件選擇（但不改變條目選擇）
            current_entry_id = self.state_manager.current_selected_entry_id
            self.state_manager.set_current_selection(current_filepath, current_entry_id)

        current_data = self._get_current_data()
        if not current_data:
            return

        # First, update all rows in the treeview
        enabled = self.highlighting_service.enabled
        for entry in current_data:
            if not enabled:
                self.event_system.publish(TreeItemHighlightEvent(entry.id, False))
            else:
                is_valid = self.highlighting_service.is_valid(entry.translated)
                self.event_system.publish(
                    TreeItemHighlightEvent(entry.id, not is_valid)
                )

        # Then, update the editor for the currently selected entry
        selected_entry = self._get_selected_entry()
        if selected_entry:
            # This will also correctly handle the case where highlighting is disabled
            self._update_highlights_for_entry(selected_entry)
        else:
            # If nothing is selected, ensure the editor highlights are cleared
            self.event_system.publish(TextHighlightUpdateEvent([]))

    def on_load_directory(self):
        dir_path = self.ui.ask_directory_dialog("選擇包含文件的目錄")
        if not dir_path:
            return

        try:
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
                from .file_type_selector_dialog import FileTypeSelectorDialog

                dialog = FileTypeSelectorDialog(self.root, dir_path, files_by_type)
                selected_files = dialog.show()

                if not selected_files:
                    return  # 用戶取消了選擇

            # 清空現有樹狀視圖
            self.ui.clear_tree()

            # 加載選中的文件
            loaded_files_data = self.file_service.load_selected_files(selected_files)

            if not loaded_files_data:
                self.event_system.publish(
                    InfoDialogEvent("加載失敗", "選中的文件無法加載或不包含有效內容。")
                )
                return

            # 使用狀態管理器設置數據
            self.state_manager.set_files_data(loaded_files_data)

            for filepath, data in loaded_files_data.items():
                tree = self.ui.add_file_tab(filepath, data)
                self._bind_tab_events(tree)

            self.on_tab_changed()
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
                        ErrorDialogEvent("保存失敗", f"批量保存文件時出錯: {e}")
                    )
                    return
            except Exception as e:
                self.event_system.publish(
                    ErrorDialogEvent("保存失敗", f"批量保存文件時出錯: {e}")
                )
                return

        # 顯示結果
        if failed_files:
            message = f"部分成功：成功保存 {total_files} 個文件，共更新 {total_updates} 個字符串。\n\n"
            message += f"無法保存的文件 ({len(failed_files)} 個)：\n"
            message += "\n".join(f"- {f}" for f in failed_files[:5])  # 只顯示前5個
            if len(failed_files) > 5:
                message += f"\n... 及其他 {len(failed_files) - 5} 個文件"
            message += (
                "\n\n這些文件可能是從項目文件加載的。請重新加載原始 .class 文件目錄。"
            )
            self.event_system.publish(WarningDialogEvent("部分保存成功", message))
        else:
            self.event_system.publish(
                InfoDialogEvent(
                    "全部保存成功",
                    f"成功保存 {total_files} 個文件，共更新 {total_updates} 個字符串。",
                )
            )

    def on_tree_select(self, event=None):
        # 更新狀態管理器中的選中狀態
        current_filepath = self.ui.get_current_filepath()
        selected_id = self.ui.get_selected_tree_item_id()
        self.state_manager.set_current_selection(current_filepath, selected_id)

        selected_entry = self.state_manager.get_selected_entry()
        if not selected_entry:
            self.event_system.publish(EditorClearEvent())
            self.event_system.publish(ApplyButtonStateEvent(False))
            return

        self.event_system.publish(
            EditorTextUpdateEvent(selected_entry.original, selected_entry.translated)
        )
        self._update_highlights_for_entry(selected_entry)
        # After loading new text, the editor is clean, so disable the apply button.
        self.ui.translated_text.edit_modified(False)
        self.event_system.publish(ApplyButtonStateEvent(False))

    def on_text_changed(self, event=None):
        selected_entry = self.state_manager.get_selected_entry()
        if not selected_entry:
            return

        new_text = self.ui.translated_text.get("1.0", tk.END).strip()
        if selected_entry.translated != new_text:
            # 使用狀態管理器更新翻譯
            self.state_manager.update_entry_translation(selected_entry.id, new_text)
            self.event_system.publish(TreeItemUpdateEvent(selected_entry.id, new_text))
            self._update_highlights_for_entry(selected_entry)
        # After applying changes, reset the modified flag, which will trigger the <<Modified>> event
        # and call on_translated_text_modified to disable the button.
        self.ui.translated_text.edit_modified(False)

    def on_translated_text_modified(self, event=None):
        """啟用或禁用 'Apply' 按鈕，基於文本小工具的修改狀態。"""
        modified = self.ui.translated_text.edit_modified()
        self.event_system.publish(ApplyButtonStateEvent(modified))

    def on_translated_text_changed_realtime(self, event=None):
        """實時處理譯文文本變化，更新高亮標記。"""
        selected_entry = self.state_manager.get_selected_entry()
        if not selected_entry:
            return

        # 獲取當前編輯器中的文本
        current_text = self.ui.translated_text.get("1.0", tk.END).strip()

        # 如果高亮功能啟用，實時更新高亮
        if self.highlighting_service.enabled and current_text:
            ranges = self.highlighting_service.get_invalid_ranges(current_text)
            self.event_system.publish(TextHighlightUpdateEvent(ranges))
        else:
            # 清除高亮
            self.event_system.publish(TextHighlightUpdateEvent([]))

    def on_save_project(self):
        all_entries = self.state_manager.get_all_entries()
        if not all_entries:
            self.event_system.publish(
                WarningDialogEvent("無數據", "沒有可保存的工程數據。")
            )
            return

        file_path = self.ui.ask_save_file_dialog(
            "保存工程文件", [("Class Editor Projects", "*.cep"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        success, message = self.project_service.save_project(file_path, all_entries)
        if success:
            self.event_system.publish(InfoDialogEvent("工程已保存", message))
        else:
            self.event_system.publish(ErrorDialogEvent("保存失敗", message))

    def on_load_project(self):
        file_path = self.ui.ask_open_file_dialog(
            "加載工程文件", [("Class Editor Projects", "*.cep"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        string_data, metadata = self.project_service.load_project(file_path)
        if string_data is None:
            self.event_system.publish(
                ErrorDialogEvent("加載失敗", "無法加載或解析工程文件。")
            )
            return

        # Clear current UI and data
        self.ui.clear_tree()

        # 重新組織數據結構
        loaded_files_data = {}
        for entry in string_data:
            if entry.file_name not in loaded_files_data:
                loaded_files_data[entry.file_name] = []
            loaded_files_data[entry.file_name].append(entry)

        # 使用狀態管理器設置數據
        self.state_manager.set_files_data(loaded_files_data)

        # 嘗試重建 parser 引用以支持保存操作
        # 現在 file_name 存儲完整路徑，應該能找到原始文件
        self._rebuild_parsers_for_loaded_data(loaded_files_data)

        # Re-create tabs
        for filepath, data in loaded_files_data.items():
            tree = self.ui.add_file_tab(filepath, data)
            self._bind_tab_events(tree)

        self.on_tab_changed()
        self.event_system.publish(
            StatusBarUpdateEvent(
                f"成功從 {os.path.basename(file_path)} 加載了 {metadata.get('total_entries', 'N/A')} 個條目。"
            )
        )
        self.event_system.publish(InfoDialogEvent("加載成功", "工程文件已成功加載。"))

    def on_tab_changed(self, event=None):
        self._update_all_highlights_for_current_tab()
        self.on_tree_select()

    def on_highlight_toggle(self):
        """Toggles the highlighting service and refreshes the UI."""
        is_enabled = self.ui.get_highlight_enabled()
        self.highlighting_service.enabled = is_enabled
        logging.info(f"Highlighting toggled: {'Enabled' if is_enabled else 'Disabled'}")
        self._update_all_highlights_for_current_tab()

    def on_translate(self):
        selected_entries = self._get_all_selected_entries()
        if not selected_entries:
            self.event_system.publish(
                InfoDialogEvent("無選擇", "請先在列表中選擇一個或多個字符串。")
            )
            return

        tasks_to_run = [
            entry
            for entry in selected_entries
            if entry.original and entry.original.strip()
        ]
        if not tasks_to_run:
            self.event_system.publish(StatusBarUpdateEvent("沒有需要翻譯的有效項目。"))
            return

        total = len(tasks_to_run)
        self.processed_count = 0
        max_workers = self.translation_service.get_max_concurrent_requests()

        self.event_system.publish(
            StatusBarUpdateEvent(
                f"已提交 {total} 個翻譯任務，使用 {max_workers} 個並發線程..."
            )
        )
        self.root.update_idletasks()

        # 如果是批量操作，立即清空編輯器
        if len(selected_entries) > 1:
            self.event_system.publish(EditorClearEvent())
            self.event_system.publish(ApplyButtonStateEvent(False))

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        for entry in tasks_to_run:
            future = executor.submit(self.translation_service.translate, entry.original)
            future.add_done_callback(
                lambda f, e=entry: self._on_translation_complete(f, e)
            )

        executor.shutdown(wait=False)

    def _on_translation_complete(self, future, entry: StringEntry):
        """Callback executed when a translation future is done. THREAD-SAFE UI UPDATES."""
        try:
            translated_text = future.result()
            # Schedule UI updates on the main thread
            self.root.after_idle(
                self._update_ui_after_translation, entry, translated_text
            )
        except Exception as e:
            logging.error(f"Translation for '{entry.original[:20]}...' failed: {e}")
            self.root.after_idle(
                lambda msg=f"翻譯失敗: {entry.original[:20]}...": self.event_system.publish(
                    StatusBarUpdateEvent(msg)
                )
            )

    def _update_ui_after_translation(self, entry: StringEntry, translated_text: str):
        """Performs the actual UI update on the main thread."""
        self.processed_count += 1
        total = len(
            [
                e
                for e in self._get_all_selected_entries()
                if e.original and e.original.strip()
            ]
        )

        if translated_text != entry.translated:
            self.state_manager.update_entry_translation(entry.id, translated_text)
            self.event_system.publish(TreeItemUpdateEvent(entry.id, translated_text))
            if self.highlighting_service.enabled:
                is_valid = self.highlighting_service.is_valid(translated_text)
                self.event_system.publish(
                    TreeItemHighlightEvent(entry.id, not is_valid)
                )

        # For single translations, update the editor as well
        if total == 1:
            self.event_system.publish(
                EditorTextUpdateEvent(entry.original, entry.translated)
            )
            self._update_highlights_for_entry(entry)

        self.event_system.publish(
            StatusBarUpdateEvent(f"翻譯進度: {self.processed_count}/{total}")
        )
        if self.processed_count == total:
            self.event_system.publish(
                StatusBarUpdateEvent(f"全部 {total} 個翻譯任務已完成。")
            )

    def on_translate_all(self):
        entries_to_translate = self._get_all_selected_entries()
        if not entries_to_translate:
            self.event_system.publish(
                InfoDialogEvent("無選擇", "請先在列表中選擇一個或多個字符串。")
            )
            return

        total = len(entries_to_translate)
        translated_count = 0
        self.event_system.publish(
            StatusBarUpdateEvent(f"開始批量翻譯 {total} 個項目...")
        )
        self.root.update_idletasks()

        try:
            for i, entry in enumerate(entries_to_translate):
                self.event_system.publish(
                    StatusBarUpdateEvent(
                        f"正在翻譯 ({i + 1}/{total}): {entry.original[:20]}..."
                    )
                )
                if entry.original:
                    translated_text = self.translation_service.translate(entry.original)
                    if translated_text != entry.translated:
                        entry.translated = translated_text
                        self.event_system.publish(
                            TreeItemUpdateEvent(entry.id, translated_text)
                        )
                        translated_count += 1
                self.root.update_idletasks()  # Allow UI to update

            self._update_all_highlights_for_current_tab()
            self.event_system.publish(
                StatusBarUpdateEvent(
                    f"批量翻譯完成。成功翻譯 {translated_count} 個字符串。"
                )
            )
            self.event_system.publish(
                InfoDialogEvent("翻譯完成", f"成功翻譯 {translated_count} 個字符串。")
            )

        except Exception as e:
            logging.error(f"Batch translation failed: {e}", exc_info=True)
            self.event_system.publish(StatusBarUpdateEvent(f"批量翻譯時出錯: {e}"))
            self.event_system.publish(
                ErrorDialogEvent("翻譯失敗", f"批量翻譯時出錯: {e}")
            )

    def show_find_dialog(self):
        current_data = self._get_current_data()
        if not current_data:
            self.event_system.publish(InfoDialogEvent("無數據", "沒有可供查找的數據。"))
            return

        dialog = FindDialog(self.root)
        if not dialog.result or not dialog.result.get("find_text"):
            return

        params = dialog.result
        find_text = params["find_text"]
        match_case = params["match_case"]
        search_in = params["search_in"]

        flags = 0 if match_case else re.IGNORECASE
        found_ids = []

        for entry in current_data:
            targets = []
            if search_in in ("translated", "both"):
                targets.append(entry.translated)
            if search_in == "both":
                targets.append(entry.original)

            for target_text in targets:
                if re.search(find_text, target_text, flags):
                    found_ids.append(entry.id)
                    break  # Move to the next entry once found

        if found_ids:
            self.event_system.publish(TreeSelectionEvent(found_ids))
            self.event_system.publish(
                StatusBarUpdateEvent(f"找到了 {len(found_ids)} 個匹配項。")
            )
        else:
            self.event_system.publish(StatusBarUpdateEvent(f"未找到 '{find_text}'。"))

    def show_find_replace_dialog(self):
        if not self._get_current_data():
            self.event_system.publish(InfoDialogEvent("無數據", "沒有可供操作的數據。"))
            return

        dialog = FindReplaceDialog(self.root)
        if not dialog.result or not dialog.result.get("find_text"):
            return

        params = dialog.result
        action = params["action"]
        find_text = params["find_text"]
        replace_text = params["replace_text"]
        match_case = params["match_case"]

        entries_to_process = []
        if action == "replace_all":
            entries_to_process = self._get_current_data()
        elif action == "replace_selection":
            entries_to_process = self._get_all_selected_entries()
            if not entries_to_process:
                self.event_system.publish(
                    InfoDialogEvent("無選擇", "請先在列表中選擇要替換的條目。")
                )
                return

        count = 0
        flags = 0 if match_case else re.IGNORECASE

        for entry in entries_to_process:
            # Use re.sub for case-insensitive replacement
            new_translated, num_subs = re.subn(
                find_text, replace_text, entry.translated, flags=flags
            )

            if num_subs > 0:
                count += 1
                entry.translated = new_translated
                self.event_system.publish(TreeItemUpdateEvent(entry.id, new_translated))

        self.event_system.publish(
            StatusBarUpdateEvent(
                f"在 {len(entries_to_process)} 個條目中，共替換了 {count} 處。"
            )
        )
        self._update_all_highlights_for_current_tab()  # Refresh highlights after changes
        # Also refresh the editor if the selected item was changed
        selected_entry = self._get_selected_entry()
        if selected_entry and selected_entry in entries_to_process:
            self.event_system.publish(
                EditorTextUpdateEvent(
                    selected_entry.original, selected_entry.translated
                )
            )

    def show_translation_settings(self):
        """Opens the settings dialog to configure translation options."""
        # The SettingsDialog now takes the translation_service directly
        # and handles its own logic for saving settings.
        SettingsDialog(self.root, self.translation_service)
        # The dialog is modal, so the code will wait here until it's closed.

    def on_show_file_type_config(self):
        """顯示文件類型配置對話框"""
        from .file_type_config_dialog import FileTypeConfigDialog

        dialog = FileTypeConfigDialog(self.root)
        result = dialog.show()

        if result:
            # 配置已更新，刷新解析器工廠
            from parsers.parser_factory import get_parser_factory

            factory = get_parser_factory()
            factory.refresh_config()

            self.event_system.publish(StatusBarUpdateEvent("文件類型配置已更新"))

    def show_about(self):
        """顯示關於對話框。"""
        self.event_system.publish(
            InfoDialogEvent(
                "About",
                "Class Editor\n\n為 STK-MIDP 的漢化而設計。\n使用內建的 Google 翻譯，讓您以更多的精力放在『翻譯的潤色』和『遊戲的測試』上。\n\n這個程式使用 Claude 和 Gemini 協作開發，如果您能喜歡，我不勝感激 ^_^\n\n如果您在使用過程中發現任何問題，請告訴我。\n\nEMAIL: magsticwind@gmail.com",
            )
        )
