from __future__ import annotations

from pytermgui import background

__version__ = "0.0.1"
__version_info__ = tuple([int(num) for num in __version__.split(".")])

import tkinter as tk
import typing
from tkinter import ttk

from biscuit.common.ui import ButtonsEntry, Frame
from biscuit.extensions import Extension
from biscuit.views import NavigationDrawerView

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI
    from biscuit.layout import NavigationDrawer


class TodoView(NavigationDrawerView):
    def __init__(self, drawer: NavigationDrawer) -> None:
        __name__ = "Todo"
        super().__init__(drawer, name="Todo", icon="checklist")
        self.base = drawer.base

        self.add_action("clear-all", self.clear_all)

        self.entry = ButtonsEntry(
            self, "Add new task", buttons=[("add", self.add_task)]
        )
        self.entry.pack(fill=tk.X, padx=15, pady=7)

        self.font = self.base.settings.uifont
        self.striked_font = self.font.copy()
        self.striked_font.config(overstrike=True)

        self.style = ttk.Style()
        self.style.configure(
            "Todo.TCheckbutton",
            font=self.font,
            background=self.base.theme.views.sidebar.background,
        )
        self.striked_style = ttk.Style()
        self.striked_style.configure(
            "Striked.TCheckbutton",
            font=self.striked_font,
            background=self.base.theme.views.sidebar.background,
        )

        self.tasks = []

        self.tasklist = Frame(self, **self.base.theme.views.sidebar)
        self.tasklist.pack(fill=tk.BOTH, expand=True)

        self.entry.entry.bind("<Return>", lambda _: self.add_task())

    def add_task(self) -> None:
        task = self.entry.get()
        if not task:
            return

        var = tk.BooleanVar()
        cb = ttk.Checkbutton(
            self.tasklist, text=task, variable=var, style="Todo.TCheckbutton"
        )
        cb.config(command=lambda cb=cb, var=var: self.toggle_striked(cb, var))
        cb.pack(fill=tk.X, padx=15, pady=(0, 5), anchor=tk.W)

        self.tasks.append((var, cb))
        self.entry.clear()

    def toggle_striked(self, cb: ttk.Checkbutton, var: tk.BooleanVar) -> None:
        if var.get():
            cb.configure(style="Striked.TCheckbutton")
        else:
            cb.configure(style="Todo.TCheckbutton")

    def clear_all(self) -> None:
        for _, cb in self.tasks:
            cb.destroy()
        self.tasks = []


class Todo(Extension):
    def __init__(self, api: ExtensionsAPI) -> None:
        super().__init__(api)
        self.base = api.base

    def install(self) -> None:
        self.view = TodoView(self.base.drawer)
        self.base.drawer.add_view(self.view)


def setup(api: ExtensionsAPI) -> None:
    api.register("todo", Todo(api))
