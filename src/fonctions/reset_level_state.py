def reset_level_state(player, water, current_level, height):
    player.health = player.max_health
    player.inventory.clear()
    player.trash_collected = 0
    player.hitbox.x = 100 if current_level == 5 else 400
    player.hitbox.y = 520
    player.y_vel = 0
    water.mistakes = 0
    water.target_y = height - 74
    water.rect.y = height - 74