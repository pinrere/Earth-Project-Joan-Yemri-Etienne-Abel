def handle_vertical_collision(player, objects):
    collided = []

    for obj in objects:
        if player.hitbox.colliderect(obj.rect):
            if player.y_vel > 0:
                player.hitbox.bottom = obj.rect.top
                player.y_vel = 0
                player.jump_count = 0
            elif player.y_vel < 0:
                player.hitbox.top = obj.rect.bottom
                player.y_vel = 0
            collided.append(obj)

    player.rect.topleft = player.hitbox.topleft
    return collided