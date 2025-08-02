"""
编辑器视图组件 - 负责原文和译文编辑区域的UI组件和逻辑
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Callable, Optional
from core.events import get_event_system
from core.services.theme_service import ThemeChangedEvent


class EditorView:
    """编辑器视图组件，管理原文和译文编辑区域"""

    def __init__(self, parent: tk.Widget, handlers: Dict[str, Callable]):
        """
        初始化编辑器视图
        
        Args:
            parent: 父容器组件
            handlers: 事件处理器字典，包含各种回调函数
        """
        self.parent = parent
        self.handlers = handlers
        self.highlight_var = tk.BooleanVar(value=True)
        
        # 创建编辑器UI组件
        self.frame = self._create_editor_frame()
        self._create_editor_widgets()
        
        # 订阅主题变更事件
        self.event_system = get_event_system()
        self.event_system.subscribe(ThemeChangedEvent, self._on_theme_changed)
        
    def _create_editor_frame(self) -> ttk.LabelFrame:
        """创建编辑器主框架"""
        frame = ttk.LabelFrame(self.parent, text="编辑", padding="5")
        return frame
        
    def _create_editor_widgets(self):
        """创建编辑器内部组件"""
        # 原文标签和文本框
        ttk.Label(self.frame, text="原文:").pack(anchor=tk.W)
        self.original_text = tk.Text(
            self.frame, height=5, state=tk.DISABLED, background="#f0f0f0"
        )
        self.original_text.pack(fill=tk.X, expand=True, pady=(0, 5))

        # 译文标签和文本框
        ttk.Label(self.frame, text="译文:").pack(anchor=tk.W)
        self.translated_text = tk.Text(self.frame, height=5)
        # 高亮樣式將在主題變更時動態配置
        # 初始化為淺色主題的高亮樣式
        self.translated_text.tag_configure("highlight", background="#E8F4FD", foreground="#1F5582")
        self.original_text.tag_configure("highlight", background="#E8F4FD", foreground="#1F5582")
        self.translated_text.pack(fill=tk.X, expand=True)
        
        # 绑定译文文本修改事件
        self.translated_text.bind(
            "<<Modified>>",
            lambda e: self._handle_text_modified(e)
        )

        # 添加实时文本变化事件处理
        def on_text_realtime_change(event):
            if self.handlers and "text_realtime_change" in self.handlers:
                self.handlers["text_realtime_change"](event)

        self.translated_text.bind("<KeyRelease>", on_text_realtime_change)
        self.translated_text.bind(
            "<Button-1>",
            lambda e: self.frame.after(10, lambda: on_text_realtime_change(e)),
        )

        # 按钮框架
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, pady=5)

        # 翻译按钮
        self.translate_button = ttk.Button(
            button_frame,
            text="翻译",
            command=lambda: self._handle_translate_command()
        )
        self.translate_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))

        # 应用修改按钮
        self.apply_button = ttk.Button(
            button_frame,
            text="应用修改",
            command=lambda: self._handle_apply_command()
        )
        self.apply_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))

        # 高亮切换复选框
        self.highlight_checkbox = ttk.Checkbutton(
            self.frame,
            text="荧光标注非 EUC-KR 字符",
            variable=self.highlight_var,
            command=lambda: self._handle_highlight_toggle()
        )
        self.highlight_checkbox.pack(anchor=tk.W, pady=5)

    def _handle_text_modified(self, event):
        """处理文本修改事件"""
        if self.handlers and "text_modified" in self.handlers:
            self.handlers["text_modified"](event)

    def _handle_translate_command(self):
        """处理翻译按钮点击"""
        if self.handlers and "translate_command" in self.handlers:
            self.handlers["translate_command"]()

    def _handle_apply_command(self):
        """处理应用修改按钮点击"""
        if self.handlers and "apply_command" in self.handlers:
            self.handlers["apply_command"]()

    def _handle_highlight_toggle(self):
        """处理高亮切换"""
        if self.handlers and "highlight_toggle" in self.handlers:
            self.handlers["highlight_toggle"]()

    # ==================== 公共接口方法 ====================

    def update_editor_text(self, original: str, translated: str):
        """更新编辑器文本内容"""
        # 更新原文
        self.original_text.config(state=tk.NORMAL)
        self.original_text.delete("1.0", tk.END)
        self.original_text.insert("1.0", original)
        self.original_text.config(state=tk.DISABLED)

        # 更新译文
        self.translated_text.delete("1.0", tk.END)
        self.translated_text.insert("1.0", translated)

    def clear_editor_text(self):
        """清空编辑器文本"""
        # 清空原文
        self.original_text.config(state=tk.NORMAL)
        self.original_text.delete("1.0", tk.END)
        self.original_text.config(state=tk.DISABLED)

        # 清空译文
        self.translated_text.delete("1.0", tk.END)

    def get_translated_text(self) -> str:
        """获取译文内容"""
        return self.translated_text.get("1.0", tk.END).strip()

    def update_text_highlights(self, ranges: List[tuple]):
        """更新文本高亮"""
        # 清除旧的高亮
        self.translated_text.tag_remove("highlight", "1.0", tk.END)
        if not ranges:
            return

        # 应用新的高亮
        for start, end in ranges:
            start_index = f"1.{start}"
            end_index = f"1.{end}"
            self.translated_text.tag_add("highlight", start_index, end_index)

    def set_apply_button_state(self, enabled: bool):
        """设置应用按钮状态"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.apply_button.config(state=state)


    
    def _on_theme_changed(self, event: ThemeChangedEvent):
        """响应主题变更事件"""
        try:
            colors = event.theme_config.get("colors", {})
            fonts = event.theme_config.get("fonts", {})
            
            # 更新原文文本框样式
            if hasattr(self, 'original_text'):
                self.original_text.configure(
                    bg=colors.get("disabled_bg", "#f0f0f0"),
                    fg=colors.get("disabled_fg", "#666666"),
                    font=fonts.get("text", ("Consolas", 10))
                )
            
            # 更新译文文本框样式
            if hasattr(self, 'translated_text'):
                self.translated_text.configure(
                    bg=colors.get("text_bg", "#ffffff"),
                    fg=colors.get("text_fg", "#000000"),
                    font=fonts.get("text", ("Consolas", 10))
                )
                
        except Exception as e:
            print(f"EditorView theme update failed: {e}")

    def get_highlight_enabled(self) -> bool:
        """获取高亮是否启用"""
        return self.highlight_var.get()

    def get_frame(self) -> ttk.LabelFrame:
        """获取主框架，用于布局"""
        return self.frame
