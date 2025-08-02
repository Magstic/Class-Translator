import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from core.config.file_type_config import get_file_type_config


class FileTypeConfigDialog:
    """文件類型配置對話框"""

    def __init__(self, parent: tk.Tk):
        self.parent = parent
        self.config = get_file_type_config()
        self.result = None

        # 創建對話框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("文件類型配置")
        self.dialog.geometry("500x400")
        self.dialog.resizable(True, True)

        # 設置為模態對話框
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中顯示
        self._center_window()

        # 創建UI
        self._create_ui()

        # 加載當前配置
        self._load_current_config()

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
        main_frame.columnconfigure(1, weight=1)

        # 純文本文件擴展名配置
        ttk.Label(main_frame, text="純文本文件擴展名:").grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5)
        )

        text_frame = ttk.Frame(main_frame)
        text_frame.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10)
        )
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        # 純文本文件列表
        self.text_listbox = tk.Listbox(text_frame, height=6)
        self.text_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        text_scrollbar = ttk.Scrollbar(
            text_frame, orient=tk.VERTICAL, command=self.text_listbox.yview
        )
        text_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.text_listbox.configure(yscrollcommand=text_scrollbar.set)

        # 純文本文件操作按鈕
        text_button_frame = ttk.Frame(text_frame)
        text_button_frame.grid(row=0, column=2, sticky=(tk.N, tk.S), padx=(10, 0))

        ttk.Button(
            text_button_frame, text="添加", command=self._add_text_extension
        ).pack(pady=(0, 5))
        ttk.Button(
            text_button_frame, text="刪除", command=self._remove_text_extension
        ).pack(pady=(0, 5))
        ttk.Button(
            text_button_frame, text="重置", command=self._reset_text_extensions
        ).pack()

        # 分隔線
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10
        )

        # CLASS文件擴展名配置（只讀顯示）
        ttk.Label(main_frame, text="CLASS文件擴展名 (只讀):").grid(
            row=3, column=0, sticky=tk.W, pady=(0, 5)
        )

        class_frame = ttk.Frame(main_frame)
        class_frame.grid(
            row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10)
        )
        class_frame.columnconfigure(0, weight=1)
        class_frame.rowconfigure(0, weight=1)

        # CLASS文件列表（只讀）
        self.class_listbox = tk.Listbox(class_frame, height=3, state=tk.DISABLED)
        self.class_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        class_scrollbar = ttk.Scrollbar(
            class_frame, orient=tk.VERTICAL, command=self.class_listbox.yview
        )
        class_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.class_listbox.configure(yscrollcommand=class_scrollbar.set)

        # 說明文字
        info_label = ttk.Label(
            main_frame,
            text="注意：CLASS文件擴展名不可修改，以確保向後兼容性。",
            foreground="gray",
        )
        info_label.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # 按鈕框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(
            row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0)
        )

        ttk.Button(button_frame, text="確定", command=self._on_ok).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        ttk.Button(button_frame, text="取消", command=self._on_cancel).pack(
            side=tk.RIGHT
        )

        # 配置網格權重
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)

    def _load_current_config(self):
        """加載當前配置"""
        # 加載純文本文件擴展名
        text_extensions = self.config.get_text_extensions()
        for ext in text_extensions:
            self.text_listbox.insert(tk.END, ext)

        # 加載CLASS文件擴展名（只讀顯示）
        class_extensions = self.config.get_class_extensions()
        for ext in class_extensions:
            self.class_listbox.insert(tk.END, ext)

    def _add_text_extension(self):
        """添加純文本文件擴展名"""
        dialog = ExtensionInputDialog(self.dialog, "添加純文本文件擴展名")
        extension = dialog.show()

        if extension:
            # 確保擴展名以點開頭
            if not extension.startswith("."):
                extension = "." + extension

            # 檢查是否已存在
            current_extensions = [
                self.text_listbox.get(i) for i in range(self.text_listbox.size())
            ]
            if extension in current_extensions:
                messagebox.showwarning("警告", f"擴展名 {extension} 已存在！")
                return

            # 檢查是否與CLASS文件擴展名衝突
            class_extensions = self.config.get_class_extensions()
            if extension in class_extensions:
                messagebox.showerror(
                    "錯誤", f"擴展名 {extension} 與CLASS文件擴展名衝突！"
                )
                return

            # 添加到列表
            self.text_listbox.insert(tk.END, extension)

    def _remove_text_extension(self):
        """刪除純文本文件擴展名"""
        selection = self.text_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "請先選擇要刪除的擴展名！")
            return

        # 從後往前刪除，避免索引變化
        for index in reversed(selection):
            self.text_listbox.delete(index)

    def _reset_text_extensions(self):
        """重置純文本文件擴展名為默認值"""
        if messagebox.askyesno("確認", "確定要重置純文本文件擴展名為默認值嗎？"):
            self.text_listbox.delete(0, tk.END)
            default_extensions = [".t", ".txt", ".text"]
            for ext in default_extensions:
                self.text_listbox.insert(tk.END, ext)

    def _on_ok(self):
        """確定按鈕處理"""
        try:
            # 獲取當前純文本文件擴展名
            text_extensions = [
                self.text_listbox.get(i) for i in range(self.text_listbox.size())
            ]

            # 驗證擴展名格式
            for ext in text_extensions:
                if not ext.startswith(".") or len(ext) < 2:
                    messagebox.showerror("錯誤", f"無效的擴展名格式: {ext}")
                    return

            # 更新配置
            self.config.set_text_extensions(text_extensions)
            self.config.save_config()

            self.result = True
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("錯誤", f"保存配置失敗: {str(e)}")

    def _on_cancel(self):
        """取消按鈕處理"""
        self.result = False
        self.dialog.destroy()

    def show(self) -> bool:
        """顯示對話框並返回結果"""
        self.dialog.wait_window()
        return self.result or False


class ExtensionInputDialog:
    """擴展名輸入對話框"""

    def __init__(self, parent: tk.Toplevel, title: str):
        self.parent = parent
        self.result = None

        # 創建對話框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("300x120")
        self.dialog.resizable(False, False)

        # 設置為模態對話框
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中顯示
        self._center_window()

        # 創建UI
        self._create_ui()

        # 綁定事件
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.entry.bind("<Return>", lambda e: self._on_ok())

        # 聚焦到輸入框
        self.entry.focus_set()

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
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 輸入框
        ttk.Label(main_frame, text="請輸入文件擴展名:").pack(anchor=tk.W, pady=(0, 5))

        entry_frame = ttk.Frame(main_frame)
        entry_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(entry_frame, text=".").pack(side=tk.LEFT)
        self.entry = ttk.Entry(entry_frame)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 按鈕
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="確定", command=self._on_ok).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        ttk.Button(button_frame, text="取消", command=self._on_cancel).pack(
            side=tk.RIGHT
        )

    def _on_ok(self):
        """確定按鈕處理"""
        extension = self.entry.get().strip()
        if not extension:
            messagebox.showwarning("警告", "請輸入擴展名！")
            return

        # 移除開頭的點（如果有）
        if extension.startswith("."):
            extension = extension[1:]

        # 驗證擴展名格式
        if not extension or not extension.replace("_", "").replace("-", "").isalnum():
            messagebox.showerror("錯誤", "擴展名只能包含字母、數字、下劃線和連字符！")
            return

        self.result = extension
        self.dialog.destroy()

    def _on_cancel(self):
        """取消按鈕處理"""
        self.result = None
        self.dialog.destroy()

    def show(self) -> Optional[str]:
        """顯示對話框並返回結果"""
        self.dialog.wait_window()
        return self.result
