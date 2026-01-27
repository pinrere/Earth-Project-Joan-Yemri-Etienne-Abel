import pygame
import entities.player as pl

# creation of the game window

screen_width = 1920
screen_height = 1080
screen = pygame.display.set_mode((screen_width,screen_height))
pygame.display.set_caption("Ecohead")

# creation of the player

player = pl.Player(100, 1,0,1017)

# main

pygame.init()

playing = True
while playing:

    screen.fill((0,0,0))
    screen.blit(pygame.image.load(player.skin),(player.posx,player.posy))
    pygame.display.update()

    for events in pygame.event.get():
        if events.type == pygame.QUIT:
            running = False

    key = pygame.key.get_pressed()
    if key[pygame.K_q] and player.posx > 0:
        player.moveLeft()
    if key[pygame.K_d] and player.posx < screen_width-63:
        player.moveRight()
    if key[pygame.K_SPACE] and player.posy >= screen_height-63:
        player.jump()

    if player.posy<screen_height-63:
        player.posy += 0.2