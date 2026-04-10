import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join
from collections import defaultdict
pygame.init()

pygame.display.set_caption("Eco Guardian")

WIDTH, HEIGHT = 1400, 800
FPS = 60
PLAYER_VEL = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprites_from_folder(dir1, dir2, scale=2, direction=False):
    path = join("assets", dir1, dir2)
    files = [f for f in os.listdir(path) if f.endswith(".png")]

    animations = defaultdict(list)

    for file in sorted(files):
        name = ''.join([c for c in file if not c.isdigit()]).replace(".png", "")
        image = pygame.image.load(join(path, file)).convert_alpha()

        if scale != 1:
            image = pygame.transform.scale_by(image, scale)

        animations[name].append(image)

    all_sprites = {}

    if direction:
        for anim, frames in animations.items():
            all_sprites[f"{anim}_right"] = frames
            all_sprites[f"{anim}_left"] = [pygame.transform.flip(f, True, False) for f in frames]
    else:
        all_sprites = dict(animations)

    return all_sprites

def load_sprite_sheets(dir1, dir2, width, height, direction = False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites

def get_block(size_x, size_y, name):
    path = join("assets", "Terrain", name)
    image = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(image, (size_x, size_y))

class Button:
    def __init__(self, x, y, name, scale=2):
        path = join("assets", "Menu", "Buttons", name)
        img = pygame.image.load(path).convert_alpha()

        width = img.get_width() * scale
        height = img.get_height() * scale
        self.image = pygame.transform.scale(img, (width, height))

        self.rect = self.image.get_rect(center=(x, y))
        self.clicked = False

    def draw(self, win):
        action = False
        pos = pygame.mouse.get_pos()

        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                self.clicked = True
                action = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        win.blit(self.image, (self.rect.x, self.rect.y))
        return action

class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 0.8
    SPRITES = load_sprites_from_folder("MainCharacters", "MaleChar",3, True)
    ANIMATION_DELAY = 4

    def __init__(self, x, y, width, height):
        super().__init__()
        self.hitbox = pygame.Rect(x, y, width, height-2)
        self.rect = self.hitbox.copy()
        self.x_vel = 0
        self.y_vel = 0
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.sprite_offset_x = 67
        self.sprite_offset_y = 50
        self.max_health = 6
        self.health = 6
        self.trash_collected = 0
        self.MAX_TRASH = 3
        self.trash_icon_size = 8
        self.trash_icon_spacing = 7
        self.inventory = []
        self.throw_cooldown = 0
        self.slot_image = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.rect(self.slot_image, (100, 100, 100, 150), (0, 0, 60, 60), border_radius=5)
        pygame.draw.rect(self.slot_image, (255, 255, 255), (0, 0, 60, 60), 2, border_radius=5)
        self.water_timer = 0

    HEART_IMG = pygame.image.load(join("assets", "Other", "heart.png")).convert_alpha()

    def draw_health_bar(self, win, offset_x):
        heart_scale = 1.5
        heart = pygame.transform.scale(
            self.HEART_IMG,
            (int(self.HEART_IMG.get_width() * heart_scale),
             int(self.HEART_IMG.get_height() * heart_scale))
        )

        half_heart = heart.subsurface((0, 0, heart.get_width() // 2, heart.get_height()))

        grey = heart.copy()
        grey.fill((80, 80, 80, 180), special_flags=pygame.BLEND_RGBA_MULT)

        bar_x = 20
        bar_y = 20
        spacing = heart.get_width() + 4

        for i in range(3):
            x_pos = bar_x + i * spacing

            win.blit(grey, (x_pos, bar_y))

            if self.health >= (i + 1) * 2:
                win.blit(heart, (x_pos, bar_y))
            elif self.health == (i * 2) + 1:
                win.blit(half_heart, (x_pos, bar_y))

    def draw_trajectory(self, win, offset_x):
        keys = pygame.key.get_pressed()
        if not (keys[pygame.K_LSHIFT] and self.trash_collected > 0):
            return

        start_x = self.hitbox.centerx - offset_x
        start_y = self.hitbox.centery

        m_x, m_y = pygame.mouse.get_pos()

        vx = (m_x - start_x) * 0.05
        vy = (m_y - start_y) * 0.1

        MAX_SPEED = 30
        vx = max(min(vx, MAX_SPEED), -MAX_SPEED)
        vy = max(min(vy, MAX_SPEED), -MAX_SPEED)

        for i in range(1, 15):
            t = i * 1.5
            px = start_x + vx * t
            py = start_y + vy * t + 0.5 * Waste.GRAVITY * (t ** 2)

            pygame.draw.circle(win, (255, 255, 255), (int(px), int(py)), 2)

    def draw_inventory(self, win):
        padding = 20
        slot_size = 60
        gap = 10
        target_max = 40

        start_x = WIDTH - padding - slot_size
        start_y = padding

        for i in range(self.MAX_TRASH):
            x = start_x - (i * (slot_size + gap))
            win.blit(self.slot_image, (x, start_y))

        for i, item_data in enumerate(reversed(self.inventory)):
            if i < self.MAX_TRASH:
                filename, _ = item_data
                path = join("assets", "Items", "Waste", filename)
                item_img = pygame.image.load(path).convert_alpha()

                original_width = item_img.get_width()
                original_height = item_img.get_height()

                ratio = target_max / max(original_width, original_height)

                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)

                item_img = pygame.transform.scale(item_img, (new_width, new_height))

                x_slot = start_x - (i * (slot_size + gap))

                pos_x = x_slot + (slot_size - new_width) // 2
                pos_y = start_y + (slot_size - new_height) // 2

                win.blit(item_img, (pos_x, pos_y))

    def jump(self):
        if self.jump_count == 0:
            self.y_vel = -17
        elif self.jump_count == 1:
            self.y_vel = -12

        self.animation_count = 0
        self.jump_count += 1

        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.hitbox.x += dx
        self.hitbox.y += dy
        self.rect.topleft = self.hitbox.topleft

    def make_hit(self):
        self.hit = True
        self.hit_count = 0

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += self.GRAVITY

        self.hitbox.x += self.x_vel
        self.rect.topleft = self.hitbox.topleft

        self.hitbox.y += self.y_vel
        self.rect.topleft = self.hitbox.topleft

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1

        if self.throw_cooldown > 0:
            self.throw_cooldown -= 1

        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.fall_count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        self.sprite_offset_y = 50
        self.sprite_offset_x = 67

        if self.hit:
            sprite_sheet = "hit"

        elif self.y_vel < 0:
            sprite_sheet = "jump"
            self.sprite_offset_y = 34

        elif self.y_vel > self.GRAVITY:
            sprite_sheet = "fall"
            self.sprite_offset_y = 34

        elif self.x_vel != 0:
            sprite_sheet = "run"
            if self.direction == "right":
                self.sprite_offset_x += 6
            else:
                self.sprite_offset_x -= 6

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]

        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]

        self.animation_count += 1
        self.update()

    def update(self):
        self.rect.topleft = self.hitbox.topleft

    def draw(self, win, offset_x):
        win.blit(
            self.sprite,
            (self.hitbox.x - offset_x - self.sprite_offset_x,
             self.hitbox.y - self.sprite_offset_y)
        )

    def collect_trash(self, obj, objects):
        if self.trash_collected < self.MAX_TRASH:
            self.trash_collected += 1
            self.inventory.append((obj.filename, obj.scale))
            if obj in objects:
                objects.remove(obj)
            return True
        return False

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name = None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class ShadowBlock(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "shadow")

        img = pygame.image.load(join("assets", "Other", "Shadow.png")).convert_alpha()
        img = pygame.transform.scale(img, (width, height))

        self.image.blit(img, (0, 0))

class Plot(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "plot")
        path = join("assets", "Other", "Plot.png")
        img = pygame.image.load(path).convert_alpha()

        self.image = pygame.transform.scale(img, (width, height))

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Waste(Object):
    GRAVITY = 0.8
    FRICTION = 0.98
    BOUNCE_DAMPING = 0.6
    STOP_THRESHOLD = 1

    def __init__(self, x, y, filename, scale=3, name="waste", vel_x=0, vel_y=0):
        path = join("assets", "Items", "Waste", filename)
        img = pygame.image.load(path).convert_alpha()

        width = img.get_width() * scale
        height = img.get_height() * scale

        super().__init__(x, y, width, height, name)
        self.image.blit(pygame.transform.scale(img, (width, height)), (0, 0))

        self.filename = filename
        self.collected = False
        self.y_vel = vel_y
        self.x_vel = vel_x
        self.scale = scale
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.on_ground = False

    def hit_vertical(self, objects):
        self.rect.y += self.y_vel
        for obj in objects:
            if isinstance(obj, Block) or isinstance(obj, Bridge) or isinstance(obj, Platform):
                if self.rect.colliderect(obj.rect):
                    self.rect.bottom = obj.rect.top
                    self.y_vel = 0
                    break

    def update(self, objects):
        if not self.on_ground:
            self.y_vel += self.GRAVITY

        self.x_vel *= self.FRICTION

        self.pos_x += self.x_vel
        self.rect.x = int(self.pos_x)

        for obj in objects:
            if (isinstance(obj, Block) or isinstance(obj, Bridge) or isinstance(obj, Platform)) and self.rect.colliderect(obj.rect):

                if self.x_vel > 0:
                    self.rect.right = obj.rect.left
                elif self.x_vel < 0:
                    self.rect.left = obj.rect.right

                self.pos_x = self.rect.x

                self.x_vel *= -self.BOUNCE_DAMPING

        self.pos_y += self.y_vel
        self.rect.y = int(self.pos_y)

        self.on_ground = False

        for obj in objects:
            if (isinstance(obj, Block) or isinstance(obj, Bridge) or isinstance(obj, Platform)) and self.rect.colliderect(obj.rect):

                if self.y_vel > 0:
                    self.rect.bottom = obj.rect.top
                    self.pos_y = self.rect.y

                    self.y_vel *= -self.BOUNCE_DAMPING
                    self.x_vel *= 0.8

                    if abs(self.y_vel) < self.STOP_THRESHOLD:
                        self.y_vel = 0
                        self.x_vel = 0
                        self.on_ground = True

                elif self.y_vel < 0:
                    self.rect.top = obj.rect.bottom
                    self.pos_y = self.rect.y
                    self.y_vel *= -self.BOUNCE_DAMPING

        if self.on_ground:
            self.is_launched = False
            self.x_vel *= 0.9

class Block(Object):
    def __init__(self, x, y, size_y, name, size_x=96):
        super().__init__(x, y, size_x, size_y)
        self.image = get_block(size_x, size_y, name)
        self.rect = pygame.Rect(x, y, size_x, size_y)

class TrashBin(Object):
    def __init__(self, x, y, color):
        img_map = {
            "green": "greenBeen.png",
            "yellow": "yellowBeen.png",
            "black": "blackBeen.png"
        }

        img = pygame.image.load(join("assets", "Items", "Waste", img_map[color])).convert_alpha()

        width = img.get_width() * 3
        height = img.get_height() * 3

        super().__init__(x, y, width, height, "trashbin")

        self.color = color
        self.image.blit(pygame.transform.scale(img, (width, height)), (0, 0))

        self.hitbox = pygame.Rect(
            x + width * 0.25,
            y + height * 0.35,
            width * 0.5,
            height * 0.55
        )

    def update(self):
        self.hitbox.x = self.rect.x + self.rect.width * 0.25
        self.hitbox.y = self.rect.y + self.rect.height * 0.35

def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    nb_tiles = math.ceil(WIDTH / width) + 2

    return image, width, nb_tiles


def draw(window, bg_parallax, player, objects, offset_x, frames_left, wrong_bin_timer, throw_harder_timer, total_recycled, level_goal):
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

    player.draw(window, offset_x)
    player.draw_health_bar(window, offset_x)
    player.draw_trajectory(window, offset_x)
    player.draw_inventory(window)

    # --- AFFICHAGE DU TIMER ---
    font_timer = pygame.font.SysFont("arial", 40, bold=True)
    secondes_restantes = max(0, frames_left // FPS)
    couleur = (255, 50, 50) if secondes_restantes <= 15 else (255, 255, 255)
    texte_timer = font_timer.render(f"Temps : {secondes_restantes}s", True, couleur)
    window.blit(texte_timer, (WIDTH // 2 - texte_timer.get_width() // 2, 20))

    # --- AFFICHAGE DU COMPTEUR DE DÉCHETS ---
    font_counter = pygame.font.SysFont("arial", 35, bold=True)
    texte_counter = font_counter.render(f"Déchets : {total_recycled} / {level_goal}", True, (200, 255, 200)) # Une petite couleur verdâtre
    window.blit(texte_counter, (WIDTH // 2 - texte_counter.get_width() // 2, 70)) # Placé juste en dessous du timer (y=70)

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

def collide(player, objects, dx):
    player.hitbox.x += dx

    collided_object = None
    for obj in objects:
        if player.hitbox.colliderect(obj.rect):
            collided_object = obj
            break

    player.hitbox.x -= dx
    player.rect.topleft = player.hitbox.topleft
    return collided_object

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

            # --- CORRECTION BUG 2 : On fait spawn le déchet au-dessus de la tête ---
            # Ça évite qu'il apparaisse "à l'intérieur" d'un mur si tu es collé à lui
            spawn_x = player.hitbox.centerx - 15
            spawn_y = player.hitbox.top - 40

            if len(player.inventory) > 0:
                last_item_file, scale = player.inventory.pop()

                launched_item = Waste(spawn_x, spawn_y, last_item_file, scale, vel_x=v_x, vel_y=v_y)
                objects.append(launched_item)

                player.trash_collected -= 1
                player.throw_cooldown = 30


class Avion(Object):
    """Gère l'avion qui traverse l'écran et largue des déchets."""
    ANIMATION_DELAY = 15  # Vitesse de l'animation (plus c'est bas, plus c'est rapide)

    def __init__(self, x, y, direction=1, speed=3, level=0):
        # Chargement et découpage du sprite sheet de l'avion
        path = join("assets", "Items", "Plane", "planeSprite.png")
        sprite_sheet = pygame.image.load(path).convert_alpha()
        self.sprites = []
        frame_width = 350
        frame_height = 150
        scale = 1

        for i in range(7):
            surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
            surface.blit(sprite_sheet, (0, 0), rect)
            if scale != 1:
                surface = pygame.transform.scale_by(surface, scale)
            self.sprites.append(surface)

        width = self.sprites[0].get_width()
        height = self.sprites[0].get_height()
        super().__init__(x, y, width, height, "avion")

        self.direction = direction
        self.speed = speed
        self.animation_count = 0
        self.level = level
        self.reset_drop_timer()

    def reset_drop_timer(self):
        """Définit le temps avant le prochain largage selon le niveau."""
        # Un timer aléatoire permet une bonne répartition sur toute la map
        if self.level == 1:
            self.drop_timer = random.randint(120, 200) # Lent
        elif self.level == 2:
            self.drop_timer = random.randint(50, 90)   # Rapide
        elif self.level >= 3:
            self.drop_timer = random.randint(15, 45)   # Mitraillette de déchets
        else:
            self.drop_timer = 9999

    def move(self):
        """Déplace l'avion horizontalement."""
        self.rect.x += self.speed * self.direction

    def update(self, objects):
        """Met à jour la position, l'animation et gère le largage."""
        self.move()
        self.animation_count += 1
        self.drop_timer -= 1

        # Zone de largage autorisée
        if self.drop_timer <= 0:
            if -140 <= self.rect.x <= 2800:
                self.drop_waste(objects)
            self.reset_drop_timer()

    def drop_waste(self, objects):
        # --- LIMITE MAX DE DÉCHETS PAR NIVEAU ---
        max_wastes_per_level = {1: 5, 2: 25, 3: 125}
        max_w = max_wastes_per_level.get(self.level, 0)

        # On compte combien de déchets sont actuellement sur la map
        current_waste = sum(1 for o in objects if isinstance(o, Waste) and not o.collected)

        # Si on a atteint la limite, on ne lâche rien
        if current_waste >= max_w:
            return

        trash_x = self.rect.right - 20 if self.direction == -1 else self.rect.left + 20
        trash_y = self.rect.bottom - 15

        test_rect = pygame.Rect(trash_x, trash_y, 30, 30)
        for obj in objects:
            if isinstance(obj, (Block, Bridge, Platform)) and test_rect.colliderect(obj.rect):
                return

        random_file = random.choice(["tire.png", "glassBottle.png", "cardboard.png", "bottle.png", "trashBag.png"])
        scales = {"tire.png": 3, "glassBottle.png": 1, "cardboard.png": 2.7, "bottle.png": 2, "trashBag.png": 3}
        s = scales.get(random_file, 3)

        trash = Waste(trash_x, trash_y, random_file, scale=s, vel_x=self.speed * self.direction, vel_y=2)
        objects.append(trash)

    def draw(self, win, offset_x):
        """Affiche l'avion avec la bonne frame d'animation et direction."""
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(self.sprites)
        sprite = self.sprites[sprite_index]

        if self.direction == -1:
            sprite = pygame.transform.flip(sprite, True, False)

        win.blit(sprite, (self.rect.x - offset_x, self.rect.y))

def spawn_avion(objects, level):
    direction = random.choice([1,-1])
    spawn_x = -1500 if direction == 1 else 3500

    # Vitesse grandement augmentée pour parcourir toute la map et bien répartir
    if level == 0:
        speed = random.randint(2, 4)
    elif level == 1:
        speed = random.randint(4, 7)
    elif level == 2:
        speed = random.randint(7, 12)
    else:
        speed = random.randint(10, 16)

    # On fait varier la hauteur Y (entre 0 et 150) pour que les avions ne se superposent pas
    spawn_y = random.randint(0, 150)

    avion = Avion(spawn_x, spawn_y, direction, speed=speed, level=level)
    objects.append(avion)


class Bridge(Object):
    """Gère l'affichage et la collision du pont."""

    def __init__(self, x, y, width, bottom_img, top_img):
        super().__init__(x, y, width, bottom_img.get_height(), "bridge")
        self.bottom_img = bottom_img
        self.top_img = top_img
        # Zone de collision (épaisseur de 20px pour marcher)
        self.rect = pygame.Rect(x, y, width, 20)

    def draw(self, win, offset_x):
        win.blit(self.bottom_img, (self.rect.x - offset_x, self.rect.y))
        # Rambarde posée sur le pont (soustraction de la hauteur)
        win.blit(self.top_img, (self.rect.x - offset_x, self.rect.y - self.top_img.get_height() + 3))


class ParallaxBackground:

    def __init__(self, win):
        self.window = win
        self.width = win.get_width()
        self.y_offset = -70

        self.layers = [
            {"img": pygame.image.load(join("assets", "Background", "sky.png")).convert_alpha(), "speed": 0.1},
            {"img": pygame.image.load(join("assets", "Background", "houses.png")).convert_alpha(), "speed": 0.4},
            {"img": pygame.image.load(join("assets", "Background", "road.png")).convert_alpha(), "speed": 0.7}
        ]

    def draw(self, offset_x):
        """Dessine les calques de fond en boucle infinie."""
        for layer in self.layers:
            rel_x = (offset_x * layer["speed"]) % self.width
            self.window.blit(layer["img"], (-rel_x, self.y_offset))

            if rel_x > 0:
                self.window.blit(layer["img"], (self.width - rel_x, self.y_offset))
            else:
                self.window.blit(layer["img"], (-self.width - rel_x, self.y_offset))


class Water(Object):
    ANIMATION_DELAY = 10
    SURFACE_COLOR = (116, 163, 59)

    def __init__(self, y, height, speed=1):
        super().__init__(-5000, y, 15000, height, "water")
        path = join("assets", "Other", "water.png")
        sprite_sheet = pygame.image.load(path).convert_alpha()

        self.sprites = []
        for i in range(4):
            surface = pygame.Surface((200, 50), pygame.SRCALPHA)
            surface.blit(sprite_sheet, (0, 0), pygame.Rect(0, i * 50, 200, 50))
            self.sprites.append(surface)

        self.image = self.sprites[0] # <--- CORRECTION : On met le pour prendre la 1ère frame
        self.animation_count = 0
        self.speed = speed
        self.mistakes = 0

    def update(self):
        """Met à jour l'animation de l'écume."""
        self.animation_count += 1
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(self.sprites)
        self.image = self.sprites[sprite_index] # <--- CORRECTION : On met le pour animer

    def draw(self, win, offset_x):
        """Dessine le corps de l'eau (rectangle) et la surface animée (sprites)."""
        pygame.draw.rect(
            win,
            self.SURFACE_COLOR,
            (self.rect.x - offset_x, self.rect.y + 50, self.rect.width, self.rect.height + 800)
        )

        sprite_w = self.image.get_width()
        for x in range(0, self.rect.width, sprite_w):
            win.blit(self.image, (self.rect.x + x - offset_x, self.rect.y))

    def up(self):
        """Fait monter le niveau de l'eau de façon non-linéaire."""
        self.mistakes += 1

        # 3 premières erreurs : montée lente (environ 30 pixels par erreur)
        if self.mistakes <= 3:
            self.rect.y -= 5

        # Erreurs suivantes : montée rapide (environ 65 pixels par erreur)
        else:
            self.rect.y -= 30


class Platform(Object):
    """Plateforme basique."""

    def __init__(self, x, y):
        width = 120
        height = 30
        super().__init__(x, y, width, height, "platform")

        img = pygame.image.load(join("assets", "Terrain", "plateform.png")).convert_alpha()
        self.image = pygame.transform.scale(img, (width, height))
        self.rect = pygame.Rect(x, y, width, height)


# =====================================================================
# MENUS ET INTERFACES
# =====================================================================

def main_menu(window):
    clock = pygame.time.Clock()
    parallax_bg = ParallaxBackground(window)

    # --- CHARGEMENT DES BLOCS POUR LE SOL ---
    block_size = 96
    grass_img = get_block(block_size, block_size, "dirtGrassBlock.png")
    dirt_img = get_block(block_size, block_size, "dirtBlock.png")

    # --- BOUTONS ---
    # On centre les boutons horizontalement (WIDTH // 2)
    # Le bouton Jouer est un peu plus haut, le bouton Quitter en dessous
    play_btn = Button(WIDTH // 2 - 75, HEIGHT // 2 - 60, "bouttonJouer.png")
    quit_btn = Button(WIDTH // 2 - 75, HEIGHT // 2 + 70, "bouttonQuitter.png")

    # --- LE JOUEUR (Visuel) ---
    menu_player = Player(WIDTH // 2 + 200, HEIGHT // 2 - 50, 60, 96)
    menu_player.direction = "right"

    menu_scroll = 0
    run_menu = True

    while run_menu:
        clock.tick(FPS)
        menu_scroll += 2

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        # 1. Dessin du Parallax
        parallax_bg.draw(menu_scroll)

        # 2. Dessin du SOL
        for i in range(-1, (WIDTH // block_size) + 2):
            x_pos = (i * block_size) - ((menu_scroll * 0.7) % block_size)
            window.blit(grass_img, (x_pos, HEIGHT - block_size * 2))
            window.blit(dirt_img, (x_pos, HEIGHT - block_size))

        # 3. Animation du Joueur
        menu_player.x_vel = 0
        menu_player.update_sprite()
        window.blit(menu_player.sprite, (menu_player.hitbox.x - menu_player.sprite_offset_x,
                                         menu_player.hitbox.y - menu_player.sprite_offset_y))

        if play_btn.draw(window):
            run_menu = False

        if quit_btn.draw(window):
            pygame.quit()
            exit()

        pygame.display.update()


def draw_pause_menu(window):
    """Affiche l'overlay de pause."""
    font = pygame.font.SysFont("arial", 80)
    text = font.render("PAUSE", True, (255, 255, 255))
    window.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 3))

    font_small = pygame.font.SysFont("arial", 40)
    text2 = font_small.render("Appuie sur Echap pour reprendre", True, (200, 200, 200))
    window.blit(text2, (WIDTH // 2 - text2.get_width() // 2, HEIGHT // 2))

    # À décommenter une fois les boutons ajoutés
    # resume_btn.draw(window)
    # quit_btn.draw(window)

    pygame.display.update()


def show_level_transition(window, level):
    """Affiche l'écran de transition et attend l'appui sur Espace."""
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
        titre = "BOSS FINAL"
        sous_titre = "Préparez-vous à l'affrontement !"
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

    # Indicateur pour lancer le jeu
    font_espace = pygame.font.SysFont('Arial', 35, italic=True)
    t3 = font_espace.render("Appuyez sur ESPACE pour commencer...", True, (255, 255, 150))
    window.blit(t3, t3.get_rect(center=(WIDTH // 2, HEIGHT - 100)))

    pygame.display.update()

    # Boucle d'attente
    attente = True
    while attente:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    attente = False


def game_over_screen(window, message="VOUS ÊTES MORT"):
    """Affiche l'écran de fin de partie avec le choix de rejouer et la cause de la mort."""
    clock = pygame.time.Clock()

    # On adapte la police et la couleur selon si c'est un game over classique ou par l'eau
    if message == "VOUS ÊTES MORT":
        font_titre = pygame.font.SysFont('Arial', 100, bold=True)
        couleur_titre = (255, 50, 50)
    else:
        font_titre = pygame.font.SysFont('Arial', 70, bold=True)  # Plus petit car la phrase est longue
        couleur_titre = (100, 200, 255)  # Couleur bleutée pour l'eau

    font_texte = pygame.font.SysFont('Arial', 40)

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    window.blit(overlay, (0, 0))

    titre = font_titre.render(message, True, couleur_titre)
    window.blit(titre, titre.get_rect(center=(WIDTH // 2, HEIGHT // 3)))

    instructions = font_texte.render("ESPACE pour rejouer  |  ECHAP pour quitter", True, (255, 255, 255))
    window.blit(instructions, instructions.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))

    pygame.display.update()

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: return True
                if event.key == pygame.K_ESCAPE: return False



def main(window, start_level=0):
    clock = pygame.time.Clock()
    current_level = start_level
    total_recycled = 0

    level_goals = {0: 6, 1: 10, 2: 15, 3: 20}

    level_times = {0: 150, 1: 90, 2: 100, 3: 120}
    frames_left = level_times.get(current_level, 60) * FPS

    show_level_transition(window, current_level)

    parallax_bg = ParallaxBackground(window)
    block_size = 96

    # Initialisation des éléments du pont
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
             range(-10, 23) if i not in [3,4,5,9,10,11,12,13,14,15,16,17,18,19,20]]
    floor += [Block(i * block_size, HEIGHT - block_size * 4, block_size, "dirtGrassBlock.png") for i in
             range(14,31) if i not in [16,17,18,21,22,23,24]]
    floor += [Block(i * block_size, HEIGHT -block_size, block_size, "dirtGrassBlock.png") for i in
              range(9, 25) if i not in [14,15,16,17,18,19,20,21,22]]
    floor += [Block(6 * block_size, HEIGHT - block_size*6, block_size, "dirtGrassBlock.png")]

    bottom_floor = [Block(i * block_size, HEIGHT - block_size, block_size, "dirtBlock.png") for i in
                    range(-10, 31) if i not in [3,4,5,9,10,11,12,13,16,17,18,23,24]]
    bottom_floor += [Block(i * block_size, HEIGHT - block_size * 2, block_size, "dirtBlock.png") for i in
                    range(14, 31) if i not in [16,17,18,21,22,23,24]]
    bottom_floor += [Block(i * block_size, HEIGHT - block_size * 3, block_size, "dirtBlock.png") for i in
                     range(14, 31) if i not in [16, 17, 18, 21, 22,23,24]]
    bottom_floor += [Block(6 * block_size, HEIGHT - block_size * 5, block_size, "dirtBlock.png")]
    bottom_floor += [Block(i * block_size, HEIGHT - block_size * 7, block_size, "dirtBlock.png") for i in
                     range(14, 16)]
    bottom_floor += [Block(i * block_size, HEIGHT - block_size * 8, block_size, "dirtBlock.png") for i in
                     range(14, 16)]
    bottom_floor += [Block(i * block_size, HEIGHT - block_size * 9, block_size, "dirtBlock.png") for i in
                     range(14, 16)]
    left_wall = [
        Block(-960, i * block_size, block_size, "dirtBlock.png") if i != 0 else Block(-960, i * block_size, block_size,
                                                                                      "dirtGrassBlock.png") for i in
        range(-5, 9)]
    left_left__wall = [
        Block(-1056, j * block_size, block_size, "dirtBlock.png") if j != 0 else Block(-1056, j * block_size,
                                                                                       block_size, "dirtGrassBlock.png")
        for j in range(-5, 9)]
    left_left_left_wall = [
        Block(-1152, i * block_size, block_size, "dirtBlock.png") if i != 0 else Block(-1152, i * block_size,
                                                                                       block_size, "dirtGrassBlock.png")
        for i in range(-5, 9)]

    plateform1 = [Platform(100 + i * 120, 150) for i in range(2)]

    plateform2 = [Platform(96 * i - 60, 96 * 4 + 2) for i in range(7, 10)]

    plateform3 = [Platform(96 * i - 60, 96 * 2 + 2) for i in range(19, 23)]

    right_wall = [
        Block(31 * block_size, i * block_size, block_size, "dirtBlock.png") if i != 0
        else Block(31 * block_size, i * block_size, block_size, "dirtGrassBlock.png")
        for i in range(-5, 9)
    ]
    right_right_wall = [
        Block(32 * block_size, i * block_size, block_size, "dirtBlock.png") if i != 0
        else Block(32 * block_size, i * block_size, block_size, "dirtGrassBlock.png")
        for i in range(-5, 9)
    ]
    right_right_right_wall = [
        Block(33 * block_size, i * block_size, block_size, "dirtBlock.png") if i != 0
        else Block(33 * block_size, i * block_size, block_size, "dirtGrassBlock.png")
        for i in range(-5, 9)
    ]

    objects = [
        *plateform1,
        *plateform2,
        *plateform3,
        bridge1,
        bridge2,
        *bottom_floor,
        *floor,
        *left_wall,
        *left_left__wall,
        *left_left_left_wall,
        *right_wall,
        *right_right_wall,
        *right_right_right_wall,

        TrashBin(-800, HEIGHT - 175 - 96, "green"),
        TrashBin(-640, HEIGHT - 175 - 96, "yellow"),
        TrashBin(-480, HEIGHT - 175 - 96, "black"),

        ShadowBlock(-180, 0, 80, HEIGHT),
        Plot(-150, 536, 48, 72),

        Waste(block_size * 3, 0, "glassBottle.png", 1),
        Waste(block_size * 7, HEIGHT - block_size * 6 - 75, "cardboard.png", 2.7),
        Waste(block_size * 12, HEIGHT - block_size * 4 - 75, "bottle.png", 2),
        Waste(block_size * 15, HEIGHT - block_size * 2 - 75, "trashBag.png", 3),
        Waste(block_size * 20, HEIGHT - block_size * 3 - 75, "tire.png", 3),
        Waste(block_size * 25, HEIGHT - block_size * 2 - 75, "glassBottle.png", 1),
    ]

    water = Water(HEIGHT - 74, 200, 0.1)
    objects.append(water)


    # Paramètres de caméra
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
        handle_vertical_collision(player, objects)

        # Règle de tri des déchets
        WASTE_TYPES = {
            "glassBottle.png": "green",
            "cardboard.png": "yellow",
            "bottle.png": "yellow",
            "tire.png": "black",
            "trashBag.png": "black"
        }

        # Parcours et mise à jour des objets
        for obj in objects[:]:

            # --- GESTION DE L'EAU (DÉGÂTS) ---
            if isinstance(obj, Water):
                obj.update()
                # On meurt INSTANTANÉMENT si on touche l'eau
                if player.hitbox.colliderect(obj.rect):
                    player.health = 0
                    death_message = "Vous avez noyé votre planète..."

            # --- GESTION DE L'AVION ---
            if isinstance(obj, Avion):
                obj.update(objects)
                # Destruction si l'avion sort de l'écran
                if (obj.direction == 1 and obj.rect.left > 3500) or (obj.direction == -1 and obj.rect.right < -1500):
                    if obj in objects: objects.remove(obj)
                    continue

                if obj.rect.colliderect(player.hitbox):
                    # CORRECTION BUG 1 : L'avion ne disparaît plus et fait très mal (1 cœur plein = 2 PV)
                    if not player.hit:
                        player.health -= 2
                        player.make_hit()

            # --- GESTION DES DÉCHETS (RECYCLAGE ET ERREURS) ---
            if isinstance(obj, Waste):
                obj.update(objects)

                # Le déchet disparaît s'il touche l'eau (SAUF pendant le tuto)
                if obj.rect.colliderect(water.rect) and current_level > 0:
                    if obj in objects: objects.remove(obj)
                    continue

                # Dégât si le déchet tombe sur le joueur (SAUF pendant le tuto)
                if obj.rect.colliderect(player.hitbox) and obj.y_vel > 0 and not obj.on_ground:
                    if current_level > 0:
                        if not player.hit:
                            player.health -= 1
                            player.make_hit()
                        if obj in objects: objects.remove(obj)
                        continue

                # --- TIR TROP FAIBLE (TUTO UNIQUEMENT) ---
                # Si on est au tuto, que le déchet touche le sol, et qu'il est avant ou sur le plot (X <= 400)
                if current_level == 0 and obj.on_ground and obj.rect.x <= -130:
                    player.collect_trash(obj, objects)  # On remet l'objet dans l'inventaire
                    throw_harder_timer = 120  # On lance l'affichage du message (2 secondes)
                    continue

                for other in objects:
                    if isinstance(other, TrashBin):
                        if obj.rect.colliderect(other.hitbox):
                            correct_color = WASTE_TYPES.get(obj.filename)
                            if correct_color == other.color:
                                # Bon tri
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

                                    player.inventory.clear()
                                    player.trash_collected = 0

                                    for o in objects[:]:
                                        if isinstance(o, Waste):
                                            objects.remove(o)
                            else:
                                if current_level == 0:
                                    # TUTO : Afficher l'alerte pendant 2 secondes
                                    wrong_bin_timer = 120

                                    # On remet directement l'objet dans l'inventaire du joueur
                                    player.collect_trash(obj, objects)
                                else:
                                    # NORMAL : Mauvais tri = l'eau monte !
                                    water.up()  # <--- On retire le '80' ici
                                    if obj in objects:
                                        objects.remove(obj)
                            break

        # --- SPAWN DES AVIONS (AUGMENTATION PAR NIVEAU) ---
        if current_level > 0:
            avions_actifs = sum(1 for o in objects if isinstance(o, Avion))

            # Limites d'avions simultanés par niveau
            max_planes = {1: 2, 2: 5, 3: 10}.get(current_level, 0)

            # Plus le niveau est haut, plus la chance de spawn par frame est élevée
            spawn_chance = {1: 100, 2: 50, 3: 20}.get(current_level, 999)

            if avions_actifs < max_planes:
                if random.randint(1, spawn_chance) == 1:
                    spawn_avion(objects, current_level)

        # --- CONDITION DE DÉFAITE ---
        if player.health <= 0:
            rejouer = game_over_screen(window, message=death_message)
            return rejouer

        # --- GESTION DE LA CAMÉRA ---
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

        if not camera_shifted:
            if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                    (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
                offset_x += player.x_vel
                scroll -= player.x_vel

            if abs(scroll) > WIDTH:
                scroll = 0

        # --- GESTION DES MESSAGES DU TUTO ---
        if wrong_bin_timer > 0:
            wrong_bin_timer -= 1
        if throw_harder_timer > 0:
            throw_harder_timer -= 1

        # On récupère l'objectif du niveau actuel
        level_goal = level_goals.get(current_level, 999)

        # Dessin global (avec les nouvelles infos du compteur)
        draw(window, parallax_bg, player, objects, offset_x, frames_left, wrong_bin_timer, throw_harder_timer,
             total_recycled, level_goal)

    pygame.quit()
    quit()


if __name__ == "__main__":
    jeu_en_cours = True

    while jeu_en_cours:
        main_menu(window)

        # On lance toujours au niveau 0 (Tuto)
        vouloir_rejouer = main(window, start_level=2)

        # Si le joueur ne veut pas rejouer (il a fait Echap), on quitte
        if not vouloir_rejouer:
            jeu_en_cours = False

    pygame.quit()
    quit()