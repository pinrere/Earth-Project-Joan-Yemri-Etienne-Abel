import pygame
import math
from os.path import join

WIDTH, HEIGHT = 1400, 800

def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    nb_tiles = math.ceil(WIDTH / width) + 2
    return image, width, nb_tiles