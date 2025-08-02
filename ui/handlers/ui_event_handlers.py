"""
UI事件處理器
負責：樹狀視圖選擇、標籤頁變化、文本修改、高亮切換等UI交互
"""

import tkinter as tk
import logging

from .base_handler import BaseHandler
from core.events import (
    EditorTextUpdateEvent,
    EditorClearEvent,
    TextHighlightUpdateEvent,
    TreeItemHighlightEvent,
    ApplyButtonStateEvent,
)
from core.commands.ui_commands import (
    TreeSelectCommand,
    TabChangedCommand,
    TextModifiedCommand,
    ApplyChangesCommand,
    HighlightToggleCommand,
    TextRealtimeChangeCommand,
    UndoCommand,
)


class UIEventHandlers(BaseHandler):
    """處理所有UI事件相關的功能"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._debounce_timer = None
        self._debounce_delay = 250  # 毫秒
        # 撤回功能相關狀態
        self._undo_history = []  # 儲存撤回歷史
        self._max_undo_steps = 50  # 最大撤回步驟數

    def register_commands(self, command_invoker):
        """註冊UI事件相關的命令"""
        command_invoker.register_command("tree_select", TreeSelectCommand(self))
        command_invoker.register_command("tab_changed", TabChangedCommand(self))
        command_invoker.register_command("text_modified", TextModifiedCommand(self))
        command_invoker.register_command("apply_changes", ApplyChangesCommand(self))
        command_invoker.register_command(
            "highlight_toggle", HighlightToggleCommand(self)
        )
        command_invoker.register_command(
            "text_realtime_change", TextRealtimeChangeCommand(self)
        )
        command_invoker.register_command("undo", UndoCommand(self))

    def on_tree_select(self, event=None):
        """處理樹狀視圖選擇事件"""
        # 更新狀態管理器中的選中狀態
        current_filepath = self.ui.get_current_filepath()
        selected_id = self.ui.get_selected_tree_item_id()
        logging.info(
            f"Tree select: filepath={current_filepath}, selected_id={selected_id}"
        )
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

        # 加載新文本後，編輯器是乾淨的，所以禁用應用按鈕
        self.ui.translated_text.edit_modified(False)
        self.event_system.publish(ApplyButtonStateEvent(False))

    def on_tab_changed(self, event=None):
        """處理標籤頁變化事件"""
        # 確保狀態管理器有當前標籤頁的信息
        current_filepath = self.ui.get_current_filepath()
        if current_filepath:
            # 更新狀態管理器的當前文件選擇（但不改變條目選擇）
            current_entry_id = self.state_manager.current_selected_entry_id
            self.state_manager.set_current_selection(current_filepath, current_entry_id)

        self._update_all_highlights_for_current_tab()

        # 觸發樹狀視圖選擇事件以更新編輯器
        self.on_tree_select()

        # 更新菜單狀態
        # 這些狀態更新可能需要通過事件系統來處理
        # 或者在協調器中處理

    def on_text_changed(self, event=None):
        """處理文本變化事件"""
        selected_entry = self.state_manager.get_selected_entry()
        if not selected_entry:
            return

        new_text = self.ui.translated_text.get("1.0", tk.END).strip()
        if selected_entry.translated != new_text:
            # 在更新前保存撤回狀態
            self._save_undo_state()
            
            # 使用狀態管理器更新翻譯
            self.state_manager.update_entry_translation(selected_entry.id, new_text)
            from core.events import TreeItemUpdateEvent

            self.event_system.publish(TreeItemUpdateEvent(selected_entry.id, new_text))
            self._update_highlights_for_entry(selected_entry)

        # 應用更改後，重置修改標誌，這將觸發 <<Modified>> 事件
        # 並調用 on_translated_text_modified 來禁用按鈕
        self.ui.translated_text.edit_modified(False)

    def on_translated_text_modified(self, event=None):
        """啟用或禁用 'Apply' 按鈕，基於文本小工具的修改狀態"""
        modified = self.ui.translated_text.edit_modified()
        self.event_system.publish(ApplyButtonStateEvent(modified))

    def on_translated_text_changed_realtime(self, event=None):
        """實時處理譯文文本變化，使用防抖技術更新高亮標記"""
        # 取消之前的計時器
        if self._debounce_timer:
            self.root.after_cancel(self._debounce_timer)

        # 設置新的計時器
        self._debounce_timer = self.root.after(
            self._debounce_delay, self._perform_highlight_update
        )

    def _perform_highlight_update(self):
        """實際執行高亮更新的操作"""
        selected_entry = self.state_manager.get_selected_entry()
        if not selected_entry:
            return

        # 獲取當前編輯器中的文本
        try:
            current_text = self.ui.translated_text.get("1.0", tk.END).strip()
        except tk.TclError:
            # 小部件可能已被銷毀
            return

        # 更新高亮標記
        if not self.highlighting_service.enabled:
            self.event_system.publish(TextHighlightUpdateEvent([]))
            return

        ranges = self.highlighting_service.get_invalid_ranges(current_text)
        self.event_system.publish(TextHighlightUpdateEvent(ranges))

    def on_highlight_toggle(self):
        """切換高亮服務並刷新UI"""
        is_enabled = self.ui.get_highlight_enabled()
        self.highlighting_service.enabled = is_enabled
        logging.info(f"Highlighting toggled: {'Enabled' if is_enabled else 'Disabled'}")
        self._update_all_highlights_for_current_tab()

    def _update_highlights_for_entry(self, entry):
        """更新條目的高亮顯示"""
        if not self.highlighting_service.enabled:
            self.event_system.publish(TextHighlightUpdateEvent([]))
            self.event_system.publish(TreeItemHighlightEvent(entry.id, False))
            return

        is_valid = self.highlighting_service.is_valid(entry.translated)
        ranges = self.highlighting_service.get_invalid_ranges(entry.translated)
        self.event_system.publish(TextHighlightUpdateEvent(ranges))
        self.event_system.publish(TreeItemHighlightEvent(entry.id, not is_valid))

    def _update_all_highlights_for_current_tab(self):
        """更新當前標籤頁的所有高亮"""
        current_data = self._get_current_data()
        if not current_data:
            return

        # 首先，更新樹狀視圖中的所有行
        enabled = self.highlighting_service.enabled
        for entry in current_data:
            if not enabled:
                self.event_system.publish(TreeItemHighlightEvent(entry.id, False))
            else:
                is_valid = self.highlighting_service.is_valid(entry.translated)
                self.event_system.publish(
                    TreeItemHighlightEvent(entry.id, not is_valid)
                )

        # 然後，更新當前選中條目的編輯器
        selected_entry = self._get_selected_entry()
        if selected_entry:
            # 這也會正確處理高亮被禁用的情況
            self._update_highlights_for_entry(selected_entry)
        else:
            # 如果沒有選中任何內容，確保編輯器高亮被清除
            self.event_system.publish(TextHighlightUpdateEvent([]))

    def _save_undo_state(self):
        """保存當前狀態到撤回歷史（只有在文本真正改變時才保存）"""
        selected_entry = self.state_manager.get_selected_entry()
        if not selected_entry:
            return

        # 獲取當前編輯器中的文本
        try:
            current_text = self.ui.translated_text.get("1.0", tk.END).strip()
        except tk.TclError:
            return

        # 檢查是否有實際的文本改變（編輯器中的文本與條目中的不同）
        if current_text == selected_entry.translated:
            # 沒有實際改變，不保存狀態
            return

        # 檢查是否與最後一個撤回狀態相同（避免重複保存）
        if self._undo_history:
            last_state = self._undo_history[-1]
            if (last_state["entry_id"] == selected_entry.id and 
                last_state["translated_text"] == selected_entry.translated):
                return

        # 創建撤回狀態
        undo_state = {
            "entry_id": selected_entry.id,
            "file_path": selected_entry.file_name,
            "original_text": selected_entry.original,
            "translated_text": selected_entry.translated,
            "editor_text": current_text
        }

        # 添加到歷史中
        self._undo_history.append(undo_state)
        logging.debug(f"已保存撤回狀態：條目 {selected_entry.id}，歷史數量: {len(self._undo_history)}")

        # 保持歷史大小在限制內
        if len(self._undo_history) > self._max_undo_steps:
            self._undo_history.pop(0)

    def clear_undo_history(self):
        """清空撤回歷史（用於加載新工程或目錄時）"""
        history_count = len(self._undo_history)
        self._undo_history.clear()
        if history_count > 0:
            logging.info(f"已清空 {history_count} 個撤回歷史記錄")
        else:
            logging.debug("撤回歷史為空，無需清理")

    def on_undo(self):
        """執行撤回操作"""
        from core.events import StatusBarUpdateEvent
        
        if not self._undo_history:
            logging.info("沒有可撤回的操作")
            self.event_system.publish(StatusBarUpdateEvent("沒有可撤回的操作"))
            return

        # 獲取最後一個狀態
        last_state = self._undo_history.pop()

        # 尋找對應的條目
        entry = None
        for file_data in self.state_manager.open_files_data.values():
            for e in file_data:
                if (e.id == last_state["entry_id"] and 
                    e.file_name == last_state["file_path"]):
                    entry = e
                    break
            if entry:
                break

        if not entry:
            logging.warning(f"找不到條目 ID {last_state['entry_id']}")
            self.event_system.publish(StatusBarUpdateEvent(f"找不到條目 ID {last_state['entry_id']}"))
            return

        # 恢復狀態
        entry.translated = last_state["translated_text"]

        # 更新狀態管理器
        self.state_manager.update_entry_translation(entry.id, last_state["translated_text"])

        # 更新UI
        # 1. 更新編輯器
        self.event_system.publish(EditorTextUpdateEvent(
            last_state["original_text"], 
            last_state["translated_text"]
        ))
        
        # 2. 更新樹狀視圖中的顯示
        from core.events import TreeItemUpdateEvent
        self.event_system.publish(TreeItemUpdateEvent(entry.id, last_state["translated_text"]))
        
        # 3. 更新高亮顯示
        self._update_highlights_for_entry(entry)

        # 提供更詳細的撤回信息
        undo_message = f"已撤回條目 {entry.id}：'{last_state['translated_text'][:20]}{'...' if len(last_state['translated_text']) > 20 else ''}'"
        logging.info(undo_message)
        self.event_system.publish(StatusBarUpdateEvent(undo_message))
