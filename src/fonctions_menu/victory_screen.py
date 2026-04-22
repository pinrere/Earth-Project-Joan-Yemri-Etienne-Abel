import pygame

WIDTH, HEIGHT = 1400, 800
FPS = 60


def victory_screen(window):
    clock = pygame.time.Clock()

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((20, 10, 0, 230))  # Fond sombre
    window.blit(overlay, (0, 0))

    font_titre = pygame.font.SysFont('Arial', 70, bold=True)
    font_sous = pygame.font.SysFont('Arial', 35)
    font_btn = pygame.font.SysFont('Arial', 30, italic=True)

    # Nouveaux textes avec la morale
    titre = font_titre.render("VOUS AVEZ DÉTRUIT L'USINE !", True, (100, 255, 100))
    sous1 = font_sous.render("C'est une belle victoire pour la planète...", True, (200, 255, 200))
    sous2 = font_sous.render("Mais ce n'est qu'une entreprise parmi des milliers d'autres.", True, (255, 150, 50))

    # Bouton adapté pour encourager à recommencer
    btn = font_btn.render("Appuyez sur ESPACE pour continuer le combat  |  ECHAP pour abandonner", True,
                          (255, 255, 255))

    # Affichage bien centré
    window.blit(titre, titre.get_rect(center=(WIDTH // 2, HEIGHT // 3 - 30)))
    window.blit(sous1, sous1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
    window.blit(sous2, sous2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))
    window.blit(btn, btn.get_rect(center=(WIDTH // 2, HEIGHT * 2 // 3 + 40)))

    pygame.display.update()

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: return True
                if event.key == pygame.K_ESCAPE: return False