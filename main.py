from __future__ import annotations

import numpy as np
import pygame
from pygame.locals import *

import stl
from renderer import Renderer
from viewport import Viewport

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

pygame.init()


class MainWindow:
    default_resolution = np.array([960, 720])
    font = pygame.font.Font(pygame.font.get_default_font(), 12)

    mouse_sensitivity = 1 / 100.0

    rotation_speed = np.pi/16

    def __init__(self):

        camera = Viewport(self.default_resolution, fov=120)

        model = stl.load("assets/untitled.stl")

        scene = [
            model.set_center(np.array([0.0, 0.0, 5.0])).scale(0.1).rotate(np.array([0.0, 0.0, np.pi / 2])).flip(y=True)
        ]

        print(len(model.triangles))
        self.renderer = Renderer(camera, scene)

        self.camera = self.renderer.camera

        self.screen = pygame.display.set_mode(self.default_resolution, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

        self.dt = 1.0

    def handle_keypresses(self):
        keys = pygame.key.get_pressed()

        if keys[K_LCTRL]:
            player_speed = 5.0
        else:
            player_speed = 2.0

        if keys[K_z]:
            self.camera.position += player_speed * self.dt * np.array(
                [np.sin(self.camera.orientation[1]), 0.0, np.cos(self.camera.orientation[1])],
                dtype=float)

        if keys[K_s]:
            self.camera.position += player_speed * self.dt * np.array(
                [-np.sin(self.camera.orientation[1]), 0.0, -np.cos(self.camera.orientation[1])], dtype=float)

        if keys[K_q]:
            self.camera.position += player_speed * self.dt * np.array(
                [-np.cos(self.camera.orientation[1]), 0.0, np.sin(self.camera.orientation[1])],
                dtype=float)

        if keys[K_d]:
            self.camera.position += player_speed * self.dt * np.array(
                [np.cos(self.camera.orientation[1]), 0.0, -np.sin(self.camera.orientation[1])],
                dtype=float)

        if keys[K_LSHIFT]:
            self.camera.position += player_speed * self.dt * np.array([0, -1, 0])

        if keys[K_SPACE]:
            self.camera.position += player_speed * self.dt * np.array([0, 1, 0])

    def draw_screen(self):
        self.screen.fill(BLACK)

        self.renderer.objects[0].rotate(np.array([0.0, self.rotation_speed * self.dt, 0.0]))

        self.renderer.render(self.screen)
        pygame.display.flip()

    def update(self):
        self.dt = self.clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == QUIT:
                return False

            if event.type == MOUSEMOTION:
                if pygame.mouse.get_pressed(3)[0]:
                    self.camera.orientation += np.array([
                        0.0,
                        event.rel[0] * self.mouse_sensitivity * self.camera.resolution[1] / self.camera.resolution[0],
                        0.0  # event.rel[1] * self.mouse_sensitivity,
                    ])

            if event.type == MOUSEWHEEL:
                if event.y > 0:
                    self.camera.fov += 1
                else:
                    self.camera.fov -= 1

            if event.type == KEYUP:
                if event.key == K_UP:
                    self.camera.focal_length *= 2.0
                if event.key == K_DOWN:
                    self.camera.focal_length /= 2.0

            if event.type == WINDOWSIZECHANGED:
                self.camera.resolution = np.array([event.x, event.y])
                # self.camera.fov = self.camera.fov

        self.handle_keypresses()

        self.draw_screen()

        rounded_pos = list(map(lambda x: round(x, 2), self.camera.position))

        pygame.display.set_caption(
            f"Position: {rounded_pos} | FOV: {self.camera.fov[0]} | FPS: {round(self.clock.get_fps())} | Frametime: {round(self.dt * 1000)}ms")

        return True

    def mainloop(self):
        running = True
        while running:
            running = self.update()
        pygame.quit()


if __name__ == "__main__":
    win = MainWindow()
    win.mainloop()
