import pygame

# creation of the game window

screen_width = 1920
screen_height = 1080
screen = pygame.display.set_mode((screen_width,screen_height))
pygame.display.set_caption("Ecohead")

# class Player

class Player:

     def __init__(self,pv,x,y):
         self.pv = pv
         self.x = x
         self.y = y

# main

pygame.init()

playing = True
while playing:
    screen.fill((255,0,0))
    pygame.display.update()