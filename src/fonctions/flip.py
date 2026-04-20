import pygame

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]