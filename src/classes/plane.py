import random
import math
import pygame
from os.path import join
from src.classes.object import Object
from src.classes.waste import Waste
from src.classes.block import Block
from src.classes.bridge import Bridge
from src.classes.platform import Platform

class Avion(Object):
    ANIMATION_DELAY = 15

    def __init__(self, x, y, direction=1, speed=3, level=0):
        path = join("assets", "Items", "Plane", "planeSprite.png")
        sprite_sheet = pygame.image.load(path).convert_alpha()
        self.sprites = []
        frame_width = 350
        frame_height = 150

        for i in range(7):
            surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
            surface.blit(sprite_sheet, (0, 0), rect)
            self.sprites.append(surface)

        width = self.sprites[0].get_width()
        height = self.sprites[0].get_height()
        super().__init__(x, y, width, height, "avion")

        self.direction = direction
        self.speed = speed
        self.animation_count = 0
        self.level = level
        self.reset_drop_timer()

    def reset_drop_timer(self):
        if self.level == 1:
            self.drop_timer = random.randint(120, 200)
        elif self.level == 2:
            self.drop_timer = random.randint(50, 90)
        elif self.level >= 3:
            self.drop_timer = random.randint(15, 45)
        else:
            self.drop_timer = 9999

    def move(self):
        self.rect.x += self.speed * self.direction

    def update(self, objects, total_recycled=0, level_goal=999, is_rush_hour=False, player_trash_collected=0):
        self.move()
        self.animation_count += 1
        self.drop_timer -= 1

        if self.drop_timer <= 0:
            self.drop_waste(objects, total_recycled, level_goal, player_trash_collected)
            if is_rush_hour:
                self.drop_timer = random.randint(15, 30)
            else:
                self.drop_timer = random.randint(60, 120)

    def drop_waste(self, objects, total_recycled, level_goal, player_trash_collected):
        trash_x = self.rect.right - 20 if self.direction == -1 else self.rect.left + 20
        trash_y = self.rect.bottom - 15

        zone = 0
        if 100 <= trash_x <= 700: zone = 1
        elif 700 < trash_x <= 1300: zone = 2
        elif 1580 <= trash_x <= 2080: zone = 3
        elif 2080 < trash_x <= 2570: zone = 4

        if zone == 0:
            return

        marges_par_niveau = {1: 3, 2: 4, 3: 5}
        marge = marges_par_niveau.get(self.level, 0)
        wastes_on_map = [o for o in objects if isinstance(o, Waste) and not o.collected]

        if len(wastes_on_map) >= 6:
            return

        total_existing = len(wastes_on_map) + player_trash_collected + total_recycled
        if total_existing >= (level_goal + marge):
            return

        quota_zone = math.ceil((level_goal + marge) / 4)
        wastes_in_zone = 0
        for o in wastes_on_map:
            ox = o.rect.x
            if zone == 1 and 100 <= ox <= 700: wastes_in_zone += 1
            elif zone == 2 and 700 < ox <= 1300: wastes_in_zone += 1
            elif zone == 3 and 1580 <= ox <= 2080: wastes_in_zone += 1
            elif zone == 4 and 2080 < ox <= 2570: wastes_in_zone += 1

        if wastes_in_zone >= quota_zone:
            return

        test_rect = pygame.Rect(trash_x, trash_y, 30, 30)
        for obj in objects:
            if isinstance(obj, (Block, Bridge, Platform)) and test_rect.colliderect(obj.rect):
                return

        random_file = random.choice(["tire.png", "glassBottle.png", "cardboard.png", "bottle.png", "trashBag.png"])
        scales = {"tire.png": 3, "glassBottle.png": 1, "cardboard.png": 2.7, "bottle.png": 2, "trashBag.png": 3}
        s = scales.get(random_file, 3)
        trash = Waste(trash_x, trash_y, random_file, scale=s, vel_x=self.speed * self.direction, vel_y=2)
        objects.append(trash)

    def draw(self, win, offset_x):
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(self.sprites)
        sprite = self.sprites[sprite_index]
        if self.direction == -1:
            sprite = pygame.transform.flip(sprite, True, False)
        win.blit(sprite, (self.rect.x - offset_x, self.rect.y))