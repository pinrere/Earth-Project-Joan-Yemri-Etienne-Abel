import pygame
from os.path import join

class ParallaxBackground:
    def __init__(self, win):
        self.window = win
        self.width = win.get_width()
        self.y_offset = -70

        self.layers = [
            {"img": pygame.image.load(join("assets", "Background", "sky.png")).convert_alpha(), "speed": 0.1},
            {"img": pygame.image.load(join("assets", "Background", "houses.png")).convert_alpha(), "speed": 0.4},
            {"img": pygame.image.load(join("assets", "Background", "road.png")).convert_alpha(), "speed": 0.7}
        ]

    def draw(self, offset_x):
        for layer in self.layers:
            rel_x = (offset_x * layer["speed"]) % self.width
            self.window.blit(layer["img"], (-rel_x, self.y_offset))
            if rel_x > 0:
                self.window.blit(layer["img"], (self.width - rel_x, self.y_offset))
            else:
                self.window.blit(layer["img"], (-self.width - rel_x, self.y_offset))
