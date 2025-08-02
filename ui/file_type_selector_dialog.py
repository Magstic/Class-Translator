import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional
import os


class FileTypeSelectorDialog:
    """文件類型選擇對話框"""

    def __init__(
        self, parent: tk.Tk, directory_path: str, files_by_type: Dict[str, List[str]]
    ):
        self.parent = parent
        self.directory_path = directory_path
        self.files_by_type = files_by_type
        self.result = None

        # 創建對話框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("選擇要加載的文件類型")
        self.dialog.geometry("600x500")
        self.dialog.resizable(True, True)

        # 設置為模態對話框
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中顯示
        self._center_window()

        # 創建UI
        self._create_ui()

        # 綁定關閉事件
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _center_window(self):
        """將對話框居中顯示"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _create_ui(self):
        """創建用戶界面"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置網格權重
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # 標題和目錄信息
        title_label = ttk.Label(
            main_frame, text="在以下目錄中發現了多種文件類型:", font=("", 10, "bold")
        )
        title_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        dir_label = ttk.Label(
            main_frame, text=f"目錄: {self.directory_path}", foreground="blue"
        )
        dir_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 15))

        # 文件類型選擇區域
        selection_frame = ttk.LabelFrame(
            main_frame, text="請選擇要加載的文件類型", padding="10"
        )
        selection_frame.grid(
            row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15)
        )
        selection_frame.columnconfigure(0, weight=1)
        selection_frame.rowconfigure(0, weight=1)

        # 創建Notebook來組織不同文件類型
        self.notebook = ttk.Notebook(selection_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 存儲複選框變量
        self.type_vars = {}
        self.file_vars = {}

        # 為每種文件類型創建標籤頁
        self._create_file_type_tabs()

        # 快速選擇按鈕
        quick_frame = ttk.Frame(selection_frame)
        quick_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        ttk.Button(quick_frame, text="全選", command=self._select_all).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(quick_frame, text="全不選", command=self._select_none).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(
            quick_frame, text="僅選擇CLASS文件", command=self._select_class_only
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            quick_frame, text="僅選擇文本文件", command=self._select_text_only
        ).pack(side=tk.LEFT)

        # 統計信息
        self._create_statistics_frame(main_frame)

        # 按鈕框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        ttk.Button(button_frame, text="加載選中的文件", command=self._on_ok).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        ttk.Button(button_frame, text="取消", command=self._on_cancel).pack(
            side=tk.RIGHT
        )

    def _create_file_type_tabs(self):
        """創建文件類型標籤頁"""
        # 按類型順序：class, text, unknown
        type_order = ["class", "text", "unknown"]
        type_names = {"class": "CLASS文件", "text": "純文本文件", "unknown": "未知文件"}

        for file_type in type_order:
            if file_type not in self.files_by_type or not self.files_by_type[file_type]:
                continue

            files = self.files_by_type[file_type]

            # 創建標籤頁框架
            tab_frame = ttk.Frame(self.notebook)
            self.notebook.add(tab_frame, text=f"{type_names[file_type]} ({len(files)})")

            # 配置網格權重
            tab_frame.columnconfigure(0, weight=1)
            tab_frame.rowconfigure(1, weight=1)

            # 類型選擇複選框
            type_var = tk.BooleanVar(value=True)  # 默認選中
            self.type_vars[file_type] = type_var

            type_check = ttk.Checkbutton(
                tab_frame,
                text=f"選擇所有{type_names[file_type]}",
                variable=type_var,
                command=lambda ft=file_type: self._on_type_toggle(ft),
            )
            type_check.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

            # 文件列表框架
            list_frame = ttk.Frame(tab_frame)
            list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            list_frame.columnconfigure(0, weight=1)
            list_frame.rowconfigure(0, weight=1)

            # 創建Treeview來顯示文件列表
            tree = ttk.Treeview(
                list_frame, columns=("path", "size"), show="tree headings", height=10
            )
            tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

            # 配置列
            tree.heading("#0", text="文件名")
            tree.heading("path", text="路徑")
            tree.heading("size", text="大小")

            tree.column("#0", width=200)
            tree.column("path", width=300)
            tree.column("size", width=80)

            # 添加滾動條
            scrollbar = ttk.Scrollbar(
                list_frame, orient=tk.VERTICAL, command=tree.yview
            )
            scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
            tree.configure(yscrollcommand=scrollbar.set)

            # 存儲文件變量和樹狀視圖
            self.file_vars[file_type] = {}

            # 添加文件到樹狀視圖
            for file_path in sorted(files):
                filename = os.path.basename(file_path)
                relative_path = os.path.relpath(file_path, self.directory_path)

                # 獲取文件大小
                try:
                    size = os.path.getsize(file_path)
                    size_str = self._format_file_size(size)
                except (OSError, IOError):
                    size_str = "未知"

                # 插入項目
                tree.insert("", tk.END, text=filename, values=(relative_path, size_str))

                # 存儲文件變量（默認選中）
                file_var = tk.BooleanVar(value=True)
                self.file_vars[file_type][file_path] = file_var

            # 綁定雙擊事件來切換選擇
            tree.bind(
                "<Double-1>",
                lambda e, ft=file_type, t=tree: self._on_file_double_click(ft, t, e),
            )

    def _create_statistics_frame(self, parent):
        """創建統計信息框架"""
        stats_frame = ttk.LabelFrame(parent, text="統計信息", padding="10")
        stats_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # 統計標籤
        self.stats_label = ttk.Label(stats_frame, text="")
        self.stats_label.pack()

        # 更新統計信息
        self._update_statistics()

    def _update_statistics(self):
        """更新統計信息"""
        total_files = sum(len(files) for files in self.files_by_type.values())
        selected_files = 0

        stats_parts = []
        for file_type, files in self.files_by_type.items():
            if not files:
                continue

            type_selected = sum(
                1
                for file_path in files
                if self.file_vars.get(file_type, {})
                .get(file_path, tk.BooleanVar())
                .get()
            )
            selected_files += type_selected

            type_names = {"class": "CLASS", "text": "文本", "unknown": "未知"}

            stats_parts.append(
                f"{type_names.get(file_type, file_type)}: {type_selected}/{len(files)}"
            )

        stats_text = f"總計: {selected_files}/{total_files} 個文件  |  " + "  |  ".join(
            stats_parts
        )
        self.stats_label.config(text=stats_text)

    def _format_file_size(self, size: int) -> str:
        """格式化文件大小"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

    def _on_type_toggle(self, file_type: str):
        """處理文件類型複選框切換"""
        type_selected = self.type_vars[file_type].get()

        # 更新該類型下所有文件的選擇狀態
        for file_path in self.file_vars.get(file_type, {}):
            self.file_vars[file_type][file_path].set(type_selected)

        self._update_statistics()

    def _on_file_double_click(self, file_type: str, tree: ttk.Treeview, event):
        """處理文件雙擊事件"""
        selection = tree.selection()
        if not selection:
            return

        item = selection[0]
        values = tree.item(item, "values")
        if not values:
            return

        relative_path = values[0]
        file_path = os.path.join(self.directory_path, relative_path)

        # 切換文件選擇狀態
        if file_path in self.file_vars.get(file_type, {}):
            current_value = self.file_vars[file_type][file_path].get()
            self.file_vars[file_type][file_path].set(not current_value)
            self._update_statistics()

    def _select_all(self):
        """全選所有文件"""
        for file_type in self.type_vars:
            self.type_vars[file_type].set(True)
            for file_path in self.file_vars.get(file_type, {}):
                self.file_vars[file_type][file_path].set(True)
        self._update_statistics()

    def _select_none(self):
        """全不選"""
        for file_type in self.type_vars:
            self.type_vars[file_type].set(False)
            for file_path in self.file_vars.get(file_type, {}):
                self.file_vars[file_type][file_path].set(False)
        self._update_statistics()

    def _select_class_only(self):
        """僅選擇CLASS文件"""
        for file_type in self.type_vars:
            selected = file_type == "class"
            self.type_vars[file_type].set(selected)
            for file_path in self.file_vars.get(file_type, {}):
                self.file_vars[file_type][file_path].set(selected)
        self._update_statistics()

    def _select_text_only(self):
        """僅選擇文本文件"""
        for file_type in self.type_vars:
            selected = file_type == "text"
            self.type_vars[file_type].set(selected)
            for file_path in self.file_vars.get(file_type, {}):
                self.file_vars[file_type][file_path].set(selected)
        self._update_statistics()

    def _on_ok(self):
        """確定按鈕處理"""
        # 收集選中的文件
        selected_files = []

        for file_type, file_vars in self.file_vars.items():
            for file_path, var in file_vars.items():
                if var.get():
                    selected_files.append(file_path)

        if not selected_files:
            tk.messagebox.showwarning("警告", "請至少選擇一個文件！")
            return

        self.result = selected_files
        self.dialog.destroy()

    def _on_cancel(self):
        """取消按鈕處理"""
        self.result = None
        self.dialog.destroy()

    def show(self) -> Optional[List[str]]:
        """顯示對話框並返回選中的文件列表"""
        self.dialog.wait_window()
        return self.result
