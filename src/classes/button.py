import pygame
from os.path import join

class Button:
    def __init__(self, x, y, name, scale=2):
        path = join("assets", "Menu", "Buttons", name)
        img = pygame.image.load(path).convert_alpha()

        width = img.get_width() * scale
        height = img.get_height() * scale
        self.image = pygame.transform.scale(img, (width, height))

        self.rect = self.image.get_rect(center=(x, y))
        self.clicked = False

    def draw(self, win):
        action = False
        pos = pygame.mouse.get_pos()

        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                self.clicked = True
                action = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        win.blit(self.image, (self.rect.x, self.rect.y))
        return action