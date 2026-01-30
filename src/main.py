import pygame
import entities.player as pl

# creation of the game window

screen_width = 640
screen_height = 480
screen = pygame.display.set_mode((screen_width,screen_height))
pygame.display.set_caption("Ecohead")

# creation of the player

player = pl.Player(100, 1,200, 200, 50)
projectile = None

# main

pygame.init()

playing = True
while playing:

    screen.fill((0,0,0))
    pygame.draw.rect(screen,(0,255,0),pygame.Rect(player.posx,player.posy,player.size,player.size))

    for events in pygame.event.get():
        if events.type == pygame.QUIT:
            running = False

    key = pygame.key.get_pressed()
    if key[pygame.K_q] and player.posx > 0:
        player.moveLeft()
    if key[pygame.K_d] and player.posx < screen_width-50:
        player.moveRight()
    if key[pygame.K_SPACE] and player.posy >= screen_height-50:
        player.jump()

    projectiles = []
    if key[pygame.K_z]:
        projectile = player.tirer()
        projectiles.append(projectile)

    compteur = 0
    for projectile in projectiles[:] :
        if projectile is not None:
            projectile.avancer()
            pygame.draw.rect(screen, (255, 255, 0), pygame.Rect(projectile.posx, projectile.posy, 10, 4))
            compteur += 1
            print(compteur)
            if projectile.get_posx() > screen_width or projectile.get_posx() < 0 :
                projectiles.remove(projectile)
                print("dell")

    pygame.display.update()

    if player.posy<screen_height-50:
        player.posy += 0.1