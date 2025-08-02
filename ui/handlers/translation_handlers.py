"""
翻譯相關的處理器
負責：單個翻譯、批量翻譯、翻譯設置等翻譯功能
"""

import logging
import concurrent.futures

from .base_handler import BaseHandler
from core.models import StringEntry
from core.events import (
    StatusBarUpdateEvent,
    InfoDialogEvent,
    ErrorDialogEvent,
    TreeItemUpdateEvent,
    TreeItemHighlightEvent,
    EditorTextUpdateEvent,
    TextHighlightUpdateEvent,
)
from core.commands import (
    TranslateCommand,
    TranslateAllCommand,
    ShowTranslationSettingsCommand,
)


class TranslationHandlers(BaseHandler):
    """處理所有翻譯相關的功能"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processed_count = 0  # 用於批量翻譯進度跟踪

    def register_commands(self, command_invoker):
        """註冊翻譯相關的命令"""
        command_invoker.register_command("translate", TranslateCommand(self))
        command_invoker.register_command("translate_all", TranslateAllCommand(self))
        command_invoker.register_command(
            "show_translation_settings", ShowTranslationSettingsCommand(self)
        )

    def on_translate(self):
        """處理單個條目翻譯"""
        selected_entry = self._get_selected_entry()
        if not selected_entry:
            self.event_system.publish(
                InfoDialogEvent("無選擇", "請先在列表中選擇一個字符串。")
            )
            return

        self.event_system.publish(StatusBarUpdateEvent("正在翻譯..."))

        try:
            translated_text = self.translation_service.translate(
                selected_entry.original
            )

            # 更新狀態管理器中的翻譯
            self.state_manager.update_entry_translation(
                selected_entry.id, translated_text
            )

            # 發布UI更新事件
            self.event_system.publish(
                TreeItemUpdateEvent(selected_entry.id, translated_text)
            )
            self.event_system.publish(
                EditorTextUpdateEvent(selected_entry.original, translated_text)
            )

            # 更新高亮（通過事件系統）
            if self.highlighting_service.enabled:
                is_valid = self.highlighting_service.is_valid(translated_text)
                ranges = self.highlighting_service.get_invalid_ranges(translated_text)
                self.event_system.publish(TextHighlightUpdateEvent(ranges))
                self.event_system.publish(
                    TreeItemHighlightEvent(selected_entry.id, not is_valid)
                )

            self.event_system.publish(StatusBarUpdateEvent("翻譯完成。"))

        except Exception as e:
            logging.error(f"Translation failed: {e}", exc_info=True)
            self.event_system.publish(StatusBarUpdateEvent(f"翻譯錯誤: {e}"))
            self.event_system.publish(ErrorDialogEvent("翻譯失敗", f"翻譯時出錯: {e}"))

    def on_translate_all(self):
        """處理批量翻譯"""
        entries_to_translate = self._get_all_selected_entries()
        if not entries_to_translate:
            self.event_system.publish(
                InfoDialogEvent("無選擇", "請先在列表中選擇一個或多個字符串。")
            )
            return

        # 過濾出有原文的條目
        entries_to_translate = [
            entry
            for entry in entries_to_translate
            if entry.original and entry.original.strip()
        ]

        if not entries_to_translate:
            self.event_system.publish(
                InfoDialogEvent("無有效選擇", "選中的條目中沒有有效的原文可供翻譯。")
            )
            return

        total = len(entries_to_translate)
        self.processed_count = 0

        self.event_system.publish(
            StatusBarUpdateEvent(f"開始批量翻譯 {total} 個項目...")
        )

        # 使用線程池進行並發翻譯
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.translation_service.get_max_concurrent_requests()
        ) as executor:
            # 提交所有翻譯任務
            future_to_entry = {
                executor.submit(
                    self.translation_service.translate, entry.original
                ): entry
                for entry in entries_to_translate
            }

            # 處理完成的翻譯
            for future in concurrent.futures.as_completed(future_to_entry):
                entry = future_to_entry[future]
                try:
                    # 在主線程中更新UI
                    self.root.after(0, self._on_translation_complete, future, entry)
                except Exception as e:
                    logging.error(f"Translation failed for entry {entry.id}: {e}")
                    self.root.after(0, self._on_translation_error, entry, str(e))

    def _on_translation_complete(self, future, entry: StringEntry):
        """翻譯完成的回調，線程安全的UI更新"""
        try:
            translated_text = future.result()
            self._update_ui_after_translation(entry, translated_text)
        except Exception as e:
            logging.error(f"Error in translation callback: {e}")
            self._on_translation_error(entry, str(e))

    def _on_translation_error(self, entry: StringEntry, error_msg: str):
        """處理翻譯錯誤"""
        self.processed_count += 1
        total = len(
            [
                e
                for e in self._get_all_selected_entries()
                if e.original and e.original.strip()
            ]
        )

        self.event_system.publish(
            StatusBarUpdateEvent(
                f"翻譯進度: {self.processed_count}/{total} (錯誤: {entry.id})"
            )
        )

        if self.processed_count == total:
            self.event_system.publish(
                StatusBarUpdateEvent("批量翻譯完成，但有部分錯誤。")
            )

    def _update_ui_after_translation(self, entry: StringEntry, translated_text: str):
        """在主線程中執行實際的UI更新"""
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

        # 對於單個翻譯，也更新編輯器
        if total == 1:
            self.event_system.publish(
                EditorTextUpdateEvent(entry.original, entry.translated)
            )
            # 更新高亮（通過事件系統）
            if self.highlighting_service.enabled:
                is_valid = self.highlighting_service.is_valid(entry.translated)
                ranges = self.highlighting_service.get_invalid_ranges(entry.translated)
                self.event_system.publish(TextHighlightUpdateEvent(ranges))
                self.event_system.publish(
                    TreeItemHighlightEvent(entry.id, not is_valid)
                )

        self.event_system.publish(
            StatusBarUpdateEvent(f"翻譯進度: {self.processed_count}/{total}")
        )

    def _on_translation_complete(self, future, entry):
        """翻譯完成回調（線程安全的UI更新）"""
        try:
            translated_text = future.result()
            # 在主線程中執行UI更新
            self.root.after(
                0, self._update_ui_after_translation, entry, translated_text
            )
        except Exception as e:
            logging.error(f"Translation failed for entry {entry.id}: {e}")
            # 在主線程中發布錯誤事件
            error_msg = str(e)
            self.root.after(
                0,
                lambda: self.event_system.publish(
                    ErrorDialogEvent(
                        "翻譯失敗", f"翻譯條目 {entry.id} 時出錯: {error_msg}"
                    )
                ),
            )

        # 計算總任務數
        total = len(
            [
                e
                for e in self._get_all_selected_entries()
                if e.original and e.original.strip()
            ]
        )

        if self.processed_count == total:
            self.event_system.publish(
                StatusBarUpdateEvent(f"全部 {total} 個翻譯任務已完成。")
            )

    def _update_highlights_for_entry(self, entry: StringEntry):
        """更新條目的高亮顯示"""
        from core.events import TextHighlightUpdateEvent, TreeItemHighlightEvent

        if not self.highlighting_service.enabled:
            self.event_system.publish(TextHighlightUpdateEvent([]))
            self.event_system.publish(TreeItemHighlightEvent(entry.id, False))
            return

        is_valid = self.highlighting_service.is_valid(entry.translated)
        ranges = self.highlighting_service.get_invalid_ranges(entry.translated)
        self.event_system.publish(TextHighlightUpdateEvent(ranges))
        self.event_system.publish(TreeItemHighlightEvent(entry.id, not is_valid))

    def show_translation_settings(self):
        """顯示翻譯設置對話框"""
        from ..settings_dialog import SettingsDialog

        try:
            SettingsDialog(self.root, self.translation_service)
            # 對話框是模態的，會自動處理結果
        except Exception as e:
            logging.error(f"Failed to show translation settings: {e}")
            self.event_system.publish(
                ErrorDialogEvent("設置錯誤", f"無法打開翻譯設置對話框: {e}")
            )
