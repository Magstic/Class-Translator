"""
查找替換相關的處理器
負責：查找對話框、替換對話框、查找替換功能
"""

import re

from .base_handler import BaseHandler
from core.events import (
    StatusBarUpdateEvent,
    InfoDialogEvent,
    TreeSelectionEvent,
    TreeItemUpdateEvent,
)
from core.commands import (
    ShowFindDialogCommand,
    ShowFindReplaceDialogCommand,
)


class SearchHandlers(BaseHandler):
    """處理所有查找替換相關的功能"""

    def register_commands(self, command_invoker):
        """註冊查找替換相關的命令"""
        command_invoker.register_command(
            "show_find_dialog", ShowFindDialogCommand(self)
        )
        command_invoker.register_command(
            "show_find_replace_dialog", ShowFindReplaceDialogCommand(self)
        )

    def show_find_dialog(self):
        """顯示查找對話框"""
        current_data = self._get_current_data()
        if not current_data:
            self.event_system.publish(InfoDialogEvent("無數據", "沒有可供查找的數據。"))
            return

        from ..find_dialog import FindDialog

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
            if search_in == "original":
                targets.append(entry.original)
            elif search_in == "translated":
                targets.append(entry.translated)
            elif search_in == "both":
                targets.append(entry.original)
                targets.append(entry.translated)

            for target_text in targets:
                if target_text and re.search(find_text, target_text, flags):
                    found_ids.append(entry.id)
                    break  # 移動到下一個條目，一旦找到

        if found_ids:
            self.event_system.publish(TreeSelectionEvent(found_ids))
            self.event_system.publish(
                StatusBarUpdateEvent(f"找到了 {len(found_ids)} 個匹配項。")
            )
        else:
            self.event_system.publish(StatusBarUpdateEvent(f"未找到 '{find_text}'。"))

    def show_find_replace_dialog(self):
        """顯示查找替換對話框"""
        if not self._get_current_data():
            self.event_system.publish(InfoDialogEvent("無數據", "沒有可供操作的數據。"))
            return

        from ..find_replace_dialog import FindReplaceDialog

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
                    InfoDialogEvent("無選擇", "請先選擇要替換的條目。")
                )
                return

        count = 0
        flags = 0 if match_case else re.IGNORECASE

        for entry in entries_to_process:
            if not entry.translated:
                continue

            new_translated, num_subs = re.subn(
                find_text, replace_text, entry.translated, flags=flags
            )
            if num_subs > 0:
                count += 1
                # 使用狀態管理器更新翻譯
                self.state_manager.update_entry_translation(entry.id, new_translated)
                self.event_system.publish(TreeItemUpdateEvent(entry.id, new_translated))

        # 更新當前標籤頁的所有高亮
        self._update_all_highlights_for_current_tab()

        # 刷新編輯器（如果需要）
        selected_entry = self._get_selected_entry()
        if selected_entry:
            from core.events import EditorTextUpdateEvent

            self.event_system.publish(
                EditorTextUpdateEvent(
                    selected_entry.original, selected_entry.translated
                )
            )

        self.event_system.publish(
            StatusBarUpdateEvent(
                f"在 {len(entries_to_process)} 個條目中，共替換了 {count} 處。"
            )
        )

    def _update_all_highlights_for_current_tab(self):
        """更新當前標籤頁的所有高亮（從UIEventHandlers複製）"""
        current_data = self._get_current_data()
        if not current_data:
            return

        # 首先，更新樹狀視圖中的所有行
        enabled = self.highlighting_service.enabled
        for entry in current_data:
            if not enabled:
                from core.events import TreeItemHighlightEvent

                self.event_system.publish(TreeItemHighlightEvent(entry.id, False))
            else:
                is_valid = self.highlighting_service.is_valid(entry.translated)
                from core.events import TreeItemHighlightEvent

                self.event_system.publish(
                    TreeItemHighlightEvent(entry.id, not is_valid)
                )

        # 然後，更新當前選中條目的編輯器
        selected_entry = self._get_selected_entry()
        if selected_entry:
            self._update_highlights_for_entry(selected_entry)
        else:
            # 如果沒有選中任何內容，確保編輯器高亮被清除
            from core.events import TextHighlightUpdateEvent

            self.event_system.publish(TextHighlightUpdateEvent([]))

    def _update_highlights_for_entry(self, entry):
        """更新條目的高亮顯示（從UIEventHandlers複製）"""
        from core.events import TextHighlightUpdateEvent, TreeItemHighlightEvent

        if not self.highlighting_service.enabled:
            self.event_system.publish(TextHighlightUpdateEvent([]))
            self.event_system.publish(TreeItemHighlightEvent(entry.id, False))
            return

        is_valid = self.highlighting_service.is_valid(entry.translated)
        ranges = self.highlighting_service.get_invalid_ranges(entry.translated)
        self.event_system.publish(TextHighlightUpdateEvent(ranges))
        self.event_system.publish(TreeItemHighlightEvent(entry.id, not is_valid))
