import pygame

WIDTH, HEIGHT = 1400, 800

def show_level_transition(window, level):
    font_titre = pygame.font.SysFont('Arial', 80, bold=True)
    font_sous_titre = pygame.font.SysFont('Arial', 40)
    font_instructions = pygame.font.SysFont('Arial', 30)

    instructions_tuto = []

    if level == 0:
        titre = "Niveau 0"
        sous_titre = "Triez 6 déchets pour commencer l'aventure !"
        instructions_tuto = [
            "Poubelle Verte : Verre",
            "Poubelle Jaune : Bouteilles plastiques & Cartons",
            "Poubelle Noire : Pneus & Sacs poubelles",
            "Touche 'E' = Ramasser  |  'MAJ (Shift) + Clic' = Lancer"
        ]
    elif level == 1:
        titre = "NIVEAU 1"
        sous_titre = "Objectif : 10 déchets. Le trafic s'intensifie..."
    elif level == 2:
        titre = "NIVEAU 2"
        sous_titre = "Objectif : 15 déchets. Soyez rapide !"
    elif level == 3:
        titre = "NIVEAU 3"
        sous_titre = "Objectif : 20 déchets. L'enfer de la pollution !"
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

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    window.blit(overlay, (0, 0))

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

    attente = True
    while attente:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    attente = False