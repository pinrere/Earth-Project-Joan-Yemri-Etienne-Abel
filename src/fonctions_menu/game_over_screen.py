import pygame

WIDTH, HEIGHT = 1400, 800
FPS = 60

def game_over_screen(window, message="VOUS ÊTES MORT"):
    clock = pygame.time.Clock()

    if message == "VOUS ÊTES MORT":
        font_titre = pygame.font.SysFont('Arial', 100, bold=True)
        couleur_titre = (255, 50, 50)
    else:
        font_titre = pygame.font.SysFont('Arial', 70, bold=True)
        couleur_titre = (100, 200, 255)

    font_texte = pygame.font.SysFont('Arial', 40)

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    window.blit(overlay, (0, 0))

    titre = font_titre.render(message, True, couleur_titre)
    window.blit(titre, titre.get_rect(center=(WIDTH // 2, HEIGHT // 3)))

    instructions = font_texte.render("ESPACE pour rejouer  |  ECHAP pour quitter", True, (255, 255, 255))
    window.blit(instructions, instructions.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))

    pygame.display.update()

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: return True
                if event.key == pygame.K_ESCAPE: return False
