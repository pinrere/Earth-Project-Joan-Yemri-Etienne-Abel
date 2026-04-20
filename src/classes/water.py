from src.classes.object import Object
import pygame
from os.path import join

class Water(Object):
    ANIMATION_DELAY = 10
    SURFACE_COLOR = (116, 163, 59)

    def __init__(self, y, height, speed=1):
        super().__init__(-5000, y, 15000, height, "water")
        path = join("assets", "Other", "water.png")
        sprite_sheet = pygame.image.load(path).convert_alpha()

        self.sprites = []
        for i in range(4):
            surface = pygame.Surface((200, 50), pygame.SRCALPHA)
            surface.blit(sprite_sheet, (0, 0), pygame.Rect(0, i * 50, 200, 50))
            self.sprites.append(surface)

        self.image = self.sprites[0]
        self.animation_count = 0
        self.speed = speed
        self.mistakes = 0

    def update(self):
        self.animation_count += 1
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(self.sprites)
        self.image = self.sprites[sprite_index]

    def draw(self, win, offset_x):
        pygame.draw.rect(win, self.SURFACE_COLOR,
                         (self.rect.x - offset_x, self.rect.y + 50, self.rect.width, self.rect.height + 800))
        sprite_w = self.image.get_width()
        for x in range(0, self.rect.width, sprite_w):
            win.blit(self.image, (self.rect.x + x - offset_x, self.rect.y))

    def up(self):
        self.mistakes += 1
        if self.mistakes <= 3:
            self.rect.y -= 4
        else:
            self.rect.y -= 30