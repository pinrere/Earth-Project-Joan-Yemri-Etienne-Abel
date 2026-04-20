import pygame
from src.fonctions.collide import collide
from src.fonctions.handle_vertical_collision import handle_vertical_collision
from src.classes.waste import Waste

PLAYER_VEL = 5

def handle_move(player, objects, offset_x):
    keys = pygame.key.get_pressed()
    mouse_buttons = pygame.mouse.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL)
    collide_right = collide(player, objects, PLAYER_VEL)

    if keys[pygame.K_q] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_d] and not collide_right:
        player.move_right(PLAYER_VEL)

    handle_vertical_collision(player, objects)

    for obj in objects:
        if isinstance(obj, Waste):
            if player.hitbox.colliderect(obj.rect.inflate(20, 20)):
                if keys[pygame.K_e]:
                    if player.collect_trash(obj, objects):
                        break

    if keys[pygame.K_LSHIFT] and player.trash_collected > 0 and player.throw_cooldown == 0:
        if mouse_buttons[0]:
            m_x, m_y = pygame.mouse.get_pos()
            player_screen_x = player.hitbox.centerx - offset_x

            v_x = (m_x - player_screen_x) * 0.05
            v_y = (m_y - player.hitbox.centery) * 0.12

            MAX_SPEED = 30
            v_x = max(min(v_x, MAX_SPEED), -MAX_SPEED)
            v_y = max(min(v_y, MAX_SPEED), -MAX_SPEED)

            spawn_x = player.hitbox.centerx - 15
            spawn_y = player.hitbox.top - 40

            if len(player.inventory) > 0:
                last_item_file, scale = player.inventory.pop()

                launched_item = Waste(spawn_x, spawn_y, last_item_file, scale, vel_x=v_x, vel_y=v_y)
                launched_item.is_launched = True
                objects.append(launched_item)

                player.trash_collected -= 1
                player.throw_cooldown = 30