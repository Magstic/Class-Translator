"""
命令模式接口定義

定義了統一的命令接口，所有用戶操作都實現這個接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class ICommand(ABC):
    """命令接口 - 所有用戶操作命令的基類"""

    @abstractmethod
    def execute(self, *args, **kwargs) -> Optional[Any]:
        """
        執行命令

        Args:
            *args: 位置參數
            **kwargs: 關鍵字參數

        Returns:
            Optional[Any]: 命令執行結果（如果有）
        """
        pass

    @abstractmethod
    def can_execute(self) -> bool:
        """
        檢查命令是否可以執行

        Returns:
            bool: True如果命令可以執行，False否則
        """
        pass

    def get_description(self) -> str:
        """
        獲取命令描述

        Returns:
            str: 命令的描述文字
        """
        return self.__class__.__name__
