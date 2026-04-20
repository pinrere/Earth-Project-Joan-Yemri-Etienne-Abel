import pygame
from src.classes.ParallaxBackground import ParallaxBackground
from src.fonctions.get_block import get_block
from src.classes.button import Button
from src.classes.player import Player

WIDTH, HEIGHT = 1400, 800
FPS = 60

def main_menu(window):
    clock = pygame.time.Clock()
    parallax_bg = ParallaxBackground(window)

    block_size = 96
    grass_img = get_block(block_size, block_size, "dirtGrassBlock.png")
    dirt_img = get_block(block_size, block_size, "dirtBlock.png")

    play_btn = Button(WIDTH // 2 - 75, HEIGHT // 2 - 60, "bouttonJouer.png")
    quit_btn = Button(WIDTH // 2 - 75, HEIGHT // 2 + 70, "bouttonQuitter.png")

    menu_player = Player(WIDTH // 2 + 200, HEIGHT // 2 - 50, 60, 96)
    menu_player.direction = "right"

    menu_scroll = 0
    run_menu = True

    while run_menu:
        clock.tick(FPS)
        menu_scroll += 2

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        parallax_bg.draw(menu_scroll)

        for i in range(-1, (WIDTH // block_size) + 2):
            x_pos = (i * block_size) - ((menu_scroll * 0.7) % block_size)
            window.blit(grass_img, (x_pos, HEIGHT - block_size * 2))
            window.blit(dirt_img, (x_pos, HEIGHT - block_size))

        menu_player.x_vel = 0
        menu_player.update_sprite()
        window.blit(menu_player.sprite, (menu_player.hitbox.x - menu_player.sprite_offset_x,
                                         menu_player.hitbox.y - menu_player.sprite_offset_y))

        if play_btn.draw(window):
            run_menu = False

        if quit_btn.draw(window):
            pygame.quit()
            exit()

        pygame.display.update()
