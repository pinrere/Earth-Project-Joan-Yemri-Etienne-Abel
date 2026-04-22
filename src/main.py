import random
import pygame
from os.path import join
from src.classes.water import Water
from src.classes.block import Block
from src.classes.shadowblock import ShadowBlock
from src.classes.waste import Waste
from src.classes.plane import Avion
from src.classes.player import Player
from src.classes.bridge import Bridge
from src.classes.platform import Platform
from src.classes.trashbin import TrashBin
from src.classes.plot import Plot
from src.classes.boss import Boss
from src.fonctions.handle_vertical_collision import handle_vertical_collision
from src.fonctions.handle_move import handle_move
from src.fonctions.draw import draw
from src.fonctions.spawn_avion import spawn_avion
from src.classes.ParallaxBackground import ParallaxBackground
from src.fonctions_menu.draw_pause_menu import draw_pause_menu
from src.fonctions_menu.main_menu import main_menu
from src.fonctions_menu.show_level_transition import show_level_transition
from src.fonctions_menu.victory_screen import victory_screen
from src.fonctions_menu.game_over_screen import game_over_screen
pygame.init()

pygame.display.set_caption("Eco Guardian")

WIDTH, HEIGHT = 1400, 800
FPS = 60
PLAYER_VEL = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))

def main(window, start_level=0):
    clock = pygame.time.Clock()
    current_level = start_level
    total_recycled = 0

    level_goals = {0: 6, 1: 10, 2: 15, 3: 1, 4: 9999, 5: 9999}
    level_times = {0: 150, 1: 110, 2: 150, 3: 200, 4: 60, 5: 300}
    frames_left = level_times.get(current_level, 60) * FPS

    show_level_transition(window, current_level)

    parallax_bg = ParallaxBackground(window)
    block_size = 96

    img_top = pygame.image.load(join("assets", "Terrain", "topBridge.png")).convert_alpha()
    img_bottom = pygame.image.load(join("assets", "Terrain", "bottomBridge.png")).convert_alpha()
    bridge_width = 308
    bridge_x1 = 3 * block_size - 10
    bridge_y1 = HEIGHT - block_size * 2
    bridge_x2 = 16 * block_size - 10
    bridge_y2 = HEIGHT - block_size * 4
    bridge1 = Bridge(bridge_x1, bridge_y1, bridge_width, img_bottom, img_top)
    bridge2 = Bridge(bridge_x2, bridge_y2, bridge_width, img_bottom, img_top)

    player = Player(400, 520, 60, 96)

    floor = [Block(i * block_size, HEIGHT - block_size * 2, block_size, "dirtGrassBlock.png") for i in
             range(-10, 23) if i not in [3, 4, 5, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]]
    floor += [Block(i * block_size, HEIGHT - block_size * 4, block_size, "dirtGrassBlock.png") for i in
              range(14, 31) if i not in [16, 17, 18, 21, 22, 23, 24]]
    floor += [Block(i * block_size, HEIGHT - block_size, block_size, "dirtGrassBlock.png") for i in
              range(9, 25) if i not in [14, 15, 16, 17, 18, 19, 20, 21, 22]]
    floor += [Block(6 * block_size, HEIGHT - block_size * 6, block_size, "dirtGrassBlock.png")]

    bottom_floor = [Block(i * block_size, HEIGHT - block_size, block_size, "dirtBlock.png") for i in
                    range(-10, 31) if i not in [3, 4, 5, 9, 10, 11, 12, 13, 16, 17, 18, 23, 24]]
    bottom_floor += [Block(i * block_size, HEIGHT - block_size * 2, block_size, "dirtBlock.png") for i in
                     range(14, 31) if i not in [16, 17, 18, 21, 22, 23, 24]]
    bottom_floor += [Block(i * block_size, HEIGHT - block_size * 3, block_size, "dirtBlock.png") for i in
                     range(14, 31) if i not in [16, 17, 18, 21, 22, 23, 24]]
    bottom_floor += [Block(6 * block_size, HEIGHT - block_size * 5, block_size, "dirtBlock.png")]
    bottom_floor += [Block(i * block_size, HEIGHT - block_size * 7, block_size, "dirtBlock.png") for i in range(14, 16)]
    bottom_floor += [Block(i * block_size, HEIGHT - block_size * 8, block_size, "dirtBlock.png") for i in range(14, 16)]
    bottom_floor += [Block(i * block_size, HEIGHT - block_size * 9, block_size, "dirtBlock.png") for i in range(14, 16)]
    bottom_floor += [Block(i * block_size, HEIGHT - block_size * 10, block_size, "dirtBlock.png") for i in range(14, 16)]
    bottom_floor += [Block(i * block_size, HEIGHT - block_size * 11, block_size, "dirtBlock.png") for i in range(14, 16)]
    bottom_floor += [Block(i * block_size, HEIGHT - block_size * 12, block_size, "dirtBlock.png") for i in range(14, 16)]

    left_wall = [Block(-960, i * block_size, block_size, "dirtBlock.png") if i != 0
                 else Block(-960, i * block_size, block_size, "dirtGrassBlock.png") for i in range(-5, 9)]
    left_left__wall = [Block(-1056, j * block_size, block_size, "dirtBlock.png") if j != 0
                       else Block(-1056, j * block_size, block_size, "dirtGrassBlock.png") for j in range(-5, 9)]
    left_left_left_wall = [Block(-1152, i * block_size, block_size, "dirtBlock.png") if i != 0
                           else Block(-1152, i * block_size, block_size, "dirtGrassBlock.png") for i in range(-5, 9)]

    plateform1 = [Platform(100 + i * 120, 150) for i in range(2)]
    plateform2 = [Platform(96 * i - 60, 96 * 4 + 2) for i in range(7, 10)]
    plateform3 = [Platform(96 * i - 60, 96 * 2 + 2) for i in range(19, 23)]

    right_wall = [Block(27 * block_size, i * block_size, block_size, "dirtBlock.png") if i != 0
                  else Block(27 * block_size, i * block_size, block_size, "dirtGrassBlock.png") for i in range(-5, 9)]
    right_right_wall = [Block(28 * block_size, i * block_size, block_size, "dirtBlock.png") if i != 0
                        else Block(28 * block_size, i * block_size, block_size, "dirtGrassBlock.png") for i in range(-5, 9)]
    right_right_right_wall = [Block(29 * block_size, i * block_size, block_size, "dirtBlock.png") if i != 0
                               else Block(29 * block_size, i * block_size, block_size, "dirtGrassBlock.png") for i in range(-5, 9)]

    objects = [
        *plateform1, *plateform2, *plateform3,
        bridge1, bridge2,
        *bottom_floor, *floor,
        *left_wall, *left_left__wall, *left_left_left_wall,
        *right_wall, *right_right_wall, *right_right_right_wall,

        TrashBin(-800, HEIGHT - 175 - 96, "green"),
        TrashBin(-640, HEIGHT - 175 - 96, "yellow"),
        TrashBin(-480, HEIGHT - 175 - 96, "black"),

        ShadowBlock(-180, 0, 80, HEIGHT),
        Plot(-150, 536, 48, 72),

        Waste(block_size * 3, 0, "glassBottle.png", 1),
        Waste(block_size * 7, HEIGHT - block_size * 6 - 75, "cardboard.png", 2.7),
        Waste(block_size * 12, HEIGHT - block_size * 4 - 75, "bottle.png", 2),
        Waste(block_size * 15, HEIGHT - block_size * 2 - 75, "trashBag.png", 3),
        Waste(block_size * 20, 0, "tire.png", 3),
        Waste(block_size * 25, HEIGHT - block_size * 2 - 75, "glassBottle.png", 1),
    ]

    water = Water(HEIGHT - 74, 200, 0.1)
    objects.append(water)

    boss = None

    offset_x = 0
    scroll_area_width = 200
    scroll = 0
    camera_shifted = False
    saved_offset_x = 0
    saved_scroll = 0
    death_message = "VOUS ÊTES MORT"

    cpt = 0
    paused = False
    run = True

    wrong_bin_timer = 0
    throw_harder_timer = 0

    # Timer spawn déchets boss
    boss_waste_spawn_timer = 0
    BOSS_WASTE_SPAWN_COOLDOWN = 180  # 3 secondes

    while run:
        clock.tick(FPS)
        cpt += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()
                if event.key == pygame.K_ESCAPE:
                    paused = not paused

        if paused:
            draw_pause_menu(window)
            continue

        frames_left -= 1
        if frames_left <= 0:
            player.health = 0
            death_message = "Temps écoulé !"

        handle_move(player, objects, offset_x)
        player.loop(FPS)

        if player.hitbox.bottom >= water.rect.y + 10:
            player.health = 0
            player.y_vel = 0
            death_message = "L'océan a repris ses droits..."

        handle_vertical_collision(player, objects)

        WASTE_TYPES = {
            "glassBottle.png": "green",
            "cardboard.png": "yellow",
            "bottle.png": "yellow",
            "tire.png": "black",
            "trashBag.png": "black"
        }

        if current_level == 5 and boss is not None:

            # --- MISE À JOUR DU BOSS ---
            boss.update(player, objects)

            # --- GESTION DES DÉCHETS (Dégâts et Lancers) ---
            for obj in objects[:]:
                if isinstance(obj, Waste):
                    # Gravité et rebonds
                    obj.update(objects)

                    # 1. SI LE DÉCHET VOLE ET TE TOUCHE = DÉGÂTS
                    if obj.rect.colliderect(player.hitbox) and obj.is_dangerous:
                        if not player.hit:
                            player.health -= 1
                            player.make_hit()
                        # Le déchet explose/disparaît quand il te blesse
                        if obj in objects:
                            objects.remove(obj)
                        continue

                    # 2. SI TU AS LANCÉ LE DÉCHET ET QU'IL TOUCHE LE BOSS = DÉGÂTS AU BOSS
                    if obj.is_launched and obj.rect.colliderect(boss.hitbox):
                        boss.take_hit()
                        if obj in objects:
                            objects.remove(obj)

            # --- VICTOIRE ---
            if not boss.alive:
                draw(window, parallax_bg, player, objects, offset_x, frames_left,
                     wrong_bin_timer, throw_harder_timer, total_recycled,
                     level_goals.get(current_level, 999), boss)
                pygame.time.wait(800)
                rejouer = victory_screen(window)
                return rejouer

        else:
            for obj in objects[:]:

                if isinstance(obj, Water):
                    obj.update()
                    if player.hitbox.bottom >= obj.rect.y + 10:
                        player.health = 0
                        death_message = "Vous avez noyé votre planète..."

                if isinstance(obj, Avion):
                    total_frames = level_times.get(current_level, 60) * FPS
                    frames_elapsed = total_frames - frames_left
                    is_rush_hour = frames_elapsed < (total_frames / 5)

                    obj.update(objects, total_recycled, level_goals.get(current_level, 999), is_rush_hour,
                               player.trash_collected)

                    if (obj.direction == 1 and obj.rect.left > 3500) or (obj.direction == -1 and obj.rect.right < -1500):
                        if obj in objects: objects.remove(obj)
                        continue

                    if obj.rect.colliderect(player.hitbox):
                        if not player.hit:
                            player.health -= 2
                            player.make_hit()

                if isinstance(obj, Waste):
                    obj.update(objects, water=water)

                    if obj.rect.colliderect(player.hitbox) and obj.is_dangerous:
                        if current_level > 0:
                            if not player.hit:
                                player.health -= 1
                                player.make_hit()
                            if obj in objects: objects.remove(obj)
                            continue

                    if current_level == 0 and obj.on_ground and obj.rect.x <= -130:
                        player.collect_trash(obj, objects)
                        throw_harder_timer = 120
                        continue

                    for other in objects:
                        if isinstance(other, TrashBin):
                            if obj.rect.colliderect(other.hitbox) and obj.is_launched:
                                correct_color = WASTE_TYPES.get(obj.filename)
                                if correct_color == other.color:
                                    objects.remove(obj)
                                    total_recycled += 1
                                    if total_recycled >= level_goals.get(current_level, 999):
                                        current_level += 1
                                        total_recycled = 0
                                        frames_left = level_times.get(current_level, 60) * FPS
                                        show_level_transition(window, current_level)

                                        player.hitbox.x = 400
                                        player.hitbox.y = 520
                                        player.x_vel = 0
                                        player.y_vel = 0
                                        player.health = player.max_health
                                        player.inventory.clear()
                                        player.trash_collected = 0

                                        for o in objects[:]:
                                            if isinstance(o, Waste):
                                                objects.remove(o)

                                        if current_level in [1, 2, 3]:
                                            zones_possibles = [(100, 700), (701, 1300), (1580, 2080), (2081, 2570)]
                                            for _ in range(3):
                                                zone_choisie = random.choice(zones_possibles)
                                                spawn_x = random.randint(zone_choisie[0], zone_choisie[1])
                                                r_file = random.choice(["tire.png", "glassBottle.png", "cardboard.png", "bottle.png", "trashBag.png"])
                                                scales = {"tire.png": 3, "glassBottle.png": 1, "cardboard.png": 2.7, "bottle.png": 2, "trashBag.png": 3}
                                                objects.append(Waste(spawn_x, 0, r_file, scales.get(r_file, 3)))

                                        if current_level == 4:
                                            for o in objects[:]:
                                                if isinstance(o, Block) and o.rect.x >= 27 * block_size and o.rect.y < HEIGHT - block_size * 4:
                                                    objects.remove(o)
                                else:
                                    if current_level == 0:
                                        wrong_bin_timer = 120
                                        player.collect_trash(obj, objects)
                                    else:
                                        if current_level >= 1:
                                            water.up()
                                        if obj in objects:
                                            objects.remove(obj)
                                break

            # --- SPAWN DES AVIONS ---
            if current_level > 0:
                avions_actifs = sum(1 for o in objects if isinstance(o, Avion))
                max_planes = {1: 2, 2: 3, 3: 4, 4: 8}.get(current_level, 0)
                spawn_chance = {1: 100, 2: 50, 3: 20, 4: 10}.get(current_level, 999)

                if avions_actifs < max_planes:
                    if random.randint(1, spawn_chance) == 1:
                        spawn_avion(objects, current_level)

        # --- CONDITION DE DÉFAITE ---
        if player.health <= 0:
            player.health = player.max_health

        # --- PASSAGE VERS L'ARÈNE DU BOSS (NIVEAU 5) ---
        if current_level == 4 and player.hitbox.x >= 28 * block_size:
            current_level = 5
            frames_left = level_times.get(current_level, 300) * FPS
            death_message = "VOUS ÊTES MORT"
            player.health = player.max_health
            player.inventory.clear()
            player.trash_collected = 0

            show_level_transition(window, current_level)
            pygame.event.clear()  # <-- vide la queue APRES la transition

            objects.clear()
            # Sol plat de l'arène (sans tour centrale)
            boss_floor = [Block(i * block_size, HEIGHT - block_size * 2, block_size, "dirtGrassBlock.png") for i in range(-3, 22)]
            boss_bottom = [Block(i * block_size, HEIGHT - block_size, block_size, "dirtBlock.png") for i in range(-3, 22)]

            # Quelques plateformes pour rendre l'arène moins vide
            boss_plateforms = [
                Platform(200, HEIGHT - block_size * 4),
                Platform(500, HEIGHT - block_size * 5),
                Platform(900, HEIGHT - block_size * 4),
                Platform(1200, HEIGHT - block_size * 5),
            ]

            # Murs
            boss_left_wall = [Block(-3 * block_size, i * block_size, block_size, "dirtBlock.png") if i != 0
                               else Block(-3 * block_size, i * block_size, block_size, "dirtGrassBlock.png") for i in range(-5, 9)]
            boss_left_left_wall = [Block(-4 * block_size, i * block_size, block_size, "dirtBlock.png") if i != 0
                              else Block(-4 * block_size, i * block_size, block_size, "dirtGrassBlock.png") for i in range(-5, 9)]
            boss_left_left_left_wall = [Block(-5 * block_size, i * block_size, block_size, "dirtBlock.png") if i != 0
                                   else Block(-5 * block_size, i * block_size, block_size, "dirtGrassBlock.png") for i in range(-5, 9)]
            boss_right_wall = [Block(20 * block_size, i * block_size, block_size, "dirtBlock.png") if i != 0
                                else Block(20 * block_size, i * block_size, block_size, "dirtGrassBlock.png") for i in range(-5, 9)]
            boss_right_right_wall = [Block(21 * block_size, i * block_size, block_size, "dirtBlock.png") if i != 0
                               else Block(21 * block_size, i * block_size, block_size, "dirtGrassBlock.png") for i in range(-5, 9)]
            boss_right_right_right_wall = [Block(22 * block_size, i * block_size, block_size, "dirtBlock.png") if i != 0
                                     else Block(22 * block_size, i * block_size, block_size, "dirtGrassBlock.png") for i in range(-5, 9)]

            objects.extend(boss_floor)
            objects.extend(boss_bottom)
            objects.extend(boss_plateforms)
            objects.extend(boss_left_wall)
            objects.extend(boss_right_wall)
            objects.extend(boss_left_left_wall)
            objects.extend(boss_right_right_wall)
            objects.extend(boss_left_left_left_wall)
            objects.extend(boss_right_right_right_wall)


            # Spawn du boss à droite de l'arène
            boss = Boss(18 * block_size, HEIGHT - block_size * 4)
            boss_waste_spawn_timer = 60  # Premier déchet après 1 seconde

            player.hitbox.x = 100
            player.hitbox.y = HEIGHT - block_size * 3

            offset_x = 0
            scroll = 0
            saved_offset_x = 0
            saved_scroll = 0
            camera_shifted = False

        if current_level < 5:
            if player.hitbox.x <= -95 and not camera_shifted:
                saved_offset_x = offset_x
                saved_scroll = scroll
                offset_x -= 800
                scroll -= 800
                camera_shifted = True
            elif player.hitbox.x > -95 and camera_shifted:
                offset_x = saved_offset_x
                scroll = saved_scroll
                camera_shifted = False

            # La caméra normale qui suit le joueur reste à l'extérieur du "if"
        if not camera_shifted:
            if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                    (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
                offset_x += player.x_vel
                scroll -= player.x_vel

            if abs(scroll) > WIDTH:
                scroll = 0

        if wrong_bin_timer > 0:
            wrong_bin_timer -= 1
        if throw_harder_timer > 0:
            throw_harder_timer -= 1

        level_goal = level_goals.get(current_level, 999)

        draw(window, parallax_bg, player, objects, offset_x, frames_left,
             wrong_bin_timer, throw_harder_timer, total_recycled, level_goal,
             boss if current_level == 5 else None)

    pygame.quit()
    quit()


if __name__ == "__main__":
    jeu_en_cours = True

    while jeu_en_cours:
        main_menu(window)
        vouloir_rejouer = main(window, start_level=3)
        if not vouloir_rejouer:
            jeu_en_cours = False

    pygame.quit()
    quit()