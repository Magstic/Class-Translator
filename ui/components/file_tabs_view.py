"""
文件标签页视图组件 - 负责文件标签页和树状视图的UI组件和逻辑
"""

import os
import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Callable, Optional, Any
from core.models import StringEntry
from core.events import get_event_system
from core.services.theme_service import ThemeChangedEvent


class FileTabsView:
    """文件标签页视图组件，管理文件标签页和树状视图"""

    def __init__(self, parent: tk.Widget, handlers: Dict[str, Callable]):
        """
        初始化文件标签页视图
        
        Args:
            parent: 父容器组件
            handlers: 事件处理器字典，包含各种回调函数
        """
        self.parent = parent
        self.handlers = handlers
        self.tabs = {}  # 映射文件路径到标签页信息的字典
        
        # 创建UI组件
        self.frame = self._create_tabs_frame()
        self._create_notebook_widget()
        
        # 订阅主题变更事件
        self.event_system = get_event_system()
        self.event_system.subscribe(ThemeChangedEvent, self._on_theme_changed)
        
    def _create_tabs_frame(self) -> ttk.LabelFrame:
        """创建文件标签页主框架"""
        frame = ttk.LabelFrame(self.parent, text="字符串列表", padding="5")
        return frame
        
    def _create_notebook_widget(self):
        """创建 Notebook组件"""
        # 创建 Notebook控件
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(expand=True, fill="both")
        
        # 绑定标签页切换事件
        self.notebook.bind(
            "<<NotebookTabChanged>>",
            lambda e: self._handle_tab_changed(e)
        )

    def _handle_tab_changed(self, event):
        """处理标签页切换事件"""
        if self.handlers and "tab_changed" in self.handlers:
            self.handlers["tab_changed"](event)

    def _handle_tree_select(self, event):
        """处理树状视图选择事件"""
        if self.handlers and "tree_select" in self.handlers:
            self.handlers["tree_select"](event)

    # ==================== 公共接口方法 ====================

    def clear_tree(self):
        """清空所有标签页"""
        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)
        self.tabs.clear()

    def add_file_tab(self, filepath: str, data: List[StringEntry]) -> Any:
        """
        创建新的文件标签页
        
        Args:
            filepath: 文件路径
            data: 字符串数据列表
            
        Returns:
            创建的树状视图控件
        """
        # 创建标签页框架
        tab_frame = ttk.Frame(self.notebook)
        filename = os.path.basename(filepath)
        self.notebook.add(tab_frame, text=filename)

        # 创建树状视图
        tree = ttk.Treeview(
            tab_frame, columns=("ID", "Original", "Translated"), show="headings"
        )
        tree.heading("ID", text="ID")
        tree.heading("Original", text="原文")
        tree.heading("Translated", text="譯文")
        tree.column("ID", width=50, stretch=tk.NO)
        tree.column("Original", width=300)
        tree.column("Translated", width=300)

        # 高亮樣式將在主題變更時動態配置
        # 初始化為淺色主題的高亮樣式
        tree.tag_configure("highlighted", background="#E8F4FD", foreground="#1F5582")

        # 创建垂直滚动条
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # 使用grid布局，让滚动条和treeview正确缩放
        tab_frame.grid_rowconfigure(0, weight=1)
        tab_frame.grid_columnconfigure(0, weight=1)
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # 填充数据
        for item in data:
            tree.insert(
                "",
                tk.END,
                iid=str(item.id),
                values=(item.id, item.original, item.translated),
            )

        # 保存标签页信息
        self.tabs[filepath] = {"frame": tab_frame, "tree": tree, "scrollbar": scrollbar}

        # 绑定树选择事件
        tree.bind("<<TreeviewSelect>>", lambda event: self._handle_tree_select(event))

        return tree

    def get_current_treeview(self) -> Optional[Any]:
        """获取当前活动标签页的树状视图"""
        try:
            current_tab_frame = self.notebook.nametowidget(self.notebook.select())
            for info in self.tabs.values():
                if info["frame"] == current_tab_frame:
                    return info["tree"]
        except tk.TclError:
            return None
        return None

    def get_current_filepath(self) -> Optional[str]:
        """获取当前活动标签页的文件路径"""
        try:
            current_tab_frame = self.notebook.nametowidget(self.notebook.select())
            for path, info in self.tabs.items():
                if info["frame"] == current_tab_frame:
                    return path
        except tk.TclError:
            return None
        return None

    def get_tree_for_file(self, filepath: str) -> Optional[Any]:
        """获取指定文件的树状视图"""
        if filepath in self.tabs:
            return self.tabs[filepath]["tree"]
        return None

    def get_selected_tree_item_id(self) -> Optional[int]:
        """获取当前选中的树状视图项目ID"""
        tree = self.get_current_treeview()
        if not tree:
            return None
        selection = tree.selection()
        if not selection:
            return None
        item = tree.item(selection[0])
        return int(item["values"][0])

    def get_all_selected_tree_item_ids(self) -> List[int]:
        """获取所有选中的树状视图项目ID列表"""
        tree = self.get_current_treeview()
        if not tree:
            return []
        selection = tree.selection()
        if not selection:
            return []
        ids = []
        for selected_item_iid in selection:
            item = tree.item(selected_item_iid)
            ids.append(int(item["values"][0]))
        return ids

    def update_tree_item(self, item_id: int, translated_text: str):
        """更新树状视图项目的译文"""
        tree = self.get_current_treeview()
        if tree:
            tree.set(str(item_id), "Translated", translated_text)

    def highlight_tree_row(self, item_id: int, highlight: bool):
        """设置树状视图行的高亮状态"""
        tree = self.get_current_treeview()
        if not tree:
            return
        try:
            current_tags = tree.item(str(item_id), "tags")
            new_tags = list(current_tags)
            if highlight and "highlighted" not in new_tags:
                new_tags.append("highlighted")
            elif not highlight and "highlighted" in new_tags:
                new_tags.remove("highlighted")

            tree.item(str(item_id), tags=tuple(new_tags))
        except tk.TclError:
            # 项目不可见或树正在更新时可能发生
            pass

    def select_tree_items(self, item_ids: List[int]):
        """选中指定的树状视图项目列表"""
        tree = self.get_current_treeview()
        if tree:
            tree.selection_set([])  # 清除现有选择
            for item_id in item_ids:
                tree.selection_add(str(item_id))

        if item_ids:
            tree = self.get_current_treeview()
            if tree:
                tree.see(str(item_ids[0]))  # 滚动到第一个找到的项目

    def get_frame(self) -> ttk.LabelFrame:
        """获取主框架，用于布局"""
        return self.frame
    
    def _on_theme_changed(self, event: ThemeChangedEvent):
        """响应主题变更事件"""
        try:
            colors = event.theme_config.get("colors", {})
            fonts = event.theme_config.get("fonts", {})
            
            # 更新所有TreeView的样式
            for file_path, tab_info in self.tabs.items():
                tree = tab_info.get("tree")
                if tree:
                    # 更新TreeView样式
                    tree.configure(
                        font=fonts.get("default", ("Segoe UI", 9))
                    )
                    
                    # 更新高亮样式
                    tree.tag_configure(
                        "highlighted",
                        background=colors.get("highlight_bg", "#ffff00"),
                        foreground=colors.get("highlight_fg", "#000000")
                    )
                    
        except Exception as e:
            print(f"FileTabsView theme update failed: {e}")
    

