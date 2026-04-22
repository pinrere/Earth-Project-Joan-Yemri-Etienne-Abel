import pygame

WIDTH, HEIGHT = 1400, 800

def show_level_transition(window, level, loop_count, parallax_bg):
    font_titre = pygame.font.SysFont('Arial', 80, bold=True)
    font_sous_titre = pygame.font.SysFont('Arial', 40)
    font_instructions = pygame.font.SysFont('Arial', 30)

    instructions_tuto = []

    # --- CALCUL DE L'OBJECTIF ---
    if level == 0:
        titre = "TUTORIEL"
        sous_titre = "Triez 6 déchets pour commencer l'aventure !"
        instructions_tuto = [
            "Poubelle Verte : Verre",
            "Poubelle Jaune : Bouteilles plastiques & Cartons",
            "Poubelle Noire : Pneus & Sacs poubelles",
            "Touche 'E' = Ramasser  |  'MAJ (Shift) + Clic' = Lancer"
        ]
    elif level == 1:
        titre = "NIVEAU 1"
        obj = 10 + (loop_count * 10)
        sous_titre = f"Objectif : {obj} déchets. Le trafic s'intensifie..."
    elif level == 2:
        titre = "NIVEAU 2"
        obj = 15 + (loop_count * 10)
        sous_titre = f"Objectif : {obj} déchets. Soyez rapide !"
    elif level == 3:
        titre = "NIVEAU 3"
        obj = 20 + (loop_count * 10)
        sous_titre = f"Objectif : {obj} déchets. L'enfer de la pollution !"
    elif level == 4:
        titre = "ÉVEIL ÉCOLOGIQUE"
        sous_titre = "Trier ne suffit plus... il y en a trop !"
        instructions_tuto = [
            "Vous réalisez que l'entreprise pollue sans arrêt.",
            "Il faut arrêter le problème à la racine !",
            "Traversez la carte vers la droite pour trouver l'usine."
        ]
    elif level == 5:
        titre = "BOSS FINAL"
        sous_titre = "Le PDG de la pollution vous attend."
        instructions_tuto = [
            "Ramassez les déchets avec E, lancez-les sur le boss avec MAJ + Clic !",
            "Esquivez ses projectiles et visez bien.",
            "En dessous de 5 PV, il entre en RAGE !"
        ]
    else:
        return

    attente = True
    while attente:
        # --- 1. ON DESSINE LE DÉCOR (Parallax) ---
        # On utilise 0 pour l'offset pour que le fond soit fixe pendant la pause
        parallax_bg.window = window
        parallax_bg.draw(0)

        # --- 2. ON AJOUTE UN VOILE SOMBRE (Pour que le texte soit lisible) ---
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) # 180 = semi-transparent
        window.blit(overlay, (0, 0))

        # --- 3. ON DESSINE LE TEXTE ---
        t1 = font_titre.render(titre, True, (255, 255, 255))
        t2 = font_sous_titre.render(sous_titre, True, (200, 255, 200))

        window.blit(t1, t1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 120)))
        window.blit(t2, t2.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))

        for i, ligne in enumerate(instructions_tuto):
            texte = font_instructions.render(ligne, True, (200, 200, 255))
            window.blit(texte, texte.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30 + (i * 35))))

        font_espace = pygame.font.SysFont('Arial', 35, italic=True)
        t3 = font_espace.render("Appuyez sur ESPACE pour commencer...", True, (255, 255, 150))
        window.blit(t3, t3.get_rect(center=(WIDTH // 2, HEIGHT - 100)))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    attente = False