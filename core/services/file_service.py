import os
import shutil
from typing import List, Dict, Tuple

from parsers import BaseParser, get_parser_factory
from core.models import StringEntry


class FileService:
    """Service responsible for file loading and saving operations."""

    def __init__(self):
        # Maps file paths to their parser instances
        self.parsers: Dict[str, BaseParser] = {}
        # 獲取解析器工廠實例
        self.parser_factory = get_parser_factory()

    def get_files_by_type_in_directory(self, dir_path: str) -> Dict[str, List[str]]:
        """獲取目錄中按文件類型分組的文件列表"""
        return self.parser_factory.get_supported_files_by_type(dir_path)

    def load_directory(self, dir_path: str) -> Dict[str, List[StringEntry]]:
        """Loads all supported files from a directory and returns their string entries."""
        self.parsers.clear()

        # 使用解析器工廠獲取支持的文件
        supported_files = self.parser_factory.get_supported_files_in_directory(dir_path)
        if not supported_files:
            supported_exts = ", ".join(self.parser_factory.get_supported_extensions())
            raise FileNotFoundError(
                f"No supported files found in '{dir_path}'. Supported types: {supported_exts}"
            )

        return self._load_files(supported_files)

    def load_selected_files(
        self, file_paths: List[str]
    ) -> Dict[str, List[StringEntry]]:
        """加載指定的文件列表"""
        self.parsers.clear()
        return self._load_files(file_paths)

    def _load_files(self, file_paths: List[str]) -> Dict[str, List[StringEntry]]:
        """內部方法：加載指定的文件列表"""
        loaded_data = {}

        for filepath in file_paths:
            try:
                # 使用解析器工廠創建對應的解析器
                parser = self.parser_factory.create_parser(filepath)
                raw_strings = parser.get_utf8_strings()

                # 獲取文件類型
                file_extension = os.path.splitext(filepath)[1].lower()

                string_entries = [
                    StringEntry(
                        id=s["id"],
                        original=s["original"],
                        translated=s["translated"],
                        file_name=filepath,  # 使用完整路徑而非只有文件名
                        line_number=s.get("line_number", 0),
                        file_type=file_extension,  # 動態獲取文件類型
                        # Store a reference to the parser for saving later
                        parser_ref=parser,
                    )
                    for s in raw_strings
                ]

                if string_entries:
                    loaded_data[filepath] = string_entries
                    self.parsers[filepath] = parser

            except Exception as e:
                filename = os.path.basename(filepath)
                print(f"Warning: Could not process file {filename}: {e}")
                # Optionally, decide if you want to skip or halt
                continue

        return loaded_data

    def save_file(
        self, filepath: str, string_entries: List[StringEntry]
    ) -> Tuple[str, int]:
        """Saves the changes for a single file back to the original path."""
        parser = self.parsers.get(filepath)
        if not parser:
            raise RuntimeError(
                f"No parser available for file: {filepath}. Was it loaded correctly?"
            )

        # Create a backup
        backup_path = filepath + ".bak"
        if not os.path.exists(backup_path):
            shutil.copy2(filepath, backup_path)

        update_count = 0
        for entry in string_entries:
            if entry.original != entry.translated:
                parser.update_utf8_string(entry.id, entry.translated)
                update_count += 1

        if update_count > 0:
            parser.save(filepath)

        return backup_path, update_count

    def get_supported_extensions(self) -> List[str]:
        """獲取所有支持的文件擴展名"""
        return self.parser_factory.get_supported_extensions()

    def is_supported_file(self, filepath: str) -> bool:
        """檢查文件是否為支持的類型"""
        return self.parser_factory.is_supported_file(filepath)

    def register_parser(self, extension: str, parser_class):
        """註冊新的解析器類型"""
        self.parser_factory.register_parser(extension, parser_class)

    def get_file_type_info(self) -> Dict[str, str]:
        """獲取文件類型信息，用於UI顯示"""
        extensions = self.get_supported_extensions()
        return {ext: f"{ext.upper()} files (*{ext})" for ext in extensions}
