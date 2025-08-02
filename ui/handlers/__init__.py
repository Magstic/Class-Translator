"""
Handlers模塊 - 拆分後的事件處理器
"""

from .base_handler import BaseHandler
from .file_operation_handlers import FileOperationHandlers
from .translation_handlers import TranslationHandlers
from .ui_event_handlers import UIEventHandlers
from .project_handlers import ProjectHandlers
from .search_handlers import SearchHandlers
from .config_handlers import ConfigHandlers
from .event_handler_coordinator import EventHandlerCoordinator

__all__ = [
    "BaseHandler",
    "FileOperationHandlers",
    "TranslationHandlers",
    "UIEventHandlers",
    "ProjectHandlers",
    "SearchHandlers",
    "ConfigHandlers",
    "EventHandlerCoordinator",
]
