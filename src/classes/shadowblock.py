import pygame
from os.path import join
from src.classes.object import Object

class ShadowBlock(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "shadow")
        img = pygame.image.load(join("assets", "Other", "Shadow.png")).convert_alpha()
        img = pygame.transform.scale(img, (width, height))
        self.image.blit(img, (0, 0))