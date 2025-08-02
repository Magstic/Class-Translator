import tkinter as tk
from tkinter import ttk
from core.services import TranslationService


class SettingsDialog(tk.Toplevel):
    """A dialog for editing translation settings, including general and plugin-specific rules."""

    def __init__(self, parent: tk.Tk, translation_service: TranslationService):
        """
        Initializes the settings dialog.

        Args:
            parent: The parent window.
            translation_service: The instance of the TranslationService.
        """
        super().__init__(parent)
        self.title("翻译设置")
        self.geometry("450x250")
        self.transient(parent)
        self.grab_set()

        self.translation_service = translation_service
        self.rules = self.translation_service.get_active_engine_rules()
        self.entries = {}
        self.concurrency_var = tk.IntVar(
            value=self.translation_service.get_max_concurrent_requests()
        )

        self._create_widgets()

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_window(self)

    def _create_widgets(self):
        """Creates a tabbed interface for different settings categories."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=5)

        # --- Plugin Rules Tab ---
        rules_frame = ttk.Frame(notebook, padding="10")
        notebook.add(rules_frame, text="插件规则")
        self._create_rules_widgets(rules_frame)

        # --- General Settings Tab ---
        general_frame = ttk.Frame(notebook, padding="10")
        notebook.add(general_frame, text="通用设置")
        self._create_general_widgets(general_frame)

        # --- Buttons ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))

        save_button = ttk.Button(button_frame, text="保存", command=self._on_save)
        save_button.pack(side=tk.RIGHT, padx=5)

        cancel_button = ttk.Button(button_frame, text="取消", command=self.destroy)
        cancel_button.pack(side=tk.RIGHT)

    def _create_rules_widgets(self, parent_frame: ttk.Frame):
        """Dynamically creates widgets for translator-specific rules."""
        if not self.rules:
            ttk.Label(parent_frame, text="当前翻译引擎没有可配置的规则。").pack()
            return

        row = 0
        for key, details in self.rules.items():
            label_text = details.get("label", key)
            value = details.get("value", "")

            label = ttk.Label(parent_frame, text=label_text)
            label.grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

            if details.get("type") == "string":
                entry = ttk.Entry(parent_frame, width=40)
                entry.insert(0, value)
                entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
                self.entries[key] = entry
            row += 1
        parent_frame.grid_columnconfigure(1, weight=1)

    def _create_general_widgets(self, parent_frame: ttk.Frame):
        """Creates widgets for general translation settings."""
        label = ttk.Label(parent_frame, text="最大并发翻译数:")
        label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        spinbox = ttk.Spinbox(
            parent_frame, from_=1, to=50, textvariable=self.concurrency_var, width=10
        )
        spinbox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

    def _on_save(self):
        """Collects new values and saves them to the TranslationService."""
        # Save plugin-specific rules
        new_rules = {}
        for key, entry_widget in self.entries.items():
            new_rules[key] = entry_widget.get()
        if new_rules:
            self.translation_service.update_active_engine_rules(new_rules)

        # Save general settings
        self.translation_service.set_max_concurrent_requests(self.concurrency_var.get())

        self.destroy()
