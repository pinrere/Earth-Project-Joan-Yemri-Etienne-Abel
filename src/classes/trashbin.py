import pygame
from os.path import join
from src.classes.object import Object

class TrashBin(Object):
    def __init__(self, x, y, color):
        img_map = {
            "green": "greenBeen.png",
            "yellow": "yellowBeen.png",
            "black": "blackBeen.png"
        }

        img = pygame.image.load(join("assets", "Items", "Waste", img_map[color])).convert_alpha()

        width = img.get_width() * 3
        height = img.get_height() * 3

        super().__init__(x, y, width, height, "trashbin")

        self.color = color
        self.image.blit(pygame.transform.scale(img, (width, height)), (0, 0))

        self.hitbox = pygame.Rect(
            x + width * 0.25,
            y + height * 0.35,
            width * 0.5,
            height * 0.55
        )

    def update(self):
        self.hitbox.x = self.rect.x + self.rect.width * 0.25
        self.hitbox.y = self.rect.y + self.rect.height * 0.35