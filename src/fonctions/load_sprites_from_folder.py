import os
import pygame
from os.path import join
from collections import defaultdict

def load_sprites_from_folder(dir1, dir2, scale=2, direction=False):
    path = join("assets", dir1, dir2)
    files = [f for f in os.listdir(path) if f.endswith(".png")]

    animations = defaultdict(list)

    for file in sorted(files):
        name = ''.join([c for c in file if not c.isdigit()]).replace(".png", "")
        image = pygame.image.load(join(path, file)).convert_alpha()

        if scale != 1:
            image = pygame.transform.scale_by(image, scale)

        animations[name].append(image)

    all_sprites = {}

    if direction:
        for anim, frames in animations.items():
            all_sprites[f"{anim}_right"] = frames
            all_sprites[f"{anim}_left"] = [pygame.transform.flip(f, True, False) for f in frames]
    else:
        all_sprites = dict(animations)

    return all_sprites
