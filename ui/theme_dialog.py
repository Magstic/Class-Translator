"""
主题选择对话框
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any
from core.services.theme_service import ThemeService


class ThemeDialog:
    """主题选择对话框"""
    
    def __init__(self, parent: tk.Tk, theme_service: ThemeService):
        self.parent = parent
        self.theme_service = theme_service
        self.result = None
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("主题设置")
        self.dialog.geometry("400x400")
        print(f"[DEBUG] 对话框尺寸設置為: 400x400")
        self.dialog.resizable(False, False)
        
        # 设置为模态对话框
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self._center_window()
        
        # 创建UI
        print("[DEBUG] 开始创建主题对话框UI")
        self._create_ui()
        print("[DEBUG] 主题对话框UI创建完成")
        
        # 绑定关闭事件
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def _center_window(self):
        """将对话框居中显示"""
        self.dialog.update_idletasks()
        
        # 获取对话框尺寸
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        # 获取父窗口位置和尺寸
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # 计算居中位置
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def _create_ui(self):
        """创建用户界面"""
        # Configure the main grid layout for the dialog itself
        self.dialog.grid_rowconfigure(0, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)

        # Main frame that holds all widgets
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid layout for the main_frame
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=0)  # Title
        main_frame.grid_rowconfigure(1, weight=1)  # Theme list (expandable)
        main_frame.grid_rowconfigure(2, weight=0)  # Preview
        main_frame.grid_rowconfigure(3, weight=0)  # Buttons
        
        # 标题
        title_label = ttk.Label(main_frame, text="选择主题", font=("Segoe UI", 12, "bold"))
        title_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # 主题列表框架（填充剩餘空間）
        list_frame = ttk.LabelFrame(main_frame, text="可用主题", padding="5")
        list_frame.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="nsew")
        
        # 创建主题创建列表
        self._create_theme_list(list_frame)
        
        # 按钮框架（優先放在底部）
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew")
        
        # 创建按钮
        self._create_buttons(button_frame)
    
    def _create_theme_list(self, parent):
        """创建主题列表"""
        # 创建列表框和滚动条
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 列表框
        self.theme_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
            font=("Segoe UI", 9)
        )
        self.theme_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.theme_listbox.yview)
        
        # 填充主题列表
        self.available_themes = self.theme_service.get_available_themes()
        current_theme = self.theme_service.get_current_theme()
        
        for theme_id, theme_name in self.available_themes.items():
            self.theme_listbox.insert(tk.END, f"{theme_name} ({theme_id})")
            
            # 选中当前主题
            if theme_id == current_theme:
                self.theme_listbox.selection_set(tk.END)
    
    def _create_buttons(self, parent):
        """创建按钮"""
        print("[DEBUG] _create_buttons 方法被调用")
        # 按钮容器填充整個框架
        button_container = ttk.Frame(parent)
        button_container.pack(fill=tk.X, pady=(10, 0))
        print("[DEBUG] 按钮容器创建完成")
        
        # 取消按钮（最左侧）
        print("[DEBUG] 开始创建取消按钮")
        cancel_button = ttk.Button(
            button_container,
            text="取消",
            command=self._on_cancel
        )
        cancel_button.pack(side=tk.RIGHT, padx=(0, 5))
        print(f"[DEBUG] 取消按钮创建完成: {cancel_button}")
        
        # 应用按钮（中间）
        print("[DEBUG] 开始创建应用按钮")
        apply_button = ttk.Button(
            button_container,
            text="应用",
            command=self._on_apply
        )
        apply_button.pack(side=tk.RIGHT, padx=(0, 5))
        print(f"[DEBUG] 应用按钮创建完成: {apply_button}")
        
        # 确定按钮（最右侧）
        print("[DEBUG] 开始创建确定按钮")
        ok_button = ttk.Button(
            button_container,
            text="确定",
            command=self._on_ok
        )
        ok_button.pack(side=tk.RIGHT, padx=(5, 0))
        print(f"[DEBUG] 确定按钮创建完成: {ok_button}")
        
        # 強制更新布局
        button_container.update_idletasks()
        print(f"[DEBUG] 所有按钮创建完成，按钮容器: {button_container}")
        print(f"[DEBUG] 按钮容器尺寸: {button_container.winfo_reqwidth()}x{button_container.winfo_reqheight()}")
    
    def _get_selected_theme_id(self) -> Optional[str]:
        """获取选中的主题ID"""
        selection = self.theme_listbox.curselection()
        if not selection:
            return None

        selected_text = self.theme_listbox.get(selection[0])
        # 列表框中的文本格式为 "DisplayName (theme_id)"
        # 我们需要从中提取出 theme_id, 例如, 从 "Azure-Dark (dark)" 中提取 "dark"
        try:
            start = selected_text.rindex('(')
            end = selected_text.rindex(')')
            if start != -1 and end != -1 and start < end:
                return selected_text[start + 1:end]
        except ValueError:
            pass  # 如果找不到'('或')'，则匹配失败

        self.logger.warning(f"无法从 '{selected_text}' 中解析主题ID")
        return None

    def _on_apply(self):
        """应用按钮处理"""
        theme_id = self._get_selected_theme_id()
        if theme_id:
            self.theme_service.apply_theme(theme_id)
    
    def _on_ok(self):
        """确定按钮处理"""
        theme_id = self._get_selected_theme_id()
        if theme_id:
            self.theme_service.apply_theme(theme_id)
            self.result = theme_id
        self.dialog.destroy()
    
    def _on_cancel(self):
        """取消按钮处理"""
        self.result = None
        self.dialog.destroy()
    
    def show(self) -> Optional[str]:
        """显示对话框并返回结果"""
        self.dialog.wait_window()
        return self.result


def show_theme_dialog(parent: tk.Tk, theme_service: ThemeService) -> Optional[str]:
    """显示主题选择对话框的便捷函数"""
    dialog = ThemeDialog(parent, theme_service)
    return dialog.show()
