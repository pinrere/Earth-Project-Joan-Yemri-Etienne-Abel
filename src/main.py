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

def draw(window, bg_parallax, player, objects, offset_x):
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

            if m_x > player_screen_x:
                spawn_x = player.hitbox.right + 10
            else:
                spawn_x = player.hitbox.left - 60
            spawn_y = player.hitbox.top + 10

            if len(player.inventory) > 0:
                last_item_file,scale = player.inventory.pop()

                launched_item = Waste(spawn_x, spawn_y, last_item_file, scale,vel_x=v_x, vel_y=v_y)
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
        if self.level == 0:
            self.drop_timer = random.randint(150, 220)
        elif self.level == 1:
            self.drop_timer = random.randint(100, 160)
        else:
            self.drop_timer = random.randint(60, 110)

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
            if -140 <= self.rect.x <= 3000:
                self.drop_waste(objects)
            self.reset_drop_timer()

    def drop_waste(self, objects):
        """Génère un déchet qui tombe de l'arrière de l'avion."""
        trash_x = self.rect.right - 20 if self.direction == -1 else self.rect.left + 20
        trash_y = self.rect.bottom - 15

        random_file = random.choice(["tire.png", "bottle.png", "glassBottle.png", "trashBag.png", "cardboard.png"])
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
    """Fait apparaître un avion avec une direction et vitesse aléatoires."""
    direction = random.choice([-1, 1])
    spawn_x = -1500 if direction == 1 else 3500

    if level == 0:
        speed = random.randint(2, 4)
    elif level == 1:
        speed = random.randint(4, 7)
    else:
        speed = random.randint(6, 9)

    avion = Avion(spawn_x, 0, direction, speed=speed, level=level)
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
        self.y_offset = -96

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

        self.image = self.sprites[0]
        self.animation_count = 0
        self.speed = speed

    def update(self):
        """Met à jour l'animation de l'écume."""
        self.animation_count += 1
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(self.sprites)
        self.image = self.sprites[sprite_index]

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

    def up(self, dy):
        """Fait monter le niveau de l'eau."""
        self.rect.y -= dy * self.speed


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
    """Affiche l'écran de transition entre les niveaux et le tutoriel."""
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

    pygame.display.update()

    # Pause plus longue pour le tutoriel afin de laisser le temps de lire
    pygame.time.delay(4500 if level == 0 else 3500)


def game_over_screen(window):
    """Affiche l'écran de fin de partie avec le choix de rejouer."""
    clock = pygame.time.Clock()
    font_titre = pygame.font.SysFont('Arial', 100, bold=True)
    font_texte = pygame.font.SysFont('Arial', 40)

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    window.blit(overlay, (0, 0))

    titre = font_titre.render("VOUS ÊTES MORT", True, (255, 50, 50))
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


# =====================================================================
# BOUCLE PRINCIPALE DU JEU
# =====================================================================

def main(window, start_level=0):
    clock = pygame.time.Clock()
    current_level = start_level
    total_recycled = 0

    level_goals = {0: 6, 1: 10, 2: 15, 3: 20}
    level_times = {0: 60, 1: 90, 2: 120, 3: 180}
    frames_left = level_times.get(current_level, 60) * FPS

    show_level_transition(window, current_level)

    parallax_bg = ParallaxBackground(window)
    block_size = 96

    # Initialisation des éléments du pont
    img_top = pygame.image.load(join("assets", "Terrain", "topBridge.png")).convert_alpha()
    img_bottom = pygame.image.load(join("assets", "Terrain", "bottomBridge.png")).convert_alpha()
    bridge_width = 308
    bridge_x = 3 * block_size - 10
    bridge_y = HEIGHT - block_size * 2
    bridge = Bridge(bridge_x, bridge_y, bridge_width, img_bottom, img_top)

    player = Player(150, 100, 60, 96)

    # Création du terrain
    floor = [Block(i * block_size, HEIGHT - block_size * 2, block_size, "dirtGrassBlock.png") for i in
             range(-10, WIDTH * 10 // block_size) if i not in [3, 4, 5]]
    bottom_floor = [Block(i * block_size, HEIGHT - block_size, block_size, "dirtBlock.png") for i in
                    range(-10, WIDTH * 10 // block_size) if i not in [3, 4, 5]]
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

    objects = [
        bridge,
        *bottom_floor,
        *floor,
        *left_wall,
        *left_left__wall,
        *left_left_left_wall,

        TrashBin(-800, HEIGHT - 175 - 96, "green"),
        TrashBin(-640, HEIGHT - 175 - 96, "yellow"),
        TrashBin(-480, HEIGHT - 175 - 96, "black"),

        ShadowBlock(-180, 0, 80, HEIGHT),
        Plot(-150, 536, 48, 72),

        Waste(block_size * 10, HEIGHT - block_size * 4 - 75, "glassBottle.png", 1),
        Waste(block_size * 12, HEIGHT - block_size * 4 - 75, "cardboard.png", 2.7),
    ]

    water = Water(HEIGHT - 100, 200, 0.3)
    objects.append(water)

    start_x = 500
    y = HEIGHT - 300
    for i in range(6):
        objects.append(Platform(start_x + i * 120, y))

    # Paramètres de caméra
    offset_x = 0
    scroll_area_width = 200
    scroll = 0
    camera_shifted = False
    saved_offset_x = 0
    saved_scroll = 0

    cpt = 0
    paused = False
    run = True

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

        # Mise à jour de la physique du joueur
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
                if player.hitbox.colliderect(obj.rect):
                    player.water_timer += 1
                    # 1 demi-coeur retiré toutes les 2 secondes (120 frames)
                    if player.water_timer >= FPS * 2:
                        player.health -= 1
                        player.make_hit()
                        player.water_timer = 0
                else:
                    player.water_timer = 0

            # --- GESTION DE L'AVION ---
            if isinstance(obj, Avion):
                obj.update(objects)
                # Destruction si l'avion sort de l'écran
                if (obj.direction == 1 and obj.rect.left > 3500) or (obj.direction == -1 and obj.rect.right < -1500):
                    if obj in objects: objects.remove(obj)
                    continue

                if obj.rect.colliderect(player.hitbox):
                    player.health -= 1
                    if obj in objects: objects.remove(obj)

            # --- GESTION DES DÉCHETS (RECYCLAGE ET ERREURS) ---
            if isinstance(obj, Waste):
                obj.update(objects)

                # Dégât si le déchet tombe sur le joueur
                if obj.rect.colliderect(player.hitbox) and obj.y_vel > 0 and not obj.on_ground:
                    player.health -= 1
                    player.health = max(0, player.health)
                    if obj in objects: objects.remove(obj)
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
                                    show_level_transition(window, current_level)
                            else:
                                # Mauvais tri : l'eau monte !
                                water.up(80)
                                objects.remove(obj)
                            break

        # --- SPAWN DES AVIONS (MAX 2 ACTIFS) ---
        avions_actifs = sum(1 for o in objects if isinstance(o, Avion))
        if avions_actifs < 2:
            spawn_chance = 150 if current_level == 0 else (100 if current_level == 1 else 60)
            if random.randint(1, spawn_chance) == 1 and cpt % 5 == 0:
                spawn_avion(objects, current_level)

        # --- CONDITION DE DÉFAITE ---
        if player.health <= 0:
            rejouer = game_over_screen(window)
            return rejouer

        # --- GESTION DE LA CAMÉRA ---
        # Shift spécial si le joueur recule loin à gauche
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

        # Caméra normale suivant le joueur
        if not camera_shifted:
            if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                    (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
                offset_x += player.x_vel
                scroll -= player.x_vel

            if abs(scroll) > WIDTH:
                scroll = 0

        # Dessin global
        draw(window, parallax_bg, player, objects, offset_x)

    pygame.quit()
    quit()


if __name__ == "__main__":
    jeu_en_cours = True
    niveau_depart = 0  # Lance le Tuto la première fois

    while jeu_en_cours:
        main_menu(window)  # Assure-toi que "window" est définie en amont dans ton code global

        # Le jeu renvoie True si le joueur choisit "Espace" au game over
        vouloir_rejouer = main(window, start_level=niveau_depart)

        if vouloir_rejouer:
            niveau_depart = 1  # S'il recommence, on saute le Tuto !
        else:
            jeu_en_cours = False

    pygame.quit()
    quit()