import pygame
import entities.player as pl

# creation of the game window

screen_width = 1920
screen_height = 1080
screen = pygame.display.set_mode((screen_width,screen_height))
pygame.display.set_caption("Ecohead")

# creation of the player

player = pl.Player(100, 1,0,1040)

# main

pygame.init()

playing = True
while playing:

    screen.fill((0,0,0))
    playerOnScreen = pygame.draw.rect(screen,(255,0,0),pygame.Rect(player.posx, player.posy, 40, 40))
    pygame.display.update()

    for events in pygame.event.get():
        if events.type == pygame.QUIT:
            running = False

    key = pygame.key.get_pressed()
    if key[pygame.K_q] and player.posx > 0:
        player.moveLeft()
    if key[pygame.K_d] and player.posx < screen_width-40:
        player.moveRight()
    if key[pygame.K_SPACE] and player.posy >= screen_height - 40:
        player.jump()

    if player.posy<screen_height-40:
        player.posy += 0.2