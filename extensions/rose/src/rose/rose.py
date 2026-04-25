from __future__ import annotations

import os
import random
import tkinter as tk
import typing

from PIL import Image, ImageTk
from biscuit.extensions import Extension
from biscuit.common.ui.native import Canvas
from biscuit.editor import BaseEditor

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


class RoseCanvas(Canvas):
    def __init__(self, master, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)
        self.bind("<Configure>", self.on_resize)
        self.bind("<Button-1>", self.regenerate)
        self.images = []
        self.current_image_index = 0
        self.load_images()
        self.draw_rose()

    def load_images(self):
        resources_dir = os.path.join(os.path.dirname(__file__), "../../images")
        image_files = [
            "rose-1.jpg",
            "rose-2.jpg", 
            "rose-3.jpg",
            "rose-4.jpg"
        ]
        
        for filename in image_files:
            filepath = os.path.join(resources_dir, filename)
            if os.path.exists(filepath):
                self.images.append(filepath)

    def on_resize(self, event):
        self.draw_rose()

    def regenerate(self, event=None):
        self.delete("all")
        self.draw_rose()

    def draw_rose(self):
        width = self.winfo_width()
        height = self.winfo_height()
        if width < 100 or height < 100 or not self.images:
            return

        self.current_image_index = random.randint(0, len(self.images) - 1)
        image_path = self.images[self.current_image_index]

        img = Image.open(image_path)
        img.thumbnail((width - 40, height - 40), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(img)
        self.photo = photo
        
        x = (width - img.width) // 2
        y = (height - img.height) // 2
        
        self.create_image(x, y, anchor=tk.NW, image=photo)
        
        self.create_text(
            width // 2, height - 20, 
            text="Click for new rose image",
            fill="#888888", 
            font=("Fira Code", 10)
        )


class RoseEditor(BaseEditor):
    name = "rose"
    
    def __init__(self, master, *args, **kwargs) -> None:
        super().__init__(master, path=None, editable=False, *args, **kwargs)
        
        self.filename = "Rose"
        self.path = None
        self.exists = False
        self.editable = False
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.canvas = RoseCanvas(self, bg=self.base.theme.primary_background)
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW)


class Rose(Extension):
    def __init__(self, api: "ExtensionsAPI") -> None:
        super().__init__(api)
        self.api.logger.info("rose extension initialised.")

    def install(self) -> None:
        self.register_rose_command()
        self.api.notifications.info("Rose extension installed - press Ctrl+Shift+P and search 'Show Rose'")

    def register_rose_command(self) -> None:
        self.api.base.settings.commands.append(("Show Rose", self.open_rose_editor))
        self.api.base.settings.generate_actionset()
        self.api.base.palette.register_actionset(lambda: self.api.base.settings.actionset)

    def open_rose_editor(self, *_) -> None:
        editor = RoseEditor(self.api.editorsmanager)
        self.api.editors.add_editor(editor)