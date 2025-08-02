import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import collections
from typing import List, Optional, Any
from .interfaces.imain_window import IMainWindow
from .components.editor_view import EditorView
from .components.file_tabs_view import FileTabsView
from core.events import (
    get_event_system,
    StatusBarUpdateEvent,
    InfoDialogEvent,
    ErrorDialogEvent,
    WarningDialogEvent,
    TreeItemUpdateEvent,
    TreeItemHighlightEvent,
    EditorTextUpdateEvent,
    EditorClearEvent,
    TextHighlightUpdateEvent,
    ApplyButtonStateEvent,
    TreeSelectionEvent,
    ThemeChangedEvent,
)
from core.models import StringEntry


class MainWindow(IMainWindow):
    """主窗口协调者，负责组件协调和事件分发"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.handlers = None  # Will be set by set_event_handlers
        self.status_var = tk.StringVar()
        
        # UI组件将在setup_ui中初始化
        self.editor_view = None
        self.file_tabs_view = None

        # 订阅事件系统
        self.event_system = get_event_system()
        self._subscribe_to_events()

    def set_event_handlers(self, handlers):
        """Sets the event handlers for the UI components."""
        self.handlers = handlers
        # 不再需要lambda佔位符，直接使用命令模式

    def setup_ui(self):
        self._create_menu_bar()
        self._create_main_layout()
        self._create_status_bar()
        self._setup_keyboard_shortcuts()  # 設置快捷鍵
        self.disable_file_operations()  # Start in a disabled state

    def _subscribe_to_events(self):
        """訂閱UI相關事件"""
        self.event_system.subscribe(
            "status_bar_update", self._on_status_bar_update_event
        )
        self.event_system.subscribe("info_dialog", self._on_info_dialog_event)
        self.event_system.subscribe("error_dialog", self._on_error_dialog_event)
        self.event_system.subscribe("warning_dialog", self._on_warning_dialog_event)
        self.event_system.subscribe("tree_item_update", self._on_tree_item_update_event)
        self.event_system.subscribe(
            "tree_item_highlight", self._on_tree_item_highlight_event
        )
        self.event_system.subscribe(
            "editor_text_update", self._on_editor_text_update_event
        )
        self.event_system.subscribe("editor_clear", self._on_editor_clear_event)
        self.event_system.subscribe(
            "text_highlight_update", self._on_text_highlight_update_event
        )
        self.event_system.subscribe(
            "apply_button_state", self._on_apply_button_state_event
        )
        self.event_system.subscribe("tree_selection", self._on_tree_selection_event)
        self.event_system.subscribe("theme_changed", self._on_theme_changed_event)
        print(f"[DEBUG] MainWindow已訂閱theme_changed事件")

    # ==================== 事件處理方法 ====================

    def _on_status_bar_update_event(self, event: StatusBarUpdateEvent):
        """處理狀態欄更新事件"""
        self.update_status_bar(event.message)

    def _on_info_dialog_event(self, event: InfoDialogEvent):
        """處理信息對話框事件"""
        self.show_info_dialog(event.title, event.message)

    def _on_error_dialog_event(self, event: ErrorDialogEvent):
        """處理錯誤對話框事件"""
        self.show_error_dialog(event.title, event.message)

    def _on_warning_dialog_event(self, event: WarningDialogEvent):
        """處理警告對話框事件"""
        self.show_warning_dialog(event.title, event.message)

    def _on_tree_item_update_event(self, event: TreeItemUpdateEvent):
        """處理樹狀視圖項目更新事件"""
        self.update_tree_item(event.item_id, event.translated_text)

    def _on_tree_item_highlight_event(self, event: TreeItemHighlightEvent):
        """處理樹狀視圖項目高亮事件"""
        self.highlight_tree_row(event.item_id, event.highlight)

    def _on_editor_text_update_event(self, event: EditorTextUpdateEvent):
        """處理編輯器文本更新事件"""
        self.update_editor_text(event.original, event.translated)

    def _on_editor_clear_event(self, event: EditorClearEvent):
        """處理編輯器清空事件"""
        self.clear_editor_text()

    def _on_text_highlight_update_event(self, event: TextHighlightUpdateEvent):
        """處理文本高亮更新事件"""
        self.update_text_highlights(event.ranges)

    def _on_apply_button_state_event(self, event: ApplyButtonStateEvent):
        """處理應用按鈕狀態事件"""
        self.set_apply_button_state(event.enabled)

    def _on_tree_selection_event(self, event: TreeSelectionEvent):
        """處理樹狀視圖選擇事件"""
        self.select_tree_items(event.item_ids)

    def _on_theme_changed_event(self, event: 'ThemeChangedEvent'):
        """處理主題變更事件，手動更新不被ttk主題影響的標準控件"""
        print(f"[DEBUG] MainWindow收到主題變更事件: {event.theme_name}")

        theme_data = event.theme_data
        non_ttk_styles = theme_data.get("non_ttk_styles", {})

        text_styles = non_ttk_styles.get("Text")
        highlight_styles = non_ttk_styles.get("Highlight")

        if self.editor_view and text_styles and highlight_styles:
            # 更新文本框顏色
            self.editor_view.original_text.config(
                bg=text_styles.get("background", "white"),
                fg=text_styles.get("foreground", "black"),
                insertbackground=text_styles.get("insertbackground", "black"),
                selectbackground=highlight_styles.get("background", "#316AC5"),
                selectforeground=highlight_styles.get("foreground", "white")
            )
            self.editor_view.translated_text.config(
                bg=text_styles.get("background", "white"),
                fg=text_styles.get("foreground", "black"),
                insertbackground=text_styles.get("insertbackground", "black"),
                selectbackground=highlight_styles.get("background", "#316AC5"),
                selectforeground=highlight_styles.get("foreground", "white")
            )
            
            # 更新高亮標籤的顏色
            self.editor_view.original_text.tag_config(
                "highlight",
                background=highlight_styles.get("background", "#E8F4FD"),
                foreground=highlight_styles.get("foreground", "#1F5582")
            )
            self.editor_view.translated_text.tag_config(
                "highlight",
                background=highlight_styles.get("background", "#E8F4FD"),
                foreground=highlight_styles.get("foreground", "#1F5582")
            )
            
        # 更新樹狀視圖顏色和高亮標籤（如果存在）
        if self.file_tabs_view and text_styles and highlight_styles:
            # 更新所有標籤頁中的樹狀視圖高亮樣式
            if hasattr(self.file_tabs_view, 'tabs'):
                for tab_info in self.file_tabs_view.tabs.values():
                    tree = tab_info.get("tree")
                    if tree:
                        tree.tag_configure(
                            "highlighted",
                            background=highlight_styles.get("background", "#E8F4FD"),
                            foreground=highlight_styles.get("foreground", "#1F5582")
                        )
            
        print(f"[DEBUG] 已為 {event.theme_name} 主題更新Text控件、樹狀視圖和高亮顏色。")
        
        # 强制刷新整个窗口以应用所有更改
        self.root.update_idletasks()
        print(f"[DEBUG] 主题切换事件处理完成，UI已刷新。")


    def _create_menu_bar(self):
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # File Menu
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="文件", menu=self.file_menu)
        self.file_menu.add_command(
            label="打開目錄...",
            command=lambda: self.handlers.get_command_handler("load_directory")()
            if self.handlers
            else None,
        )
        self.file_menu.add_command(
            label="保存當前文件",
            command=lambda: self.handlers.get_command_handler("save_file")()
            if self.handlers
            else None,
        )
        self.file_menu.add_command(
            label="全部保存",
            command=lambda: self.handlers.get_command_handler("save_all_files")()
            if self.handlers
            else None,
        )
        self.file_menu.add_separator()
        self.file_menu.add_command(
            label="保存工程...",
            command=lambda: self.handlers.get_command_handler("save_project")()
            if self.handlers
            else None,
        )
        self.file_menu.add_command(
            label="加載工程...",
            command=lambda: self.handlers.get_command_handler("load_project")()
            if self.handlers
            else None,
        )
        self.file_menu.add_separator()
        self.file_menu.add_command(label="退出", command=self.root.quit)

        # Edit Menu
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="编辑", menu=edit_menu)

        edit_menu.add_command(
            label="查找...",
            command=lambda: self.handlers.get_command_handler("show_find_dialog")()
            if self.handlers
            else None,
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label="查找和替换...",
            command=lambda: self.handlers.get_command_handler(
                "show_find_replace_dialog"
            )()
            if self.handlers
            else None,
        )

        # Options Menu
        options_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="选项", menu=options_menu)
        options_menu.add_command(
            label="翻译设置...",
            command=lambda: self.handlers.get_command_handler(
                "show_translation_settings"
            )()
            if self.handlers
            else None,
        )
        options_menu.add_separator()
        options_menu.add_command(
            label="文件类型配置...",
            command=lambda: self.handlers.get_command_handler("show_file_type_config")()
            if self.handlers
            else None,
        )
        # 主題設置已移至菜單欄快速切換

        # --- Help Menu ---
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(
            label="关于",
            command=lambda: self.handlers.get_command_handler("show_about")()
            if self.handlers
            else None,
        )
        
        # --- Theme Menu ---
        self.menubar.add_command(label="🎨 主題", command=self._quick_toggle_theme)

    def _create_main_layout(self):
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Paned window for resizable sections
        self.paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # 创建组件处理器字典
        component_handlers = self._create_component_handlers()
        
        # 创建UI组件
        self.file_tabs_view = FileTabsView(self.paned_window, component_handlers)
        self.editor_view = EditorView(self.paned_window, component_handlers)

        # 添加组件到面板
        self.paned_window.add(self.file_tabs_view.get_frame())
        self.paned_window.add(self.editor_view.get_frame())

        # 设置初始比例和窗口大小变化监听
        self._setup_paned_window_ratio()

    def _create_component_handlers(self) -> dict:
        """创建传递给组件的处理器字典"""
        return {
            "tab_changed": lambda e: self.handlers.get_command_handler("tab_changed")(e) if self.handlers else None,
            "tree_select": lambda e: self.handlers.get_command_handler("tree_select")(e) if self.handlers else None,
            "text_modified": lambda e: self.handlers.get_command_handler("text_modified")(e) if self.handlers else None,
            "text_realtime_change": lambda e: self._handle_text_realtime_change(e),
            "translate_command": lambda: self._handle_translate_command(),
            "apply_command": lambda: self.handlers.get_command_handler("apply_changes")() if self.handlers else None,
            "highlight_toggle": lambda: self.handlers.get_command_handler("highlight_toggle")() if self.handlers else None,
        }

    def _setup_paned_window_ratio(self):
        """设置面板窗口比例和监听窗口大小变化"""
        # 初始化比例状态
        self._current_ratio = 0.6  # 默认比例
        self._last_window_width = 0
        self._user_adjusted = False  # 用户是否手动调整过
        self._resize_timer = None # 用于延迟处理窗口大小变化的计时器
        
        # 初始延迟设置比例
        self.root.after(100, self._initial_paned_setup)
        
        # 监听窗口大小变化事件
        self.root.bind('<Configure>', self._on_window_configure)
        
        # 监听用户手动调整sash位置
        self.paned_window.bind('<Button-1>', self._on_sash_drag_start)
        self.paned_window.bind('<ButtonRelease-1>', self._on_sash_drag_end)
        
    def _initial_paned_setup(self):
        """初始设置面板比例"""
        try:
            total_width = self.paned_window.winfo_width()
            if total_width > 100:  # 确保窗口已经渲染
                left_width = int(total_width * self._current_ratio)
                self.paned_window.sashpos(0, left_width)
                self._last_window_width = total_width
            else:
                # 如果窗口还没有渲染完成，再次尝试
                self.root.after(50, self._initial_paned_setup)
        except tk.TclError:
            self.root.after(50, self._initial_paned_setup)
            
    def _on_sash_drag_start(self, event):
        """开始拖拽sash"""
        pass  # 只是为了监听事件
        
    def _on_sash_drag_end(self, event):
        """结束拖拽sash，记录用户调整"""
        try:
            total_width = self.paned_window.winfo_width()
            sash_pos = self.paned_window.sashpos(0)
            if total_width > 0:
                self._current_ratio = sash_pos / total_width
                self._user_adjusted = True
        except tk.TclError:
            pass
            
    def _on_window_configure(self, event):
        """窗口大小变化时的事件处理"""
        if event.widget != self.root:
            return

        # 取消之前的计时器，防止重复执行
        if self._resize_timer:
            self.root.after_cancel(self._resize_timer)

        # 检查窗口是否最大化 (在Windows上是 'zoomed')
        try:
            if self.root.state() == 'zoomed':
                # 如果是最大化，强制更新待办任务以获取最新尺寸
                self.root.update_idletasks()
                # 然后立即调整，以消除抖动
                self._adjust_paned_ratio()
            else:
                # 对于普通的大小调整，使用延迟以避免性能问题
                self._resize_timer = self.root.after(100, self._adjust_paned_ratio)
        except tk.TclError:
            # 在某些情况下（如窗口刚创建时），状态可能无法立即获取，使用备用方案
            self._resize_timer = self.root.after(100, self._adjust_paned_ratio)
                
    def _adjust_paned_ratio(self):
        """调整面板比例以保持用户设置"""
        try:
            total_width = self.paned_window.winfo_width()
            if total_width > 100:
                # 使用当前比例计算新位置
                new_sash_pos = int(total_width * self._current_ratio)
                # 确保 sash 位置在合理范围内
                min_pos = 200  # 最小左侧宽度
                max_pos = total_width - 200  # 最小右侧宽度
                new_sash_pos = max(min_pos, min(new_sash_pos, max_pos))
                
                self.paned_window.sashpos(0, new_sash_pos)
                self._last_window_width = total_width
        except tk.TclError:
            pass

    def _handle_text_realtime_change(self, event):
        """处理实时文本变化事件"""
        if self.handlers:
            # 使用命令模式调用，而不是直接访问子处理器
            command = self.handlers.get_command_handler('text_realtime_change')
            if command:
                command(event)

    def update_editor_text(self, original: str, translated: str):
        """更新编辑器文本内容"""
        if self.editor_view:
            self.editor_view.update_editor_text(original, translated)

    def clear_editor_text(self):
        """清空编辑器文本"""
        if self.editor_view:
            self.editor_view.clear_editor_text()

    def _create_status_bar(self):
        status_bar = ttk.Label(
            self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var.set("准备就绪。请打开一个 .class 文件。")

    def clear_tree(self):
        """清空所有树状视图内容"""
        if self.file_tabs_view:
            self.file_tabs_view.clear_tree()

    def add_file_tab(self, filepath: str, data: List[StringEntry]) -> Any:
        """添加文件标签页"""
        if self.file_tabs_view:
            return self.file_tabs_view.add_file_tab(filepath, data)
        return None

    def get_current_treeview(self):
        """获取当前活动标签页的树状视图"""
        if self.file_tabs_view:
            return self.file_tabs_view.get_current_treeview()
        return None

    def get_current_filepath(self) -> Optional[str]:
        """获取当前活动标签页的文件路径"""
        if self.file_tabs_view:
            return self.file_tabs_view.get_current_filepath()
        return None

    def get_tree_for_file(self, filepath: str):
        """获取指定文件的树状视图控件"""
        if self.file_tabs_view:
            return self.file_tabs_view.get_tree_for_file(filepath)
        return None

    def get_highlight_enabled(self) -> bool:
        """获取高亮功能的启用状态"""
        if self.editor_view:
            return self.editor_view.get_highlight_enabled()
        return True

    def get_selected_tree_item_id(self) -> Optional[int]:
        """获取当前选中的树状视图项目ID"""
        if self.file_tabs_view:
            return self.file_tabs_view.get_selected_tree_item_id()
        return None

    def get_all_selected_tree_item_ids(self) -> List[int]:
        """获取所有选中的树状视图项目ID列表"""
        if self.file_tabs_view:
            return self.file_tabs_view.get_all_selected_tree_item_ids()
        return []

    def update_tree_item(self, item_id: int, translated_text: str):
        """更新树状视图中指定项目的翻译文本"""
        if self.file_tabs_view:
            self.file_tabs_view.update_tree_item(item_id, translated_text)

    def highlight_tree_row(self, item_id: int, highlight: bool):
        """设置树状视图行的高亮状态"""
        if self.file_tabs_view:
            self.file_tabs_view.highlight_tree_row(item_id, highlight)

    def update_text_highlights(self, ranges: List[tuple]):
        """更新文本编辑器中的高亮范围"""
        if self.editor_view:
            self.editor_view.update_text_highlights(ranges)

    def update_status_bar(self, status_data):
        """Updates the status bar with statistics about the loaded data."""
        if isinstance(status_data, str):
            self.status_var.set(status_data)
            return

        total_entries = len(status_data)
        file_types = [entry.file_type for entry in status_data]
        stats = collections.Counter(file_types)

        stats_str = ", ".join([f"{ft}: {count}" for ft, count in stats.items()])
        self.status_var.set(f"共 {total_entries} 个条目 ({stats_str})")

    def select_tree_items(self, item_ids: List[int]):
        """选中树状视图中的指定项目列表"""
        if self.file_tabs_view:
            self.file_tabs_view.select_tree_items(item_ids)

    def enable_file_operations(self):
        self.file_menu.entryconfig("保存當前文件", state="normal")

    def disable_file_operations(self):
        self.file_menu.entryconfig("保存當前文件", state="disabled")
        if self.editor_view:
            self.editor_view.set_apply_button_state(False)

    # ==================== 新增的接口方法 ====================

    def get_translated_text(self) -> str:
        """获取编辑器中的译文内容"""
        if self.editor_view:
            return self.editor_view.get_translated_text()
        return ""
    
    # ==================== 组件内部控件访问方法 ====================
    # 这些方法为了保持与现有事件处理器的兼容性
    
    @property
    def translated_text(self):
        """获取译文文本控件（兼容性属性）"""
        if self.editor_view:
            return self.editor_view.translated_text
        return None

    def set_apply_button_state(self, enabled: bool) -> None:
        """设置应用修改按钮的启用状态"""
        if self.editor_view:
            self.editor_view.set_apply_button_state(enabled)

    def _handle_translate_command(self):
        """根据选中项目数量决定使用哪个翻译命令"""
        if not self.handlers:
            return
            
        # 获取当前选中的项目数量
        selected_count = len(self.get_all_selected_tree_item_ids())
        
        if selected_count == 0:
            # 没有选中项目，显示提示
            self.show_info_dialog("无选择", "请先在列表中选择一个或多个字符串。")
            return
        elif selected_count == 1:
            # 单个项目，使用单个翻译
            self.handlers.get_command_handler("translate")()
        else:
            # 多个项目，使用批量翻译
            self.handlers.get_command_handler("translate_all")()

    def show_info_dialog(self, title: str, message: str) -> None:
        """顯示信息對話框"""
        self._center_dialog_on_parent()
        messagebox.showinfo(title, message, parent=self.root)

    def show_warning_dialog(self, title: str, message: str) -> None:
        """顯示警告對話框"""
        self._center_dialog_on_parent()
        messagebox.showwarning(title, message, parent=self.root)

    def show_error_dialog(self, title: str, message: str) -> None:
        """顯示錯誤對話框"""
        self._center_dialog_on_parent()
        messagebox.showerror(title, message, parent=self.root)

    def ask_save_file_dialog(
        self, title: str, filetypes: List[tuple[str, str]]
    ) -> Optional[str]:
        """顯示保存文件對話框，返回選中的文件路徑"""
        self._center_dialog_on_parent()
        return filedialog.asksaveasfilename(
            title=title, filetypes=filetypes, defaultextension=".cep", parent=self.root
        )

    def ask_open_file_dialog(
        self, title: str, filetypes: List[tuple[str, str]]
    ) -> Optional[str]:
        """顯示打開文件對話框，返回選中的文件路徑"""
        self._center_dialog_on_parent()
        return filedialog.askopenfilename(title=title, filetypes=filetypes, parent=self.root)

    def ask_directory_dialog(self, title: str) -> Optional[str]:
        """顯示選擇目錄對話框，返回選中的目錄路徑"""
        self._center_dialog_on_parent()
        return filedialog.askdirectory(title=title, parent=self.root)

    def _center_dialog_on_parent(self):
        """確保對話框相對於主窗口居中顯示"""
        # 更新主窗口的位置和大小信息
        self.root.update_idletasks()
        # 設置主窗口為焦點，這樣對話框就會相對於它居中
        self.root.focus_force()

    def _update_status_message(self, message: str, duration_ms: int = 0):
        """更新狀態欄消息，可選擇自動清除"""
        self.status_var.set(message)
        if duration_ms > 0:
            # 在指定時間後清除狀態消息
            self.root.after(duration_ms, lambda: self.status_var.set("就緒"))
    
    # === 主題切換方法 ===
    
    def _get_theme_service(self):
        """獲取主題服務實例"""
        try:
            # 方式1: 通過全局應用實例獲取
            if hasattr(self.root, '_app_instance'):
                from core.services.theme_service import ThemeService
                return self.root._app_instance.container.resolve(ThemeService)
            
            # 方式2: 通過根窗口的屬性獲取
            for attr_name in ['app', 'application', '_application']:
                if hasattr(self.root, attr_name):
                    app = getattr(self.root, attr_name)
                    if hasattr(app, 'container'):
                        from core.services.theme_service import ThemeService
                        return app.container.resolve(ThemeService)
            
            # 方式3: 創建新的主題服務實例（備用方案）
            print("[WARNING] 無法從容器獲取主題服務，創建新實例")
            from core.services.theme_service import ThemeService
            return ThemeService(self.root)
            
        except Exception as e:
            print(f"[ERROR] 獲取主題服務失敗: {e}")
            # 如果所有方法都失敗，嘗試創建一個新實例
            try:
                from core.services.theme_service import ThemeService
                return ThemeService(self.root)
            except Exception as create_error:
                print(f"[ERROR] 創建主題服務實例失敗: {create_error}")
                return None
    

    
    def _quick_toggle_theme(self):
        """快速切換主題（明暗切換）"""
        try:
            theme_service = self._get_theme_service()
            if theme_service:
                current = theme_service.get_current_theme()
                new_theme = "dark" if current == "light" else "light"
                theme_service.apply_theme(new_theme)
                print(f"[DEBUG] 快速切換主題: {current} → {new_theme}")
            else:
                print(f"[ERROR] 無法獲取主題服務")
                self.show_error_dialog("主題切換失敗", "無法獲取主題服務")
        except Exception as e:
            print(f"[ERROR] 主題切換失敗: {e}")
            self.show_error_dialog("主題切換失敗", f"無法切換主題: {str(e)}")
    
    def _apply_theme(self, theme_name: str):
        """應用指定主題"""
        try:
            theme_service = self._get_theme_service()
            if theme_service:
                current = theme_service.get_current_theme()
                if current != theme_name:
                    theme_service.apply_theme(theme_name)
                    print(f"[DEBUG] 應用主題: {theme_name}")
                else:
                    print(f"[DEBUG] 主題 {theme_name} 已經是當前主題")
            else:
                print(f"[ERROR] 無法獲取主題服務")
                self.show_error_dialog("主題應用失敗", "無法獲取主題服務")
        except Exception as e:
            print(f"[ERROR] 應用主題失敗: {e}")
            self.show_error_dialog("主題應用失敗", f"無法應用主題 {theme_name}: {str(e)}")

    def _setup_keyboard_shortcuts(self):
        """設置快捷鍵綁定"""
        # Ctrl+S: 保存工程
        self.root.bind('<Control-s>', lambda e: self._handle_save_project_shortcut())
        
        # Ctrl+Z: 撤回
        self.root.bind('<Control-z>', lambda e: self._handle_undo_shortcut())
        
        # Ctrl+F: 搜尋
        self.root.bind('<Control-f>', lambda e: self._handle_find_shortcut())
        
        # Ctrl+H: 替換
        self.root.bind('<Control-h>', lambda e: self._handle_replace_shortcut())

    def _handle_save_project_shortcut(self):
        """處理保存工程快捷鍵"""
        self._update_status_message("正在保存工程...")
        if self.handlers:
            command_handler = self.handlers.get_command_handler("save_project")
            if command_handler:
                command_handler()
                self._update_status_message("工程已保存", 2000)

    def _handle_undo_shortcut(self):
        """處理撤回快捷鍵"""
        # 不在這裡設置狀態消息，讓撤回操作本身處理狀態反饋
        if self.handlers:
            command_handler = self.handlers.get_command_handler("undo")
            if command_handler:
                command_handler()
                # 不覆蓋撤回操作的狀態消息

    def _handle_find_shortcut(self):
        """處理搜尋快捷鍵"""
        self._update_status_message("打開搜尋對話框...")
        if self.handlers:
            command_handler = self.handlers.get_command_handler("show_find_dialog")
            if command_handler:
                command_handler()
                self._update_status_message("搜尋對話框已打開", 1500)

    def _handle_replace_shortcut(self):
        """處理替換快捷鍵"""
        self._update_status_message("打開替換對話框...")
        if self.handlers:
            command_handler = self.handlers.get_command_handler("show_find_replace_dialog")
            if command_handler:
                command_handler()
                self._update_status_message("替換對話框已打開", 1500)
