import pygame

WIDTH, HEIGHT = 1400, 800


def level_selection_menu(window):
    """Affiche un menu pour choisir son niveau et retourne le numéro du niveau choisi."""
    clock = pygame.time.Clock()
    font_titre = pygame.font.SysFont('Arial', 60, bold=True)
    font_btn = pygame.font.SysFont('Arial', 40)

    # Liste des niveaux (Texte affiché, ID du niveau)
    niveaux = [
        ("Tutoriel", 0),
        ("Niveau 1", 1),
        ("Niveau 2", 2),
        ("Niveau 3", 3),
        ("Niveau 4 (Alerte)", 4),
        ("Boss Final", 5)
    ]

    boutons = []
    start_y = 200
    # Création des zones cliquables
    for i, (texte, lvl) in enumerate(niveaux):
        rect = pygame.Rect(WIDTH // 2 - 150, start_y + i * 85, 300, 65)
        boutons.append((texte, lvl, rect))

    # On crée un fond semi-transparent au cas où on l'ouvre en mode Pause
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((20, 20, 20, 240))

    while True:
        window.blit(overlay, (0, 0))

        titre = font_titre.render("SÉLECTION DU NIVEAU", True, (255, 255, 255))
        window.blit(titre, titre.get_rect(center=(WIDTH // 2, 100)))

        mouse_pos = pygame.mouse.get_pos()

        # Dessin des boutons
        for texte, lvl, rect in boutons:
            # Change de couleur si on passe la souris dessus
            color = (100, 200, 100) if rect.collidepoint(mouse_pos) else (80, 80, 80)
            pygame.draw.rect(window, color, rect, border_radius=10)
            pygame.draw.rect(window, (255, 255, 255), rect, 2, border_radius=10)

            surface_texte = font_btn.render(texte, True, (255, 255, 255))
            window.blit(surface_texte, surface_texte.get_rect(center=rect.center))

        quitter = font_btn.render("ÉCHAP pour annuler/quitter", True, (200, 200, 200))
        window.blit(quitter, quitter.get_rect(center=(WIDTH // 2, HEIGHT - 80)))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None  # On annule la sélection
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Clic gauche
                    for texte, lvl, rect in boutons:
                        if rect.collidepoint(mouse_pos):
                            return lvl  # Retourne le numéro du niveau cliqué
        clock.tick(60)