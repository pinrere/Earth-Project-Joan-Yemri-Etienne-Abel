import pygame
from src.classes.object import Object
from src.fonctions.get_block import get_block

class Block(Object):
    def __init__(self, x, y, size_y, name, size_x=96):
        super().__init__(x, y, size_x, size_y)
        self.image = get_block(size_x, size_y, name)
        self.rect = pygame.Rect(x, y, size_x, size_y)