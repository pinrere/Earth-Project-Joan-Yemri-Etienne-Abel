import math
import pygame
from os.path import join
from src.classes.object import Object
from src.classes.block import Block
from src.classes.bridge import Bridge
from src.classes.platform import Platform

class Waste(Object):
    GRAVITY = 0.8
    FRICTION = 0.98
    BOUNCE_DAMPING = 0.6
    STOP_THRESHOLD = 1

    def __init__(self, x, y, filename, scale=3, name="waste", vel_x=0, vel_y=0):
        path = join("assets", "Items", "Waste", filename)
        img = pygame.image.load(path).convert_alpha()

        width = img.get_width() * scale
        height = img.get_height() * scale

        super().__init__(x, y, width, height, name)
        self.image.blit(pygame.transform.scale(img, (width, height)), (0, 0))

        self.filename = filename
        self.collected = False
        self.y_vel = vel_y
        self.x_vel = vel_x
        self.scale = scale
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.on_ground = False
        self.is_launched = False
        self.is_dangerous = True

    def update(self, objects, water=None):
        if not self.on_ground:
            self.y_vel += self.GRAVITY

        if water and self.rect.bottom > water.rect.y:
            self.x_vel *= 0.95
            self.y_vel *= 0.90
            vague = math.sin(pygame.time.get_ticks() / 200.0) * 5
            ligne_flottaison = water.rect.y + (self.rect.height * 0.7) + vague
            if self.rect.bottom > ligne_flottaison:
                self.y_vel -= 1.5

        self.x_vel *= self.FRICTION

        self.pos_x += self.x_vel
        self.rect.x = int(self.pos_x)

        for obj in objects:
            if obj.__class__.__name__ in ["Block", "Bridge", "Platform"] and self.rect.colliderect(obj.rect):
                if self.x_vel > 0:
                    self.rect.right = obj.rect.left
                elif self.x_vel < 0:
                    self.rect.left = obj.rect.right
                self.pos_x = self.rect.x
                self.x_vel *= -self.BOUNCE_DAMPING

        self.pos_y += self.y_vel
        self.rect.y = int(self.pos_y)

        self.on_ground = False

        for obj in objects:
            if obj.__class__.__name__ in ["Block", "Bridge", "Platform"] and self.rect.colliderect(obj.rect):
                if self.y_vel > 0:
                    self.rect.bottom = obj.rect.top
                    self.pos_y = self.rect.y
                    self.y_vel *= -self.BOUNCE_DAMPING
                    self.x_vel *= 0.8
                    if abs(self.y_vel) < self.STOP_THRESHOLD:
                        self.y_vel = 0
                        self.x_vel = 0
                        self.on_ground = True
                elif self.y_vel < 0:
                    self.rect.top = obj.rect.bottom
                    self.pos_y = self.rect.y
                    self.y_vel *= -self.BOUNCE_DAMPING

        for obj in objects:
            if isinstance(obj, Block) or isinstance(obj, Platform):
                if self.rect.colliderect(obj.rect):
                    # Si on est coincé à l'intérieur d'un bloc au spawn
                    # On se téléporte juste au-dessus
                    self.rect.bottom = obj.rect.top
                    self.pos_y = float(self.rect.y)  # On synchronise la position réelle
                    self.y_vel = 0  # Correction du nom de la variable
                    self.on_ground = True

        if self.on_ground:
            self.is_launched = False
            self.is_dangerous = False
            self.x_vel *= 0.9

