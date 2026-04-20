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

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
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
    SPRITES = load_sprites_from_folder("MainCharacters", "MaleChar", 3, True)
    ANIMATION_DELAY = 4

    def __init__(self, x, y, width, height):
        super().__init__()
        self.hitbox = pygame.Rect(x, y, width, height - 2)
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


# =====================================================================
# BOSS
# =====================================================================

class Boss:
    """Le boss final : PDG de la pollution."""

    ANIMATION_DELAY = 6
    MAX_HP = 10
    STOP_DISTANCE = 350   # Distance à laquelle il s'arrête pour tirer
    WALK_SPEED = 2
    WALK_SPEED_RAGE = 4

    def __init__(self, x, y):
        self.sprites = {}
        boss_path = join("assets", "MainCharacters", "Boss")

        for subfolder in ["player-stand", "player-run", "player-hurt", "player-shoot"]:
            folder_path = join(boss_path, subfolder)
            files = sorted([f for f in os.listdir(folder_path) if f.endswith(".png")])
            frames = []
            for f in files:
                img = pygame.image.load(join(folder_path, f)).convert_alpha()
                img = pygame.transform.scale_by(img, 3)
                frames.append(img)

            # Version gauche et droite
            self.sprites[subfolder + "_left"] = [pygame.transform.flip(f, True, False) for f in frames]
            self.sprites[subfolder + "_right"] = frames

        sample = self.sprites["player-stand_left"][0]
        self.width = sample.get_width() // 2
        self.height = sample.get_height()
        self.hitbox = pygame.Rect(x, y, self.width, self.height)

        self.hp = self.MAX_HP
        self.direction = "left"
        self.animation_count = 0
        self.current_anim = "player-stand"

        # IA
        self.state = "walk"
        self.hurt_timer = 0
        self.shoot_timer = 0
        self.shoot_anim_timer = 0  # NOUVEAU : Pour gérer la durée de l'animation de tir
        self.shoot_cooldown = 120
        self.alive = True

        self.sprite = self.sprites["player-stand_left"][0]

    @property
    def is_rage(self):
        return self.hp <= self.MAX_HP // 2

    def take_hit(self):
        """Appelé quand un déchet touche le boss."""
        if self.state == "hurt":
            return  # Invincible pendant l'animation hurt
        self.hp -= 1
        self.state = "hurt"
        self.hurt_timer = 40
        self.animation_count = 0
        if self.hp <= 0:
            self.alive = False

    def update(self, player, objects):
        # --- TIMER HURT ---
        if self.state == "hurt":
            self.hurt_timer -= 1
            if self.hurt_timer <= 0:
                self.state = "walk"
            self._animate("player-hurt")
            return

        # --- DIRECTION ---
        if player.hitbox.centerx < self.hitbox.centerx:
            self.direction = "left"
        else:
            self.direction = "right"

        dist = abs(player.hitbox.centerx - self.hitbox.centerx)
        speed = self.WALK_SPEED_RAGE if self.is_rage else self.WALK_SPEED

        # --- COOLDOWN ET ANIMATION DE TIR ---
        cooldown = 60 if self.is_rage else self.shoot_cooldown
        self.shoot_timer -= 1

        # Si l'animation de tir est en cours, il s'arrête et tire
        if self.shoot_anim_timer > 0:
            self.shoot_anim_timer -= 1
            self._animate("player-shoot")
        else:
            if dist > self.STOP_DISTANCE:
                # Avancer vers le joueur
                self.state = "walk"
                if player.hitbox.centerx < self.hitbox.centerx:
                    self.hitbox.x -= speed
                else:
                    self.hitbox.x += speed
                self._animate("player-run")
            else:
                # À portée : Prêt à tirer
                self.state = "stand"
                self._animate("player-stand")

                # Déclenchement du tir
                if self.shoot_timer <= 0:
                    self.shoot_anim_timer = 25  # Fait durer l'animation de tir pendant 25 frames
                    self._shoot(player, objects)  # Envoie les 'objects' pour faire spawner le déchet
                    self.shoot_timer = cooldown

        # --- Gravité basique pour que le boss reste au sol ---
        self.hitbox.y += 8
        for obj in objects:
            if isinstance(obj, Block) and self.hitbox.colliderect(obj.rect):
                self.hitbox.bottom = obj.rect.top
                break

    def _shoot(self, player, objects):
        spawn_x = self.hitbox.centerx
        spawn_y = self.hitbox.centery - 20

        # On calcule la distance horizontale (dx) ET verticale (dy) vers le joueur
        dx = player.hitbox.centerx - spawn_x
        dy = player.hitbox.centery - spawn_y

        # PARAMÈTRES PAR DÉFAUT (Normal)
        nb_dechets = 1
        flight_time = 45.0  # Temps de vol en frames (plus c'est grand, plus c'est lent et en cloche)
        spread = 1.0  # Éparpillement

        # CHANGEMENT DE PATTERN SELON LES PV
        if self.hp <= 3:
            # PHASE 3 : Panique (Shotgun)
            nb_dechets = 4
            flight_time = 32.0  # Rapide
            spread = 4.0

        elif self.hp <= 5:
            # PHASE 2 : Rage (Sniper / Tir très rapide et tendu)
            nb_dechets = 2
            flight_time = 22.0  # Très rapide !
            spread = 1.5

        elif self.hp <= 8:
            # PHASE 1.5 : S'énerve doucement
            nb_dechets = 2
            flight_time = 40.0
            spread = 1.5

        # --- CALCUL BALISTIQUE INTELLIGENT ---
        # On calcule les vitesses exactes (X et Y) pour que le déchet retombe PILE sur le joueur
        gravity = Waste.GRAVITY  # (0.8 dans ta classe Waste)

        base_vx = dx / flight_time
        base_vy = (dy / flight_time) - (0.5 * gravity * flight_time)

        # On limite les vitesses extrêmes pour éviter les bugs si le joueur est collé au boss
        base_vx = max(min(base_vx, 25), -25)
        base_vy = max(min(base_vy, 10), -35)  # Max -35 vers le haut

        # CRÉATION DES DÉCHETS
        for _ in range(nb_dechets):
            r_file = random.choice(["tire.png", "glassBottle.png", "cardboard.png", "bottle.png", "trashBag.png"])
            scales = {"tire.png": 3, "glassBottle.png": 1, "cardboard.png": 2.7, "bottle.png": 2, "trashBag.png": 3}

            # On applique l'éparpillement (spread)
            vx_final = base_vx + random.uniform(-spread, spread)
            vy_final = base_vy + random.uniform(-spread, spread / 2)

            trash = Waste(spawn_x, spawn_y, r_file, scale=scales.get(r_file, 3), vel_x=vx_final, vel_y=vy_final)
            objects.append(trash)

    def _animate(self, anim_name):
        # Cherche la clé qui contient anim_name et la bonne direction
        key = next((k for k in self.sprites if anim_name in k and k.endswith("_" + self.direction)), None)
        if key is None:
            key = next((k for k in self.sprites if anim_name in k and k.endswith("_left")), None)
        sprites = self.sprites[key]
        idx = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[idx]
        self.animation_count += 1

    def draw(self, win, offset_x):
        # Sprite
        draw_x = self.hitbox.x - offset_x - self.hitbox.width // 2
        draw_y = self.hitbox.y + 50
        win.blit(self.sprite, (draw_x, draw_y))
        # Barre de vie
        self._draw_health_bar(win)

    def _draw_health_bar(self, win):
        bar_width = 300
        bar_height = 22
        bar_x = WIDTH // 2 - bar_width // 2
        bar_y = 140

        # Fond
        pygame.draw.rect(win, (60, 0, 0), (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4), border_radius=6)
        pygame.draw.rect(win, (30, 30, 30), (bar_x, bar_y, bar_width, bar_height), border_radius=5)

        # Barre HP
        ratio = max(0, self.hp / self.MAX_HP)
        color = (220, 50, 50) if not self.is_rage else (255, 120, 0)
        filled_w = int(bar_width * ratio)
        if filled_w > 0:
            pygame.draw.rect(win, color, (bar_x, bar_y, filled_w, bar_height), border_radius=5)

        # Contour
        pygame.draw.rect(win, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 2, border_radius=5)

        # Texte
        font = pygame.font.SysFont("arial", 20, bold=True)
        label = font.render(f"PDG DE LA POLLUTION  {self.hp} / {self.MAX_HP}", True, (255, 255, 255))
        win.blit(label, (bar_x + bar_width // 2 - label.get_width() // 2, bar_y + 2))


# =====================================================================
# OBJETS
# =====================================================================

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
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
        self.is_launched = False

    def update(self, objects, water=None):
        if not self.on_ground:
            self.y_vel += self.GRAVITY

        if water and self.rect.bottom > water.rect.y:
            self.x_vel *= 0.95
            self.y_vel *= 0.90
            vague = math.sin(pygame.time.get_ticks() / 200.0) * 5
            ligne_flottaison = water.rect.y + (self.rect.height * 0.7) + vague
            if self.rect.bottom > ligne_flottaison:
                self.y_vel -= 1.5

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

            spawn_x = player.hitbox.centerx - 15
            spawn_y = player.hitbox.top - 40

            if len(player.inventory) > 0:
                last_item_file, scale = player.inventory.pop()

                launched_item = Waste(spawn_x, spawn_y, last_item_file, scale, vel_x=v_x, vel_y=v_y)
                launched_item.is_launched = True
                objects.append(launched_item)

                player.trash_collected -= 1
                player.throw_cooldown = 30


class Avion(Object):
    ANIMATION_DELAY = 15

    def __init__(self, x, y, direction=1, speed=3, level=0):
        path = join("assets", "Items", "Plane", "planeSprite.png")
        sprite_sheet = pygame.image.load(path).convert_alpha()
        self.sprites = []
        frame_width = 350
        frame_height = 150

        for i in range(7):
            surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
            surface.blit(sprite_sheet, (0, 0), rect)
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
        if self.level == 1:
            self.drop_timer = random.randint(120, 200)
        elif self.level == 2:
            self.drop_timer = random.randint(50, 90)
        elif self.level >= 3:
            self.drop_timer = random.randint(15, 45)
        else:
            self.drop_timer = 9999

    def move(self):
        self.rect.x += self.speed * self.direction

    def update(self, objects, total_recycled=0, level_goal=999, is_rush_hour=False, player_trash_collected=0):
        self.move()
        self.animation_count += 1
        self.drop_timer -= 1

        if self.drop_timer <= 0:
            self.drop_waste(objects, total_recycled, level_goal, player_trash_collected)
            if is_rush_hour:
                self.drop_timer = random.randint(15, 30)
            else:
                self.drop_timer = random.randint(60, 120)

    def drop_waste(self, objects, total_recycled, level_goal, player_trash_collected):
        trash_x = self.rect.right - 20 if self.direction == -1 else self.rect.left + 20
        trash_y = self.rect.bottom - 15

        zone = 0
        if 100 <= trash_x <= 700: zone = 1
        elif 700 < trash_x <= 1300: zone = 2
        elif 1580 <= trash_x <= 2080: zone = 3
        elif 2080 < trash_x <= 2570: zone = 4

        if zone == 0:
            return

        marges_par_niveau = {1: 3, 2: 4, 3: 5}
        marge = marges_par_niveau.get(self.level, 0)
        wastes_on_map = [o for o in objects if isinstance(o, Waste) and not o.collected]

        if len(wastes_on_map) >= 6:
            return

        total_existing = len(wastes_on_map) + player_trash_collected + total_recycled
        if total_existing >= (level_goal + marge):
            return

        quota_zone = math.ceil((level_goal + marge) / 4)
        wastes_in_zone = 0
        for o in wastes_on_map:
            ox = o.rect.x
            if zone == 1 and 100 <= ox <= 700: wastes_in_zone += 1
            elif zone == 2 and 700 < ox <= 1300: wastes_in_zone += 1
            elif zone == 3 and 1580 <= ox <= 2080: wastes_in_zone += 1
            elif zone == 4 and 2080 < ox <= 2570: wastes_in_zone += 1

        if wastes_in_zone >= quota_zone:
            return

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
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(self.sprites)
        sprite = self.sprites[sprite_index]
        if self.direction == -1:
            sprite = pygame.transform.flip(sprite, True, False)
        win.blit(sprite, (self.rect.x - offset_x, self.rect.y))


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


class Bridge(Object):
    def __init__(self, x, y, width, bottom_img, top_img):
        super().__init__(x, y, width, bottom_img.get_height(), "bridge")
        self.bottom_img = bottom_img
        self.top_img = top_img
        self.rect = pygame.Rect(x, y, width, 20)

    def draw(self, win, offset_x):
        win.blit(self.bottom_img, (self.rect.x - offset_x, self.rect.y))
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

        self.image = self.sprites[0]
        self.animation_count = 0
        self.speed = speed
        self.mistakes = 0

    def update(self):
        self.animation_count += 1
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(self.sprites)
        self.image = self.sprites[sprite_index]

    def draw(self, win, offset_x):
        pygame.draw.rect(win, self.SURFACE_COLOR,
                         (self.rect.x - offset_x, self.rect.y + 50, self.rect.width, self.rect.height + 800))
        sprite_w = self.image.get_width()
        for x in range(0, self.rect.width, sprite_w):
            win.blit(self.image, (self.rect.x + x - offset_x, self.rect.y))

    def up(self):
        self.mistakes += 1
        if self.mistakes <= 3:
            self.rect.y -= 4
        else:
            self.rect.y -= 30


class Platform(Object):
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

    block_size = 96
    grass_img = get_block(block_size, block_size, "dirtGrassBlock.png")
    dirt_img = get_block(block_size, block_size, "dirtBlock.png")

    play_btn = Button(WIDTH // 2 - 75, HEIGHT // 2 - 60, "bouttonJouer.png")
    quit_btn = Button(WIDTH // 2 - 75, HEIGHT // 2 + 70, "bouttonQuitter.png")

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

        parallax_bg.draw(menu_scroll)

        for i in range(-1, (WIDTH // block_size) + 2):
            x_pos = (i * block_size) - ((menu_scroll * 0.7) % block_size)
            window.blit(grass_img, (x_pos, HEIGHT - block_size * 2))
            window.blit(dirt_img, (x_pos, HEIGHT - block_size))

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
    font = pygame.font.SysFont("arial", 80)
    text = font.render("PAUSE", True, (255, 255, 255))
    window.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 3))

    font_small = pygame.font.SysFont("arial", 40)
    text2 = font_small.render("Appuie sur Echap pour reprendre", True, (200, 200, 200))
    window.blit(text2, (WIDTH // 2 - text2.get_width() // 2, HEIGHT // 2))

    pygame.display.update()


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


def game_over_screen(window, message="VOUS ÊTES MORT"):
    clock = pygame.time.Clock()

    if message == "VOUS ÊTES MORT":
        font_titre = pygame.font.SysFont('Arial', 100, bold=True)
        couleur_titre = (255, 50, 50)
    else:
        font_titre = pygame.font.SysFont('Arial', 70, bold=True)
        couleur_titre = (100, 200, 255)

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


def victory_screen(window):
    """Écran de victoire après avoir vaincu le boss."""
    clock = pygame.time.Clock()

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 20, 0, 220))
    window.blit(overlay, (0, 0))

    font_titre = pygame.font.SysFont('Arial', 80, bold=True)
    font_sous = pygame.font.SysFont('Arial', 40)
    font_btn = pygame.font.SysFont('Arial', 35)

    titre = font_titre.render("VOUS AVEZ SAUVÉ LA PLANÈTE !", True, (100, 255, 100))
    sous = font_sous.render("Le PDG de la pollution a été vaincu grâce à vous.", True, (200, 255, 200))
    btn = font_btn.render("ESPACE pour rejouer  |  ECHAP pour quitter", True, (255, 255, 255))

    window.blit(titre, titre.get_rect(center=(WIDTH // 2, HEIGHT // 3)))
    window.blit(sous, sous.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
    window.blit(btn, btn.get_rect(center=(WIDTH // 2, HEIGHT * 2 // 3)))

    pygame.display.update()

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: return True
                if event.key == pygame.K_ESCAPE: return False


# =====================================================================
# BOUCLE PRINCIPALE
# =====================================================================

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
              range(14, 27) if i not in [16, 17, 18, 21, 22, 23, 24]]
    floor += [Block(i * block_size, HEIGHT - block_size, block_size, "dirtGrassBlock.png") for i in
              range(9, 25) if i not in [14, 15, 16, 17, 18, 19, 20, 21, 22]]
    floor += [Block(6 * block_size, HEIGHT - block_size * 6, block_size, "dirtGrassBlock.png")]

    bottom_floor = [Block(i * block_size, HEIGHT - block_size, block_size, "dirtBlock.png") for i in
                    range(-10, 27) if i not in [3, 4, 5, 9, 10, 11, 12, 13, 16, 17, 18, 23, 24]]
    bottom_floor += [Block(i * block_size, HEIGHT - block_size * 2, block_size, "dirtBlock.png") for i in
                     range(14, 27) if i not in [16, 17, 18, 21, 22, 23, 24]]
    bottom_floor += [Block(i * block_size, HEIGHT - block_size * 3, block_size, "dirtBlock.png") for i in
                     range(14, 27) if i not in [16, 17, 18, 21, 22, 23, 24]]
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

        if player.hitbox.colliderect(water.rect):
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
                    if obj.rect.colliderect(player.hitbox) and not obj.on_ground and not obj.is_launched:
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
                    if player.hitbox.colliderect(obj.rect):
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

                    if obj.rect.colliderect(player.hitbox) and obj.y_vel > 0 and not obj.on_ground:
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
                                        water.up()
                                        if obj in objects:
                                            objects.remove(obj)
                                break

            # --- SPAWN DES AVIONS ---
            if current_level > 0:
                avions_actifs = sum(1 for o in objects if isinstance(o, Avion))
                max_planes = {1: 2, 2: 4, 3: 6, 4: 6}.get(current_level, 0)
                spawn_chance = {1: 100, 2: 50, 3: 20, 4: 20}.get(current_level, 999)

                if avions_actifs < max_planes:
                    if random.randint(1, spawn_chance) == 1:
                        spawn_avion(objects, current_level)

        # --- CONDITION DE DÉFAITE ---
        if player.health <= 0:
            rejouer = game_over_screen(window, message=death_message)
            return rejouer

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
                              else Block(-3 * block_size, i * block_size, block_size, "dirtGrassBlock.png") for i in
                              range(-5, 9)]
            boss_right_wall = [Block(20 * block_size, i * block_size, block_size, "dirtBlock.png") if i != 0
                                else Block(20 * block_size, i * block_size, block_size, "dirtGrassBlock.png") for i in range(-5, 9)]
            boss_right_right_wall = [Block(21 * block_size, i * block_size, block_size, "dirtBlock.png") if i != 0
                               else Block(20 * block_size, i * block_size, block_size, "dirtGrassBlock.png") for i in
                               range(-5, 9)]

            objects.extend(boss_floor)
            objects.extend(boss_bottom)
            objects.extend(boss_plateforms)
            objects.extend(boss_left_wall)
            objects.extend(boss_right_wall)
            objects.extend(boss_left_left_wall)
            objects.extend(boss_right_right_wall)

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

        # --- GESTION DE LA CAMÉRA ---
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