"""
解析器工廠模塊

負責根據文件類型創建對應的解析器實例，支持動態註冊新的解析器類型。
"""

import os
from typing import Dict, Type, List
from .base_parser import BaseParser
from .class_parser import ClassParser
from .text_parser import TextParser

# 導入配置管理（可選，保持向後兼容）
try:
    from core.config.file_type_config import get_file_type_config

    _config_available = True
except ImportError:
    _config_available = False


class ParserFactory:
    """解析器工廠類，負責根據文件擴展名創建對應的解析器"""

    def __init__(self):
        # 基礎解析器映射（硬編碼，確保向後兼容）
        self._base_parsers: Dict[str, Type[BaseParser]] = {
            ".class": ClassParser,
            ".t": TextParser,
        }

        # 動態解析器映射（用戶註冊的）
        self._dynamic_parsers: Dict[str, Type[BaseParser]] = {}

        # 配置系統引用
        self._config = None
        if _config_available:
            try:
                self._config = get_file_type_config()
            except Exception:
                pass  # 如果配置加載失敗，繼續使用基礎功能

        # 更新支持的擴展名列表
        self._update_supported_extensions()

    def _update_supported_extensions(self):
        """更新支持的擴展名列表"""
        # 合併基礎解析器和動態解析器
        all_parsers = {**self._base_parsers, **self._dynamic_parsers}

        # 如果有配置系統，添加配置中的純文本擴展名
        if self._config:
            text_extensions = self._config.get_text_extensions()
            for ext in text_extensions:
                if ext not in all_parsers:
                    # 對於配置中的純文本擴展名，使用TextParser
                    all_parsers[ext] = TextParser

        self._parsers = all_parsers
        self._supported_extensions = list(all_parsers.keys())

    def register_parser(self, extension: str, parser_class: Type[BaseParser]):
        """
        註冊新的解析器類型

        Args:
            extension: 文件擴展名（如 '.jar', '.dex'）
            parser_class: 解析器類，必須繼承自 BaseParser
        """
        if not extension.startswith("."):
            extension = "." + extension

        if not issubclass(parser_class, BaseParser):
            raise ValueError(
                f"Parser class {parser_class} must inherit from BaseParser"
            )

        # 註冊到動態解析器映射中
        self._dynamic_parsers[extension.lower()] = parser_class

        # 更新支持的擴展名列表
        self._update_supported_extensions()

    def create_parser(self, filepath: str) -> BaseParser:
        """
        根據文件路徑創建對應的解析器

        Args:
            filepath: 文件路徑

        Returns:
            對應的解析器實例

        Raises:
            ValueError: 不支持的文件類型
        """
        extension = self._get_file_extension(filepath)

        if extension not in self._parsers:
            raise ValueError(
                f"Unsupported file type: {extension}. Supported types: {self._supported_extensions}"
            )

        parser_class = self._parsers[extension]
        return parser_class(filepath)

    def is_supported_file(self, filepath: str) -> bool:
        """
        檢查文件是否為支持的類型

        Args:
            filepath: 文件路徑

        Returns:
            是否支持該文件類型
        """
        extension = self._get_file_extension(filepath)
        return extension in self._parsers

    def get_supported_extensions(self) -> List[str]:
        """
        獲取所有支持的文件擴展名

        Returns:
            支持的文件擴展名列表
        """
        return self._supported_extensions.copy()

    def get_supported_files_in_directory(self, dir_path: str) -> List[str]:
        """
        獲取目錄中所有支持的文件

        Args:
            dir_path: 目錄路徑

        Returns:
            支持的文件路徑列表
        """
        if not os.path.exists(dir_path):
            return []

        supported_files = []
        for filename in os.listdir(dir_path):
            filepath = os.path.join(dir_path, filename)
            if os.path.isfile(filepath) and self.is_supported_file(filepath):
                supported_files.append(filepath)

        return sorted(supported_files)

    def _get_file_extension(self, filepath: str) -> str:
        """
        獲取文件擴展名

        Args:
            filepath: 文件路徑

        Returns:
            小寫的文件擴展名
        """
        return os.path.splitext(filepath)[1].lower()

    def refresh_config(self):
        """
        刷新配置系統，重新加載文件類型配置
        """
        if _config_available:
            try:
                from core.config.file_type_config import get_file_type_config

                self._config = get_file_type_config()
                self._update_supported_extensions()
            except Exception as e:
                print(f"刷新配置失敗: {e}")

    def set_config(self, config):
        """
        設置文件類型配置實例（用於測試）

        Args:
            config: FileTypeConfig實例
        """
        self._config = config
        self._update_supported_extensions()

    def get_file_type(self, filepath: str) -> str:
        """
        獲取文件類型（text/class/unknown）

        Args:
            filepath: 文件路徑

        Returns:
            文件類型字符串
        """
        if self._config:
            return self._config.get_file_type(filepath)
        else:
            # 回退到基礎檢測
            ext = self._get_file_extension(filepath)
            if ext == ".class":
                return "class"
            elif ext in [".t", ".txt", ".text"]:
                return "text"
            else:
                return "unknown"

    def get_supported_files_by_type(self, dir_path: str) -> Dict[str, List[str]]:
        """
        獲取目錄中支持的文件，按類型分組

        Args:
            dir_path: 目錄路徑

        Returns:
            按文件類型分組的文件路徑字典
        """
        if self._config:
            return self._config.get_supported_files_in_directory(dir_path)
        else:
            # 回退到基礎實現
            result = {"text": [], "class": [], "unknown": []}
            if os.path.exists(dir_path):
                for filename in os.listdir(dir_path):
                    filepath = os.path.join(dir_path, filename)
                    if os.path.isfile(filepath):
                        file_type = self.get_file_type(filepath)
                        if file_type in result:
                            result[file_type].append(filepath)
            return result


# 全局解析器工廠實例
_parser_factory = ParserFactory()


def get_parser_factory() -> ParserFactory:
    """獲取全局解析器工廠實例"""
    return _parser_factory


def register_parser(extension: str, parser_class: Type[BaseParser]):
    """
    註冊新的解析器類型的便捷函數

    Args:
        extension: 文件擴展名
        parser_class: 解析器類
    """
    _parser_factory.register_parser(extension, parser_class)
