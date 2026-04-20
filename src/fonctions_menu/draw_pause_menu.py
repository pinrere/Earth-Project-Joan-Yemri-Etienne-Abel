import pygame

WIDTH, HEIGHT = 1400, 800

def draw_pause_menu(window):
    font = pygame.font.SysFont("arial", 80)
    text = font.render("PAUSE", True, (255, 255, 255))
    window.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 3))

    font_small = pygame.font.SysFont("arial", 40)
    text2 = font_small.render("Appuie sur Echap pour reprendre", True, (200, 200, 200))
    window.blit(text2, (WIDTH // 2 - text2.get_width() // 2, HEIGHT // 2))

    pygame.display.update()