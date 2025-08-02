import tkinter as tk
from tkinter import ttk


class FindDialog(tk.Toplevel):
    """A modal dialog for finding text."""

    def __init__(self, parent):
        """Initializes the Find dialog window."""
        super().__init__(parent)
        self.transient(parent)
        self.title("查找")
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

        # Options
        self.match_case_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="区分大小写", variable=self.match_case_var).grid(
            row=1, column=1, sticky=tk.W, pady=5
        )

        self.search_in_var = tk.StringVar(value="translated")
        ttk.Label(parent, text="搜索范围:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Radiobutton(
            parent, text="仅译文", variable=self.search_in_var, value="translated"
        ).grid(row=2, column=1, sticky=tk.W)
        ttk.Radiobutton(
            parent, text="原文和译文", variable=self.search_in_var, value="both"
        ).grid(row=2, column=2, sticky=tk.W)

        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)

        ttk.Button(button_frame, text="查找全部", command=self._on_find_all).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="取消", command=self._on_cancel).pack(
            side=tk.LEFT, padx=5
        )

        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(2, weight=1)

        return self.find_entry

    def _on_find_all(self):
        """Handles the 'Find All' button click."""
        self.result = {
            "find_text": self.find_entry.get(),
            "match_case": self.match_case_var.get(),
            "search_in": self.search_in_var.get(),
        }
        self.destroy()

    def _on_cancel(self):
        """Handles the dialog cancellation."""
        self.result = None
        self.destroy()
