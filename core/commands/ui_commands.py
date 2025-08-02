"""
UI相關命令實現

實現了所有UI操作的命令類，統一處理用戶交互。
"""

from typing import Optional, Any
from .command_interface import ICommand


class LoadDirectoryCommand(ICommand):
    """加載目錄命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.on_load_directory()

    def can_execute(self) -> bool:
        return True


class SaveFileCommand(ICommand):
    """保存文件命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.on_save_file()

    def can_execute(self) -> bool:
        return self.event_handlers.state_manager.has_open_files()


class SaveAllFilesCommand(ICommand):
    """保存所有文件命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.on_save_all_files()

    def can_execute(self) -> bool:
        return self.event_handlers.state_manager.has_open_files()


class SaveProjectCommand(ICommand):
    """保存工程命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.on_save_project()

    def can_execute(self) -> bool:
        return self.event_handlers.state_manager.has_open_files()


class LoadProjectCommand(ICommand):
    """加載工程命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.on_load_project()

    def can_execute(self) -> bool:
        return True


class TranslateCommand(ICommand):
    """翻譯命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.on_translate()

    def can_execute(self) -> bool:
        return self.event_handlers.state_manager.get_selected_entry() is not None


class TranslateAllCommand(ICommand):
    """翻譯全部命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.on_translate_all()

    def can_execute(self) -> bool:
        return self.event_handlers.state_manager.has_open_files()


class ApplyChangesCommand(ICommand):
    """應用更改命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.on_text_changed(*args)

    def can_execute(self) -> bool:
        return self.event_handlers.state_manager.get_selected_entry() is not None


class HighlightToggleCommand(ICommand):
    """切換高亮命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.on_highlight_toggle()

    def can_execute(self) -> bool:
        return True


class ShowFindDialogCommand(ICommand):
    """顯示查找對話框命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.show_find_dialog()

    def can_execute(self) -> bool:
        return self.event_handlers.state_manager.has_open_files()


class ShowFindReplaceDialogCommand(ICommand):
    """顯示查找替換對話框命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.show_find_replace_dialog()

    def can_execute(self) -> bool:
        return self.event_handlers.state_manager.has_open_files()


class ShowTranslationSettingsCommand(ICommand):
    """顯示翻譯設置對話框命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.show_translation_settings()

    def can_execute(self) -> bool:
        return True


class ShowAboutCommand(ICommand):
    """顯示關於對話框命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.show_about()

    def can_execute(self) -> bool:
        return True


class TreeSelectCommand(ICommand):
    """樹狀視圖選擇命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, event=None, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.on_tree_select(event)

    def can_execute(self) -> bool:
        return True


class TabChangedCommand(ICommand):
    """標籤頁切換命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, event=None, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.on_tab_changed(event)

    def can_execute(self) -> bool:
        return True


class TextModifiedCommand(ICommand):
    """文本修改命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, event=None, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.on_translated_text_modified(event)

    def can_execute(self) -> bool:
        return True


class ShowFileTypeConfigCommand(ICommand):
    """顯示文件類型配置對話框命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.on_show_file_type_config()

    def can_execute(self) -> bool:
        return True


class TextRealtimeChangeCommand(ICommand):
    """實時文本變更命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, event=None, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.on_translated_text_changed_realtime(event)

    def can_execute(self) -> bool:
        return True


class UndoCommand(ICommand):
    """撤回命令"""

    def __init__(self, event_handlers):
        self.event_handlers = event_handlers

    def execute(self, *args, **kwargs) -> Optional[Any]:
        return self.event_handlers.on_undo()

    def can_execute(self) -> bool:
        return True
