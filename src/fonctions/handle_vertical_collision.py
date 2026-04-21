from src.classes.block import Block
from src.classes.bridge import Bridge
from src.classes.platform import Platform


def handle_vertical_collision(player, objects):
    collided = []

    for obj in objects:
        if obj.__class__.__name__ not in ["Block", "Bridge", "Platform", "Plot", "ShadowBlock", "TrashBin", "Waste"]:
            continue

        if player.hitbox.colliderect(obj.rect):
            if player.y_vel > 0:
                if player.hitbox.bottom <= obj.rect.bottom:
                    player.hitbox.bottom = obj.rect.top
                    player.y_vel = 0
                    player.jump_count = 0
                    collided.append(obj)

            elif player.y_vel < 0:
                if player.hitbox.top >= obj.rect.top:
                    player.hitbox.top = obj.rect.bottom
                    player.y_vel = 0
                    collided.append(obj)

    player.rect.topleft = player.hitbox.topleft
    return collided