#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文件類型配置管理模塊
支持用戶自定義純文本文件擴展名
"""

import json
import os
from typing import List, Set
from pathlib import Path


class FileTypeConfig:
    """文件類型配置管理器"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.default_text_extensions = {".t", ".txt", ".text"}
        self.default_class_extensions = {".class"}

        # 當前配置
        self.text_extensions: Set[str] = set()
        self.class_extensions: Set[str] = set()

        # 加載配置
        self.load_config()

    def load_config(self):
        """從配置文件加載設置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

                # 加載純文本文件擴展名
                text_exts = config_data.get(
                    "text_file_extensions", list(self.default_text_extensions)
                )
                self.text_extensions = set(text_exts)

                # 加載CLASS文件擴展名（通常不變）
                class_exts = config_data.get(
                    "class_file_extensions", list(self.default_class_extensions)
                )
                self.class_extensions = set(class_exts)
            else:
                # 使用默認配置
                self.text_extensions = self.default_text_extensions.copy()
                self.class_extensions = self.default_class_extensions.copy()
                self.save_config()

        except Exception as e:
            print(f"加載配置失敗，使用默認配置: {e}")
            self.text_extensions = self.default_text_extensions.copy()
            self.class_extensions = self.default_class_extensions.copy()

    def save_config(self):
        """保存配置到文件"""
        try:
            config_data = {
                "text_file_extensions": list(self.text_extensions),
                "class_file_extensions": list(self.class_extensions),
            }

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"保存配置失敗: {e}")

    def is_text_file(self, filepath: str) -> bool:
        """檢查文件是否為純文本文件"""
        ext = Path(filepath).suffix.lower()
        return ext in self.text_extensions

    def is_class_file(self, filepath: str) -> bool:
        """檢查文件是否為CLASS文件"""
        ext = Path(filepath).suffix.lower()
        return ext in self.class_extensions

    def is_supported_file(self, filepath: str) -> bool:
        """檢查文件是否為支持的文件類型"""
        return self.is_text_file(filepath) or self.is_class_file(filepath)

    def get_file_type(self, filepath: str) -> str:
        """獲取文件類型"""
        if self.is_class_file(filepath):
            return "class"
        elif self.is_text_file(filepath):
            return "text"
        else:
            return "unknown"

    def add_text_extension(self, extension: str):
        """添加純文本文件擴展名"""
        if not extension.startswith("."):
            extension = "." + extension

        extension = extension.lower()
        self.text_extensions.add(extension)
        self.save_config()

    def remove_text_extension(self, extension: str):
        """移除純文本文件擴展名"""
        if not extension.startswith("."):
            extension = "." + extension

        extension = extension.lower()
        self.text_extensions.discard(extension)
        self.save_config()

    def get_text_extensions(self) -> List[str]:
        """獲取純文本文件擴展名列表"""
        return sorted(list(self.text_extensions))

    def get_class_extensions(self) -> List[str]:
        """獲取CLASS文件擴展名列表"""
        return sorted(list(self.class_extensions))

    def reset_to_defaults(self):
        """重置為默認配置"""
        self.text_extensions = self.default_text_extensions.copy()
        self.class_extensions = self.default_class_extensions.copy()
        self.save_config()

    def get_supported_files_in_directory(self, directory: str) -> dict:
        """獲取目錄中支持的文件，按類型分組"""
        result = {"text": [], "class": [], "unknown": []}

        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    filepath = os.path.join(root, file)
                    file_type = self.get_file_type(filepath)
                    result[file_type].append(filepath)

        except Exception as e:
            print(f"掃描目錄失敗: {e}")

        return result

    def __str__(self):
        return f"FileTypeConfig(text={self.text_extensions}, class={self.class_extensions})"


# 全局配置實例
_global_config = None


def get_file_type_config() -> FileTypeConfig:
    """獲取全局文件類型配置實例"""
    global _global_config
    if _global_config is None:
        _global_config = FileTypeConfig()
    return _global_config
