import tkinter as tk
from tkinter import ttk


class FindReplaceDialog(tk.Toplevel):
    """A modal dialog for find and replace operations."""

    def __init__(self, parent):
        """Initializes the Find and Replace dialog window."""
        super().__init__(parent)
        self.transient(parent)
        self.title("查找和替换")
        self.parent = parent
        self.result = None

        body = ttk.Frame(self, padding="10")
        self.initial_focus = self._create_widgets(body)
        body.pack(fill=tk.BOTH, expand=True)

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

        self.initial_focus.focus_set()
        self.wait_visibility()
        self.grab_set()
        self.wait_window(self)

    def _create_widgets(self, parent):
        """Creates and lays out the widgets for the dialog."""
        # Find what
        ttk.Label(parent, text="查找内容:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.find_entry = ttk.Entry(parent, width=40)
        self.find_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)

        # Replace with
        ttk.Label(parent, text="替换为:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.replace_entry = ttk.Entry(parent, width=40)
        self.replace_entry.grid(
            row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2
        )

        # Options
        self.match_case_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="区分大小写", variable=self.match_case_var).grid(
            row=2, column=1, sticky=tk.W, pady=5
        )

        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)

        ttk.Button(
            button_frame, text="在选中项中替换", command=self._on_replace_selection
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="全部替换", command=self._on_replace_all).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="取消", command=self._on_cancel).pack(
            side=tk.LEFT, padx=5
        )

        parent.columnconfigure(1, weight=1)

        return self.find_entry

    def _on_replace_selection(self):
        """Handles the 'Replace in Selection' button click."""
        self.result = {
            "action": "replace_selection",
            "find_text": self.find_entry.get(),
            "replace_text": self.replace_entry.get(),
            "match_case": self.match_case_var.get(),
        }
        self.destroy()

    def _on_replace_all(self):
        """Handles the 'Replace All' button click."""
        self.result = {
            "action": "replace_all",
            "find_text": self.find_entry.get(),
            "replace_text": self.replace_entry.get(),
            "match_case": self.match_case_var.get(),
        }
        self.destroy()

    def _on_cancel(self):
        """Handles the dialog cancellation."""
        self.result = None
        self.destroy()
