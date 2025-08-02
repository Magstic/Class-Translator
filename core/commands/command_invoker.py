"""
命令調用器

負責執行命令並處理錯誤，提供統一的命令執行入口。
"""

import logging
from typing import Optional, Any, Dict
from .command_interface import ICommand


class CommandInvoker:
    """命令調用器 - 統一執行所有用戶命令"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._commands: Dict[str, ICommand] = {}

    def register_command(self, name: str, command: ICommand):
        """
        註冊命令

        Args:
            name: 命令名稱
            command: 命令實例
        """
        self._commands[name] = command
        self.logger.debug(f"註冊命令: {name}")

    def execute_command(self, name: str, *args, **kwargs) -> Optional[Any]:
        """
        執行命令

        Args:
            name: 命令名稱
            *args: 位置參數
            **kwargs: 關鍵字參數

        Returns:
            Optional[Any]: 命令執行結果
        """
        command = self._commands.get(name)
        if not command:
            self.logger.error(f"未找到命令: {name}")
            return None

        if not command.can_execute():
            self.logger.warning(f"命令無法執行: {name}")
            return None

        try:
            self.logger.debug(f"執行命令: {name}")
            return command.execute(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"命令執行失敗: {name}, 錯誤: {e}")
            raise

    def can_execute_command(self, name: str) -> bool:
        """
        檢查命令是否可以執行

        Args:
            name: 命令名稱

        Returns:
            bool: True如果命令可以執行
        """
        command = self._commands.get(name)
        return command.can_execute() if command else False

    def get_registered_commands(self) -> Dict[str, str]:
        """
        獲取已註冊的命令列表

        Returns:
            Dict[str, str]: 命令名稱到描述的映射
        """
        return {name: cmd.get_description() for name, cmd in self._commands.items()}

    def create_command_handler(self, command_name: str):
        """
        創建命令處理器函數，用於UI綁定

        Args:
            command_name: 命令名稱

        Returns:
            callable: 可用於UI綁定的函數
        """

        def handler(*args, **kwargs):
            return self.execute_command(command_name, *args, **kwargs)

        handler.__name__ = f"handle_{command_name}"
        return handler
