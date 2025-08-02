"""
主题服务 - 负责管理应用程序的主题和样式 (使用 Azure-ttk-theme)
"""

import os
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional
import logging
from ..events import get_event_system
from ..events.theme_events import ThemeChangedEvent


class ThemeService:
    """使用 Azure TTK Theme 管理应用程序主题的服务"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.logger = logging.getLogger(__name__)
        self.event_system = get_event_system()
        self._current_theme: str = "light"  # 默认主题

        self._theme_definitions = {
            "light": {
                "display_name": "Azure Light",
                "non_ttk_styles": {
                    "Text": {"background": "#FFFFFF", "foreground": "#000000", "insertbackground": "#000000"},
                    "Highlight": {"background": "#E8F4FD", "foreground": "#1F5582"}  # 淺藍色高亮，更柔和
                }
            },
            "dark": {
                "display_name": "Azure Dark",
                "non_ttk_styles": {
                    "Text": {"background": "#2E2E2E", "foreground": "#FFFFFF", "insertbackground": "#FFFFFF"},
                    "Highlight": {"background": "#3D5A80", "foreground": "#E0E6ED"}  # 深藍灰色高亮，護眼
                }
            }
        }

        # 加载 Azure TTK theme
        try:
            # 假设 Azure-ttk-theme-main 与 CLASS編輯器 在同一目录下
            base_dir = os.path.dirname(os.path.dirname(__file__))
            theme_path = os.path.join(base_dir, "Azure-ttk-theme-main", "azure.tcl")
            
            if not os.path.exists(theme_path):
                 # 如果不在上一级，就假设在当前目录
                 base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                 theme_path = os.path.join(base_dir, "Azure-ttk-theme-main", "azure.tcl")

            self.root.tk.call("source", theme_path)
            self.logger.info(f"Azure TTK 主题已从 {theme_path} 加载")
        except tk.TclError as e:
            self.logger.error(f"加载 Azure TTK 主题失败: {e}")
            return
        except FileNotFoundError:
            self.logger.error(f"Azure TTK 主题文件未找到: {theme_path}")
            return

        self._apply_default_theme()

    def get_available_themes(self) -> Dict[str, str]:
        """获取可用主题列表"""
        return {name: data["display_name"] for name, data in self._theme_definitions.items()}

    def get_current_theme(self) -> str:
        """获取当前主题名称"""
        return self._current_theme

    def apply_theme(self, theme_name: str):
        """应用指定的主题 ('light' 或 'dark')"""
        if theme_name not in ["light", "dark"]:
            self.logger.warning(f"不支持 Azure 主题 '{theme_name}'。请使用 'light' 或 'dark'。")
            return

        try:
            self.root.tk.call("set_theme", theme_name)
            self._current_theme = theme_name
            
            # 发布主题变更事件，以便UI的其他部分可以做出响应（如果需要）
            # Azure主题会自动处理大部分样式，但事件可能对自定义组件有用
            theme_data = self._theme_definitions.get(theme_name, {})
            self.event_system.publish(
                ThemeChangedEvent(source=self, theme_name=theme_name, theme_data=theme_data)
            )
            self.logger.info(f"Azure 主题已应用: {theme_name}")
        except tk.TclError as e:
            self.logger.error(f"设置 Azure 主题 '{theme_name}' 失败: {e}")

    def _apply_default_theme(self):
        """应用默认主题"""
        self.apply_theme("light")

    def get_current_theme_data(self) -> Optional[Dict[str, Any]]:
        """获取当前主題的样式数据"""
        return self._theme_definitions.get(self._current_theme, {})

    def get_current_highlight_styles(self) -> Optional[Dict[str, str]]:
        """获取当前主題的高亮样式，供新创建的组件使用"""
        theme_data = self.get_current_theme_data()
        if theme_data:
            non_ttk_styles = theme_data.get("non_ttk_styles", {})
            return non_ttk_styles.get("Highlight")
        return None

    def get_color(self, color_key: str, default: str = "#000000") -> str:
        """此方法已弃用，因为颜色由Azure主题管理。返回默认值。"""
        # self.logger.debug(f"get_color('{color_key}') is deprecated with Azure theme.")
        return default

    def get_font(self, font_key: str, default: tuple = ("Segoe UI", 9)) -> tuple:
        """此方法已弃用，因为字体由Azure主题管理。返回默认值。"""
        # self.logger.debug(f"get_font('{font_key}') is deprecated with Azure theme.")
        return default
