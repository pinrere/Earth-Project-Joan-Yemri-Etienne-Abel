import random
from src.classes.plane import Avion

def spawn_avion(objects, level):
    direction = random.choice([1, -1])
    spawn_x = -1500 if direction == 1 else 3500

    if level == 0: speed = random.randint(2, 4)
    elif level == 1: speed = random.randint(4, 7)
    elif level == 2: speed = random.randint(7, 12)
    else: speed = random.randint(10, 16)

    spawn_y = random.randint(0, 150)
    avion = Avion(spawn_x, spawn_y, direction, speed=speed, level=level)
    objects.append(avion)

