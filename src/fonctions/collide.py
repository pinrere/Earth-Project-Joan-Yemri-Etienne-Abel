from src.classes.block import Block
from src.classes.bridge import Bridge
from src.classes.platform import Platform


def collide(player, objects, dx):
    player.hitbox.x += dx

    collided_object = None
    for obj in objects:
        if obj.__class__.__name__ not in ["Block", "Bridge", "Platform", "Plot", "ShadowBlock", "TrashBin", "Waste"]:
            continue

        if player.hitbox.colliderect(obj.rect):
            player.hitbox.x -= dx
            was_colliding = player.hitbox.colliderect(obj.rect)
            player.hitbox.x += dx

            if not was_colliding:
                collided_object = obj
                break

    player.hitbox.x -= dx
    return collided_object