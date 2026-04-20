import pygame
from os.path import join
from src.classes.object import Object

class Platform(Object):
    def __init__(self, x, y):
        width = 120
        height = 30
        super().__init__(x, y, width, height, "platform")
        img = pygame.image.load(join("assets", "Terrain", "plateform.png")).convert_alpha()
        self.image = pygame.transform.scale(img, (width, height))
        self.rect = pygame.Rect(x, y, width, height)