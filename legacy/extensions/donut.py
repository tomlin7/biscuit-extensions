from __future__ import annotations

__version__ = "0.0.1"
__version_info__ = tuple([int(num) for num in __version__.split(".")])

import math
import subprocess as sp
import tkinter as tk
import typing
from tkinter import ttk
from tkinter.filedialog import askopenfilename

numpy = None
try:
    import numpy as np
except ImportError:
    try:
        sp.run(["pip", "install", "numpy"], check=True)
    except Exception as e:
        numpy = None


from biscuit.common import BaseGame
from biscuit.extensions import Extension

if typing.TYPE_CHECKING:
    from biscuit.api import ExtensionsAPI


class DonutDimensions(BaseGame):
    name = "Donut Dimensions"

    def __init__(self, master, *a, **kw):
        super().__init__(master, *a, **kw)

        self.offset_x = 200  # Center of the canvas width (400 / 2)
        self.offset_y = 200  # Center of the canvas height (400 / 2)
        self.vertices = self.initial = [
            (100, 100, 100),
            (100, 100, -100),
            (100, -100, 100),
            (100, -100, -100),
            (-100, 100, 100),
            (-100, 100, -100),
            (-100, -100, 100),
            (-100, -100, -100),
        ]

        self.edges = [
            (0, 1),
            (0, 2),
            (0, 4),
            (1, 3),
            (1, 5),
            (2, 3),
            (2, 6),
            (3, 7),
            (4, 5),
            (4, 6),
            (5, 7),
            (6, 7),
        ]

        self.faces = [
            (0, 2, 6, 4),
            (0, 1, 3, 2),
            (0, 4, 5, 1),
            (1, 5, 7, 3),
            (2, 3, 7, 6),
            (4, 6, 7, 5),
        ]

        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.rotation_z = 0.0
        self.light_source = [200, -200, 200]

        # self.load_obj('horror.obj')

        self.load_btn = ttk.Button(self, text="Load OBJ", command=self.load_obj_dialog)
        self.load_btn.pack()

        self.canvas = tk.Canvas(self, width=400, height=400)
        self.canvas.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)

        self.d = 500
        self.is_animating = False
        self.curves = False

        self.slider = ttk.Scale(
            self, from_=1, to=500, orient=tk.VERTICAL, command=self.on_zoom_change
        )
        self.slider.set(500)
        self.slider.pack()

        self.wireframe = True
        self.create_gui()
        self.animate()

    def on_x_rotation_change(self, _):
        self.rotation_x = math.radians(self.x_rotation_slider.get())
        self.update_rotation_angles()

    def on_y_rotation_change(self, _):
        self.rotation_y = math.radians(self.y_rotation_slider.get())
        self.update_rotation_angles()

    def on_z_rotation_change(self, _):
        self.rotation_z = math.radians(self.z_rotation_slider.get())
        self.update_rotation_angles()

    def update_rotation_angles(self):
        self.rotation_matrix = np.dot(
            self.rotate_x(math.radians(self.x_rotation_slider.get())),
            np.dot(
                self.rotate_y(math.radians(self.y_rotation_slider.get())),
                self.rotate_z(math.radians(self.z_rotation_slider.get())),
            ),
        )
        self.vertices = [
            np.dot(self.rotation_matrix, vertex) for vertex in self.initial
        ]
        self.canvas.delete("all")
        self.draw_mesh()

    def toggle_animation(self):
        self.is_animating = not self.is_animating
        if self.is_animating:
            self.animate()
        else:
            self.after_cancel(self.animation_job)

    def create_gui(self):
        self.x_rotation_slider = ttk.Scale(self, from_=1, to=360, orient=tk.HORIZONTAL)
        self.x_rotation_slider.config(command=self.on_x_rotation_change)
        self.x_rotation_slider.set(0)
        self.x_rotation_slider.pack(fill=tk.X)

        self.y_rotation_slider = ttk.Scale(self, from_=1, to=360, orient=tk.HORIZONTAL)
        self.y_rotation_slider.config(command=self.on_y_rotation_change)
        self.y_rotation_slider.set(0)
        self.y_rotation_slider.pack(fill=tk.X)

        self.z_rotation_slider = ttk.Scale(self, from_=1, to=360, orient=tk.HORIZONTAL)
        self.z_rotation_slider.config(command=self.on_z_rotation_change)
        self.z_rotation_slider.set(0)
        self.z_rotation_slider.pack(fill=tk.X)

        ttk.Button(self, text="spin", command=self.toggle_animation).pack()
        ttk.Button(self, text="wireframe", command=self.wireframe_toggle).pack()
        ttk.Button(self, text="curves owo", command=self.curves_toggle).pack()

    def wireframe_toggle(self):
        self.wireframe = not self.wireframe
        self.canvas.delete("all")
        self.draw_mesh()

    def curves_toggle(self):
        self.curves = not self.curves
        self.canvas.delete("all")
        self.draw_mesh()

    def load_obj_dialog(self):
        file_path = askopenfilename(filetypes=[("Wavefront OBJ", "*.obj")])
        if file_path:
            self.load_obj(file_path)
            self.canvas.delete("all")
            self.animate()

    def load_obj(self, file_path):
        self.vertices = []
        self.faces = []
        with open(file_path, "r") as obj_file:
            for line in obj_file:
                if line.startswith("v "):
                    _, x, y, z = line.strip().split()
                    self.vertices.append(
                        (float(x) * 100, float(y) * 100, float(z) * 100)
                    )
                elif line.startswith("f "):
                    _, *face_indices = line.strip().split()
                    face_indices = [int(idx.split("/")[0]) - 1 for idx in face_indices]
                    self.faces.append(tuple(face_indices))

        self.initial = self.vertices

    def on_zoom_change(self, _):
        self.d = int(self.slider.get())
        self.canvas.delete("all")
        self.draw_mesh()

    def rotate_x(self, theta):
        return [
            [1, 0, 0],
            [0, math.cos(theta), -math.sin(theta)],
            [0, math.sin(theta), math.cos(theta)],
        ]

    def rotate_y(self, theta):
        return [
            [math.cos(theta), 0, math.sin(theta)],
            [0, 1, 0],
            [-math.sin(theta), 0, math.cos(theta)],
        ]

    def rotate_z(self, theta):
        return [
            [math.cos(theta), -math.sin(theta), 0],
            [math.sin(theta), math.cos(theta), 0],
            [0, 0, 1],
        ]

    def project_vertex(self, vertex):
        transformed_vertex = np.dot(self.rotation_matrix, vertex)
        x, y, z = transformed_vertex
        if z != 0:
            projected_x = x * self.d / (z + self.d)
            projected_y = y * self.d / (z + self.d)
            return projected_x, projected_y
        else:
            return x, y

    def perspective_projection(self, vertices):
        projected_vertices = [self.project_vertex(vertex) for vertex in vertices]
        return projected_vertices

    def is_backfacing(self, face):
        v1 = np.array(self.vertices[face[0]])
        v2 = np.array(self.vertices[face[1]])
        v3 = np.array(self.vertices[face[2]])
        normal = np.cross(v2 - v1, v3 - v1)

        view_vector = np.array([0, 0, -1])  # towards me
        return np.dot(normal, view_vector) > 0

    def sort_faces(self):
        face_depths = []
        for face in self.faces:
            depth_sum = 0
            for vertex_index in face:
                x, y, z = self.vertices[vertex_index]
                depth_sum += z
            avg_depth = depth_sum / len(face)
            face_depths.append((face, avg_depth))

        sorted_faces = sorted(face_depths, key=lambda item: item[1], reverse=True)
        return [face for face, _ in sorted_faces]

    def draw_mesh(self):
        if self.wireframe:
            for face in self.sort_faces():
                coords = self.perspective_projection([self.vertices[i] for i in face])
                coords = [
                    (x + self.offset_x, y + self.offset_y) for x, y in coords
                ]  # Offset the coordinates
                self.canvas.create_polygon(
                    coords, outline="white", fill="", smooth=self.curves
                )
            return

        for face in self.sort_faces():
            if self.is_backfacing(face):  # skip backfacing faces
                continue

            v1 = np.array(self.vertices[face[0]])
            v2 = np.array(self.vertices[face[1]])
            v3 = np.array(self.vertices[face[2]])
            normal = np.cross(v2 - v1, v3 - v1)

            to_light = np.array(self.light_source) - v1
            cos_theta = np.dot(normal, to_light) / (
                np.linalg.norm(normal) * np.linalg.norm(to_light)
            )

            shade = int(255 * (cos_theta + 1) / 2)
            color = "#{:02x}{:02x}{:02x}".format(shade, shade, shade)

            coords = self.perspective_projection([self.vertices[i] for i in face])
            coords = [
                (x + self.offset_x, y + self.offset_y) for x, y in coords
            ]  # Offset the coordinates
            self.canvas.create_polygon(coords, fill=color, smooth=self.curves)

        # for edge in self.edges:
        #     x1, y1, z1 = self.vertices[edge[0]]
        #     x2, y2, z2 = self.vertices[edge[1]]
        #     coords = self.perspective_projection([(x1, y1, z1), (x2, y2, z2)])
        #     x1, y1 = coords[0]
        #     x2, y2 = coords[1]
        #     self.canvas.create_line(x1 + self.offset_x, y1 + self.offset_y, x2 + self.offset_x, y2 + self.offset_y)

        # for vertex in self.vertices:
        #     x, y, z = vertex
        #     coords = self.perspective_projection([(x, y, z)])
        #     x, y = coords[0]
        #     self.canvas.create_text(x + self.offset_x, y + self.offset_y, text="+", fill='black')

    def animate(self):
        self.rotation_matrix = np.dot(
            self.rotate_x(0.0), np.dot(self.rotate_y(0.1), self.rotate_z(0.0))
        )
        self.vertices = [
            np.dot(self.rotation_matrix, vertex) for vertex in self.vertices
        ]

        self.canvas.delete("all")
        self.draw_mesh()

        if self.is_animating:
            self.animation_job = self.after(10, self.animate)


class DonutExtension(Extension):
    """3D model viewer for Biscuit (author: @tomlin7)

    Contributes:
    """

    def __init__(self, api: ExtensionsAPI) -> None:
        super().__init__(api)

    def install(self) -> None:
        # if not numpy:
        #     self.api.notifications.info(
        #         "numpy pip package is not installed. Install it to use this extension.",
        #         actions=[
        #             (
        #                 "Install",
        #                 lambda: self.api.terminalmanager.run_command(
        #                     "pip install numpy"
        #                 ),
        #             ),
        #         ],
        #     )

        self.api.register_game(DonutDimensions)
        self.api.commands.register_command("Donut: Run", self.run_donut)

    def run_donut(self, *_) -> None:
        self.api.base.open_game("Donut Dimensions")


def setup(api: ExtensionsAPI) -> None:
    """Setup the extension"""
    api.register("donut", DonutExtension(api))
