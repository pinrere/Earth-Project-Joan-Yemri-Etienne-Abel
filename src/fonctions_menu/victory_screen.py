import pygame

WIDTH, HEIGHT = 1400, 800
FPS = 60

def victory_screen(window):
    """Écran de victoire après avoir vaincu le boss."""
    clock = pygame.time.Clock()

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 20, 0, 220))
    window.blit(overlay, (0, 0))

    font_titre = pygame.font.SysFont('Arial', 80, bold=True)
    font_sous = pygame.font.SysFont('Arial', 40)
    font_btn = pygame.font.SysFont('Arial', 35)

    titre = font_titre.render("L'USINE EST DÉTRUITE !", True, (100, 255, 100))
    sous = font_sous.render("La nature reprend enfin ses droits...", True, (200, 255, 200))
    btn = font_btn.render("ESPACE pour rejouer  |  ECHAP pour quitter", True, (255, 255, 255))

    window.blit(titre, titre.get_rect(center=(WIDTH // 2, HEIGHT // 3)))
    window.blit(sous, sous.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
    window.blit(btn, btn.get_rect(center=(WIDTH // 2, HEIGHT * 2 // 3)))

    pygame.display.update()

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: return True
                if event.key == pygame.K_ESCAPE: return False
