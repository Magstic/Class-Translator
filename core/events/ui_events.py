"""
UI相關事件定義
定義所有與UI交互相關的事件類型
"""

from typing import List
from .event_system import Event


class StatusBarUpdateEvent(Event):
    """狀態欄更新事件"""

    def __init__(self, message: str, source: str = "EventHandlers"):
        super().__init__(source)
        self.message = message

    @property
    def event_type(self) -> str:
        return "status_bar_update"


class InfoDialogEvent(Event):
    """信息對話框事件"""

    def __init__(self, title: str, message: str, source: str = "EventHandlers"):
        super().__init__(source)
        self.title = title
        self.message = message

    @property
    def event_type(self) -> str:
        return "info_dialog"


class ErrorDialogEvent(Event):
    """錯誤對話框事件"""

    def __init__(self, title: str, message: str, source: str = "EventHandlers"):
        super().__init__(source)
        self.title = title
        self.message = message

    @property
    def event_type(self) -> str:
        return "error_dialog"


class WarningDialogEvent(Event):
    """警告對話框事件"""

    def __init__(self, title: str, message: str, source: str = "EventHandlers"):
        super().__init__(source)
        self.title = title
        self.message = message

    @property
    def event_type(self) -> str:
        return "warning_dialog"


class TreeItemUpdateEvent(Event):
    """樹狀視圖項目更新事件"""

    def __init__(
        self, item_id: int, translated_text: str, source: str = "EventHandlers"
    ):
        super().__init__(source)
        self.item_id = item_id
        self.translated_text = translated_text

    @property
    def event_type(self) -> str:
        return "tree_item_update"


class TreeItemHighlightEvent(Event):
    """樹狀視圖項目高亮事件"""

    def __init__(self, item_id: int, highlight: bool, source: str = "EventHandlers"):
        super().__init__(source)
        self.item_id = item_id
        self.highlight = highlight

    @property
    def event_type(self) -> str:
        return "tree_item_highlight"


class EditorTextUpdateEvent(Event):
    """編輯器文本更新事件"""

    def __init__(self, original: str, translated: str, source: str = "EventHandlers"):
        super().__init__(source)
        self.original = original
        self.translated = translated

    @property
    def event_type(self) -> str:
        return "editor_text_update"


class EditorClearEvent(Event):
    """編輯器清空事件"""

    def __init__(self, source: str = "EventHandlers"):
        super().__init__(source)

    @property
    def event_type(self) -> str:
        return "editor_clear"


class TextHighlightUpdateEvent(Event):
    """文本高亮更新事件"""

    def __init__(self, ranges: List[tuple[int, int]], source: str = "EventHandlers"):
        super().__init__(source)
        self.ranges = ranges

    @property
    def event_type(self) -> str:
        return "text_highlight_update"


class ApplyButtonStateEvent(Event):
    """應用按鈕狀態事件"""

    def __init__(self, enabled: bool, source: str = "EventHandlers"):
        super().__init__(source)
        self.enabled = enabled

    @property
    def event_type(self) -> str:
        return "apply_button_state"


class TreeSelectionEvent(Event):
    """樹狀視圖選擇事件"""

    def __init__(self, item_ids: List[int], source: str = "EventHandlers"):
        super().__init__(source)
        self.item_ids = item_ids

    @property
    def event_type(self) -> str:
        return "tree_selection"
