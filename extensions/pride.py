import tkinter as tk

# Constants
WIDTH = 800
HEIGHT = 900
SPEED = 10

# Rainbow colors
RAINBOW_COLORS = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]


class Extension:
    def __init__(self, api):
        self.api = api

    def run(self):
        class RainbowFlag(self.api.Game):
            name = "Pride"

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

                self.canvas = tk.Canvas(
                    self, width=WIDTH, height=HEIGHT, **self.base.theme.editors
                )
                self.canvas.pack()

                # Create vertical rainbow bars
                bar_width = WIDTH / len(RAINBOW_COLORS)
                self.bars = []
                for i, color in enumerate(RAINBOW_COLORS):
                    x0 = i * bar_width
                    y0 = 0
                    x1 = (i + 1) * bar_width
                    y1 = HEIGHT
                    bar = self.canvas.create_rectangle(
                        x0, y0, x1, y1, fill=color, outline=""
                    )
                    self.bars.append(bar)

                # Initial position of the bars
                self.x = 0

                # Start moving the bars
                self.move_bars()

            def move_bars(self):
                # Move the bars horizontally from left to right
                for bar in self.bars:
                    self.canvas.move(bar, SPEED, 0)
                self.x += SPEED

                # Check if any bar has reached the right end
                for bar in self.bars:
                    coords = self.canvas.coords(bar)
                    if coords[2] >= WIDTH:
                        # Teleport the bar to the left end
                        self.canvas.move(bar, -WIDTH, 0)

                # Repeat moving the bars
                self.after(50, self.move_bars)

        self.api.register_game(RainbowFlag)
