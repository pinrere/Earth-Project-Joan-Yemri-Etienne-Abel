import pygame
from os.path import join

def get_block(size_x, size_y, name):
    path = join("assets", "Terrain", name)
    image = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(image, (size_x, size_y))