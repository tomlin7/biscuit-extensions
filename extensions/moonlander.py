import tkinter as tk

GRAVITY = 0.1
THRUST_POWER = 0.2


class Moonlander:
    def __init__(self, api):
        self.api = api

    def install(self):
        class MoonlanderGame(self.api.Game):
            name = "Moonlander"

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.canvas = tk.Canvas(self, width=600, height=600)
                self.canvas.pack()

                self.rocketship = self.canvas.create_rectangle(
                    300, 100, 310, 90, fill="red"
                )
                self.fuel_gauge = self.canvas.create_rectangle(
                    10, 10, 110, 20, fill="green"
                )

                self.fuel = 100.0
                self.velocity = 0.0
                self.position = 100.0
                self.game_over = False

                self.bind_all("<space>", self.thrust)
                self.bind("<r>", self.restart_game)

                self.update()

            def thrust(self, event: tk.Event):
                if self.fuel > 0 and not self.game_over:
                    self.velocity -= THRUST_POWER
                    self.fuel -= 0.1
                    self.canvas.move(self.fuel_gauge, 1, 0)

            def restart_game(self, event: tk.Event):
                self.fuel = 100.0
                self.velocity = 0.0
                self.position = 100.0
                self.game_over = False
                self.canvas.delete("all")
                self.rocketship = self.canvas.create_rectangle(
                    300, 100, 310, 90, fill="red"
                )
                self.fuel_gauge = self.canvas.create_rectangle(
                    10, 10, 110, 20, fill="green"
                )
                self.update()

            def update(self):
                if not self.game_over:
                    self.velocity += GRAVITY
                    self.position += self.velocity
                    self.canvas.move(self.rocketship, 0, self.velocity)

                    if self.position > 550:
                        self.game_over = True
                        self.canvas.create_text(
                            300, 300, text="Crashed!", fill="red", font=("Arial", 30)
                        )
                    elif self.fuel <= 0:
                        self.game_over = True
                        self.canvas.create_text(
                            300,
                            300,
                            text="Out of fuel!",
                            fill="red",
                            font=("Arial", 30),
                        )
                    else:
                        self.after(20, self.update)

        self.api.register_game(MoonlanderGame)


def setup(api):
    api.register("moonlander", Moonlander(api))
