"""
文本文件解析器

專門用於處理 .t 文件（每個文件包含一行文本）的解析器。
支持單行文本的讀取、編輯和保存。
"""

import os
from typing import List, Dict, Any
from .base_parser import BaseParser


class TextParser(BaseParser):
    """文本文件解析器，專門處理 .t 文件"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.original_content = ""
        self.current_content = ""
        self.modified = False

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Text file not found: {filepath}")

        # 讀取文件內容
        self._load_content()

    def _load_content(self):
        """加載文件內容，支持多種編碼自動檢測"""
        # 編碼檢測順序：UTF-8 -> EUC-KR -> GBK -> 錯誤替換
        encodings_to_try = [
            ("utf-8", "UTF-8"),
            ("euc-kr", "EUC-KR (韓文)"),
            ("gbk", "GBK (中文)"),
            ("cp949", "CP949 (韓文擴展)"),
            ("latin-1", "Latin-1 (備用)"),
        ]

        content = None
        used_encoding = None

        for encoding, encoding_name in encodings_to_try:
            try:
                with open(self.filepath, "r", encoding=encoding) as f:
                    content = f.read().strip()
                    used_encoding = encoding_name
                    break
            except UnicodeDecodeError:
                continue

        # 如果所有編碼都失敗，使用UTF-8錯誤替換
        if content is None:
            with open(self.filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()
                used_encoding = "UTF-8 (錯誤替換)"

        # .t 文件應該只有一行，如果有多行則只取第一行
        lines = content.split("\n")
        self.original_content = lines[0] if lines else ""
        self.current_content = self.original_content

        # 記錄使用的編碼（用於調試）
        self.detected_encoding = used_encoding

        # 如果檢測到韓文字符，記錄日誌
        if any("\uac00" <= char <= "\ud7af" for char in self.original_content):
            print(f"檢測到韓文文本，使用編碼: {used_encoding}")

    def get_utf8_strings(self) -> List[Dict[str, Any]]:
        """
        獲取文本內容作為字符串條目

        Returns:
            包含單個字符串條目的列表
        """
        return [
            {
                "id": 0,
                "original": self.original_content,
                "translated": self.current_content,
                "line_number": 1,
                "file_path": self.filepath,
            }
        ]

    def update_utf8_string(self, index: int, new_string: str):
        """
        更新文本內容

        Args:
            index: 字符串索引（對於 .t 文件總是 0）
            new_string: 新的文本內容
        """
        if index != 0:
            raise IndexError(
                f"Text file only has one string (index 0), got index {index}"
            )

        # 確保新字符串是單行的
        new_string = new_string.replace("\n", " ").replace("\r", " ").strip()

        if self.current_content != new_string:
            self.current_content = new_string
            self.modified = True

    def save(self, output_path: str):
        """
        保存文本文件

        Args:
            output_path: 輸出文件路徑
        """
        try:
            # 創建備份（如果是覆蓋原文件）
            if output_path == self.filepath and os.path.exists(self.filepath):
                backup_path = self.filepath + ".bak"
                if not os.path.exists(backup_path):
                    import shutil

                    shutil.copy2(self.filepath, backup_path)

            # 保存文件
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(self.current_content)
                if not self.current_content.endswith("\n"):
                    f.write("\n")  # 確保文件以換行符結尾

            # 更新狀態
            if output_path == self.filepath:
                self.original_content = self.current_content
                self.modified = False

        except Exception as e:
            raise RuntimeError(f"Failed to save text file: {e}")

    def is_modified(self) -> bool:
        """檢查文件是否已修改"""
        return self.modified

    def get_content(self) -> str:
        """獲取當前內容"""
        return self.current_content

    def set_content(self, content: str):
        """設置內容"""
        self.update_utf8_string(0, content)

    def reset_content(self):
        """重置到原始內容"""
        self.current_content = self.original_content
        self.modified = False

    def get_file_info(self) -> Dict[str, Any]:
        """獲取文件信息"""
        try:
            stat = os.stat(self.filepath)
            return {
                "file_size": stat.st_size,
                "content_length": len(self.current_content),
                "original_length": len(self.original_content),
                "modified": self.modified,
                "encoding": "utf-8",
                "line_count": 1,
            }
        except Exception:
            return {"error": "Failed to get file info"}
