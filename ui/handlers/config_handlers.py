"""
配置相關的處理器
負責：文件類型配置、關於對話框等配置功能
"""

import logging

from .base_handler import BaseHandler
from core.events import (
    StatusBarUpdateEvent,
    ErrorDialogEvent,
)
from core.commands import (
    ShowFileTypeConfigCommand,
    ShowAboutCommand,
)


class ConfigHandlers(BaseHandler):
    """處理所有配置相關的功能"""

    def register_commands(self, command_invoker):
        """註冊配置相關的命令"""
        command_invoker.register_command(
            "show_file_type_config", ShowFileTypeConfigCommand(self)
        )
        command_invoker.register_command("show_about", ShowAboutCommand(self))

    def on_show_file_type_config(self):
        """顯示文件類型配置對話框"""
        from ..file_type_config_dialog import FileTypeConfigDialog

        try:
            dialog = FileTypeConfigDialog(self.root)
            result = dialog.show()

            if result:
                # 配置已更新，刷新解析器工廠
                from parsers.parser_factory import get_parser_factory

                factory = get_parser_factory()
                factory.refresh_config()

                self.event_system.publish(StatusBarUpdateEvent("文件類型配置已更新"))
        except Exception as e:
            logging.error(f"Failed to show file type config: {e}")
            self.event_system.publish(
                ErrorDialogEvent("配置錯誤", f"無法打開文件類型配置對話框: {e}")
            )

    def show_about(self):
        """顯示關於對話框"""
        import tkinter.messagebox as messagebox

        try:
            messagebox.showinfo(
                "關於",
                "CLASS 編輯器\n\n"
                "為 J2ME 遊戲漢化而設計。\n"
                "使用內建的翻譯引擎，讓您專注於翻譯的潤色和遊戲的測試。\n\n"
                "這個程式使用現代化的事件驅動架構開發。\n\n"
                "如果您在使用過程中發現任何問題，請告訴我們。\n\n"
                "版本: 2.0 (解耦重構版)",
            )
        except Exception as e:
            logging.error(f"Failed to show about dialog: {e}")
            self.event_system.publish(
                ErrorDialogEvent("顯示錯誤", f"無法顯示關於對話框: {e}")
            )
