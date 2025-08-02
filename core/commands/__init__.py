"""
命令模式實現 - 統一用戶操作處理

這個模塊實現了命令模式，用於統一處理所有用戶操作，
提供更好的解耦和可測試性。
"""

from .command_interface import ICommand
from .ui_commands import (
    LoadDirectoryCommand,
    SaveFileCommand,
    SaveAllFilesCommand,
    SaveProjectCommand,
    LoadProjectCommand,
    TranslateCommand,
    TranslateAllCommand,
    ApplyChangesCommand,
    HighlightToggleCommand,
    ShowFindDialogCommand,
    ShowFindReplaceDialogCommand,
    ShowTranslationSettingsCommand,
    ShowAboutCommand,
    TreeSelectCommand,
    TabChangedCommand,
    TextModifiedCommand,
    ShowFileTypeConfigCommand,
    TextRealtimeChangeCommand,
)
from .command_invoker import CommandInvoker

__all__ = [
    "ICommand",
    "LoadDirectoryCommand",
    "SaveFileCommand",
    "SaveAllFilesCommand",
    "SaveProjectCommand",
    "LoadProjectCommand",
    "TranslateCommand",
    "TranslateAllCommand",
    "ApplyChangesCommand",
    "HighlightToggleCommand",
    "ShowFindDialogCommand",
    "ShowFindReplaceDialogCommand",
    "ShowTranslationSettingsCommand",
    "ShowAboutCommand",
    "TreeSelectCommand",
    "TabChangedCommand",
    "TextModifiedCommand",
    "ShowFileTypeConfigCommand",
    "CommandInvoker",
]
