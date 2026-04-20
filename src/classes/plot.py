import pygame
from os.path import join
from src.classes.object import Object

class Plot(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "plot")
        path = join("assets", "Other", "Plot.png")
        img = pygame.image.load(path).convert_alpha()
        self.image = pygame.transform.scale(img, (width, height))

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))