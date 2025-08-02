"""
主题相关的命令
"""

import logging
from .command_interface import ICommand
class ShowThemeDialogCommand(ICommand):
    """显示主题选择对话框命令"""

    def __init__(self, theme_handlers: 'ThemeHandlers'):
        self.logger = logging.getLogger(__name__)
        self.theme_handlers = theme_handlers

    def can_execute(self) -> bool:
        """检查命令是否可以执行"""
        return self.theme_handlers is not None

    def execute(self):
        """执行显示主题对话框命令"""
        try:
            if self.can_execute():
                self.theme_handlers.on_show_theme_dialog()
        except Exception as e:
            self.logger.error(f"执行主题对话框命令失败: {e}")
            from core.events import get_event_system, ErrorDialogEvent
            event_system = get_event_system()
            event_system.publish(ErrorDialogEvent("错误", f"无法显示主题设置对话框: {e}"))
