import pygame
from src.classes.object import Object

class Bridge(Object):
    def __init__(self, x, y, width, bottom_img, top_img):
        super().__init__(x, y, width, bottom_img.get_height(), "bridge")
        self.bottom_img = bottom_img
        self.top_img = top_img
        self.rect = pygame.Rect(x, y, width, 20)

    def draw(self, win, offset_x):
        win.blit(self.bottom_img, (self.rect.x - offset_x, self.rect.y))
        win.blit(self.top_img, (self.rect.x - offset_x, self.rect.y - self.top_img.get_height() + 3))
