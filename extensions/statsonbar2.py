from __future__ import annotations

import psutil

__version__ = "0.3.2"
__version_info__ = tuple(int(num) for num in __version__.split("."))

import threading
import time
import tkinter as tk
import typing
from collections import deque

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


class StatsOnBar2:
    def __init__(self, api: ExtensionsAPI) -> None:
        self.api = api
        self.statusbar = self.api.statusbar
        self.sysinfo = self.api.sysinfo

        # CPU canvas
        self.cpu_canvas = tk.Canvas(
            self.statusbar,
            width=60,
            height=20,
            bg="#181818",
            highlightthickness=0,
            border=0,
        )
        self.cpu_canvas.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)

        # Memory canvas
        self.memory_canvas = tk.Canvas(
            self.statusbar,
            width=60,
            height=20,
            bg="#181818",
            highlightthickness=0,
            border=0,
        )
        self.memory_canvas.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))

        self.cpu_data = deque(maxlen=5)  # Store 5 seconds of CPU data
        self.memory_data = deque(maxlen=5)  # Store 5 seconds of Memory data
        self.alive = False

        self.cpu_label = self.cpu_canvas.create_text(
            5,
            10,
            anchor="w",
            text="CPU: 0%",
            fill=self.api.base.theme.primary_foreground,
            font=("Helvetica", 8),
        )

        self.memory_label = self.memory_canvas.create_text(
            5,
            10,
            anchor="w",
            text="MEM: 0%",
            fill=self.api.base.theme.primary_foreground,
            font=("Helvetica", 8),
        )

    def update_stats(self) -> None:
        while self.alive:
            cpu_usage, memory_usage = self.get_current_stats()
            self.cpu_data.append(cpu_usage)
            self.memory_data.append(memory_usage)
            self.statusbar.after(
                0, self.draw_graph
            )  # Schedule drawing on the main thread
            time.sleep(0.1)

    def get_current_stats(self) -> typing.Tuple[float, float]:
        """Get current CPU and Memory usage"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        return cpu_percent, memory_percent

    def draw_graph(self) -> None:
        # Draw CPU graph
        self.cpu_canvas.delete("graph")  # Remove old graph lines
        self.cpu_canvas.itemconfig(
            self.cpu_label, text=f"CPU: {self.cpu_data[-1]:.1f}%"
        )

        cpu_points = [
            (i * (60 / 4), 18 - (d / 50) * 20) for i, d in enumerate(self.cpu_data)
        ]

        if len(cpu_points) > 1:
            cpu_polygon_points = [(-10, 30)] + cpu_points + [(80, 30)]
            self.cpu_canvas.create_polygon(
                cpu_polygon_points,
                smooth=True,
                fill="#624652",
                outline="#db7d80",
                tags="graph",
            )

        # Draw Memory graph
        self.memory_canvas.delete("graph")  # Remove old graph lines
        self.memory_canvas.itemconfig(
            self.memory_label, text=f"MEM: {self.memory_data[-1]:.1f}%"
        )

        memory_points = [
            (i * (60 / 4), 30 - (d / 100) * 20) for i, d in enumerate(self.memory_data)
        ]

        if len(memory_points) > 1:
            memory_polygon_points = [(-10, 30)] + memory_points + [(80, 30)]
            self.memory_canvas.create_polygon(
                memory_polygon_points,
                smooth=True,
                fill="#404355",
                outline="#c6d0f5",
                tags="graph",
            )

    def install(self) -> None:
        self.alive = True
        threading.Thread(target=self.update_stats, daemon=True).start()

    def uninstall(self) -> None:
        self.alive = False
        self.cpu_canvas.destroy()
        self.memory_canvas.destroy()


def setup(api: ExtensionsAPI) -> StatsOnBar2:
    return api.register("statsonbar2", StatsOnBar2(api))
