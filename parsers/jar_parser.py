"""
JAR文件解析器示例

這是一個示例解析器，展示如何擴展系統以支持新的文件類型。
實際的JAR解析需要更複雜的實現。
"""

import os
import zipfile
from typing import List, Dict, Any
from .base_parser import BaseParser


class JarParser(BaseParser):
    """JAR文件解析器示例類"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.strings_data: List[Dict[str, Any]] = []
        self.modified = False

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"JAR file not found: {filepath}")

        # 驗證是否為有效的ZIP/JAR文件
        try:
            with zipfile.ZipFile(filepath, "r") as jar:
                # 簡單驗證
                jar.testzip()
        except (zipfile.BadZipFile, zipfile.LargeZipFile) as e:
            raise ValueError(f"Invalid JAR file: {e}")

    def get_utf8_strings(self) -> List[Dict[str, Any]]:
        """
        從JAR文件中提取UTF-8字符串

        注意：這是一個簡化的示例實現
        實際的JAR解析需要：
        1. 解析class文件中的常量池
        2. 提取字符串常量
        3. 處理多個class文件
        """
        if self.strings_data:
            return self.strings_data

        strings = []

        try:
            with zipfile.ZipFile(self.filepath, "r") as jar:
                # 獲取所有.class文件
                class_files = [
                    name for name in jar.namelist() if name.endswith(".class")
                ]

                for i, class_file in enumerate(class_files):
                    # 這裡應該解析class文件的常量池
                    # 為了示例，我們創建一些模擬數據
                    strings.append(
                        {
                            "id": i,
                            "original": f"Sample string from {class_file}",
                            "translated": f"Sample string from {class_file}",  # 初始時與原文相同
                            "line_number": 0,
                            "class_file": class_file,
                        }
                    )

        except Exception as e:
            raise RuntimeError(f"Failed to parse JAR file: {e}")

        self.strings_data = strings
        return strings

    def update_utf8_string(self, index: int, new_string: str):
        """
        更新指定索引的UTF-8字符串

        Args:
            index: 字符串索引
            new_string: 新的字符串內容
        """
        if not self.strings_data:
            raise RuntimeError("No strings loaded. Call get_utf8_strings() first.")

        if index < 0 or index >= len(self.strings_data):
            raise IndexError(f"String index {index} out of range")

        if self.strings_data[index]["translated"] != new_string:
            self.strings_data[index]["translated"] = new_string
            self.modified = True

    def save(self, output_path: str):
        """
        保存修改後的JAR文件

        注意：這是一個簡化的示例實現
        實際的保存需要：
        1. 重新構建class文件的常量池
        2. 更新字符串常量
        3. 重新打包JAR文件
        """
        if not self.modified:
            return  # 沒有修改，無需保存

        try:
            # 這裡應該實現實際的JAR文件重構邏輯
            # 為了示例，我們只是複製原文件
            if output_path != self.filepath:
                import shutil

                shutil.copy2(self.filepath, output_path)

            print(f"JAR file saved to: {output_path}")
            print(
                f"Modified strings: {sum(1 for s in self.strings_data if s['original'] != s['translated'])}"
            )

            self.modified = False

        except Exception as e:
            raise RuntimeError(f"Failed to save JAR file: {e}")

    def get_file_info(self) -> Dict[str, Any]:
        """獲取JAR文件信息"""
        try:
            with zipfile.ZipFile(self.filepath, "r") as jar:
                info = jar.infolist()
                class_files = [f for f in info if f.filename.endswith(".class")]

                return {
                    "total_entries": len(info),
                    "class_files": len(class_files),
                    "file_size": os.path.getsize(self.filepath),
                    "compression": "ZIP_DEFLATED" if info else "Unknown",
                }
        except Exception:
            return {"error": "Failed to read JAR info"}
