import pygame
from src.classes.water import Water
from src.classes.shadowblock import ShadowBlock

WIDTH, HEIGHT = 1400, 800
FPS = 60
PLAYER_VEL = 5

def draw(window, bg_parallax, player, objects, offset_x, frames_left, wrong_bin_timer, throw_harder_timer,
         total_recycled, level_goal, boss=None):
    bg_parallax.draw(offset_x)

    for obj in objects:
        if isinstance(obj, Water):
            obj.draw(window, offset_x)

    for obj in objects:
        if isinstance(obj, Water):
            continue
        if isinstance(obj, ShadowBlock):
            continue
        if hasattr(obj, "collected") and obj.collected:
            continue
        obj.draw(window, offset_x)

    # Dessin du boss
    if boss and boss.alive:
        boss.draw(window, offset_x)

    player.draw(window, offset_x)
    player.draw_health_bar(window, offset_x)
    player.draw_trajectory(window, offset_x)
    player.draw_inventory(window)

    # --- TIMER ---
    font_timer = pygame.font.SysFont("arial", 40, bold=True)
    secondes_restantes = max(0, frames_left // FPS)
    couleur = (255, 50, 50) if secondes_restantes <= 15 else (255, 255, 255)
    texte_timer = font_timer.render(f"Temps : {secondes_restantes}s", True, couleur)
    window.blit(texte_timer, (WIDTH // 2 - texte_timer.get_width() // 2, 20))

    # --- COMPTEUR DÉCHETS (masqué pendant le boss) ---
    if boss is None:
        font_counter = pygame.font.SysFont("arial", 35, bold=True)
        texte_counter = font_counter.render(f"Déchets : {total_recycled} / {level_goal}", True, (200, 255, 200))
        window.blit(texte_counter, (WIDTH // 2 - texte_counter.get_width() // 2, 70))

    # --- MESSAGE : Mauvaise poubelle ---
    if wrong_bin_timer > 0:
        font_alerte = pygame.font.SysFont("arial", 60, bold=True)
        texte_alerte = font_alerte.render("Mauvaise poubelle attention !", True, (255, 50, 50))
        bg_alerte = pygame.Surface((texte_alerte.get_width() + 40, texte_alerte.get_height() + 20), pygame.SRCALPHA)
        bg_alerte.fill((0, 0, 0, 180))
        x_pos = WIDTH // 2 - texte_alerte.get_width() // 2
        y_pos = HEIGHT // 3
        window.blit(bg_alerte, (x_pos - 20, y_pos - 10))
        window.blit(texte_alerte, (x_pos, y_pos))

    # --- MESSAGE : Tire plus fort ! ---
    if throw_harder_timer > 0:
        font_alerte = pygame.font.SysFont("arial", 60, bold=True)
        texte_alerte = font_alerte.render("Tire plus fort !", True, (255, 150, 50))
        bg_alerte = pygame.Surface((texte_alerte.get_width() + 40, texte_alerte.get_height() + 20), pygame.SRCALPHA)
        bg_alerte.fill((0, 0, 0, 180))
        x_pos = WIDTH // 2 - texte_alerte.get_width() // 2
        y_pos = HEIGHT // 3 + 80
        window.blit(bg_alerte, (x_pos - 20, y_pos - 10))
        window.blit(texte_alerte, (x_pos, y_pos))

    pygame.display.update()
