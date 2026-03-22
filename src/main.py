import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join
from collections import defaultdict
pygame.init()


pygame.display.set_caption("Eco Guardian")


WIDTH, HEIGHT = 1422, 800
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
    images = [f for f in listdir(path) if isfile(join(path, f))] #lire tous les fichiers dans un dossier jcrois

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect) #blit = draw
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size_x, size_y, name):
    # On charge directement ton nouveau fichier extrait
    path = join("assets", "Terrain", name)
    image = pygame.image.load(path).convert_alpha()

    # On redimensionne l'image à la taille voulue pour le jeu
    # (Si block_size est 96, elle restera en 96x96)
    return pygame.transform.scale(image, (size_x, size_y))

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
        self.max_health = 100
        self.health = 100
        self.trash_collected = 0
        self.MAX_TRASH = 3
        # Pour l'affichage des carrés des déchets
        self.trash_icon_size = 8  # taille des carrés
        self.trash_icon_spacing = 7  # espace entre les carrés
        self.inventory = []
        self.throw_cooldown = 0
        self.slot_image = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.rect(self.slot_image, (100, 100, 100, 150), (0, 0, 60, 60),border_radius=5)  # Fond gris semi-transparent
        pygame.draw.rect(self.slot_image, (255, 255, 255), (0, 0, 60, 60), 2, border_radius=5)  # Bordure blanche

    HEART_IMG = pygame.image.load(join("assets", "Other", "heart.png")).convert_alpha()

    def draw_health_bar(self, win, offset_x):
        heart_scale = 1.5
        heart = pygame.transform.scale(
            self.HEART_IMG,
            (self.HEART_IMG.get_width() * heart_scale,
             self.HEART_IMG.get_height() * heart_scale)
        )

        max_hearts = 3
        current_hearts = round((self.health / self.max_health) * max_hearts)

        bar_x = 20
        bar_y = 20
        spacing = heart.get_width() + 4

        for i in range(max_hearts):
            if i < current_hearts:
                win.blit(heart, (bar_x + i * spacing, bar_y))
            else:
                # Cœur grisé (vide)
                grey = heart.copy()
                grey.fill((80, 80, 80, 180), special_flags=pygame.BLEND_RGBA_MULT)
                win.blit(grey, (bar_x + i * spacing, bar_y))

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
        target_max = 40  # La taille maximale souhaitée (longueur ou largeur)

        start_x = WIDTH - padding - slot_size
        start_y = padding

        # 1. Dessiner les slots vides
        for i in range(self.MAX_TRASH):
            x = start_x - (i * (slot_size + gap))
            win.blit(self.slot_image, (x, start_y))

        # 2. Dessiner les objets
        for i, item_data in enumerate(reversed(self.inventory)):
            if i < self.MAX_TRASH:
                filename, _ = item_data
                path = join("assets", "Items", "Waste", filename)
                item_img = pygame.image.load(path).convert_alpha()

                # --- REDIMENSIONNEMENT PROPORTIONNEL ---
                original_width = item_img.get_width()
                original_height = item_img.get_height()

                # On cherche le ratio pour que le plus grand côté soit égal à target_max
                ratio = target_max / max(original_width, original_height)

                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)

                item_img = pygame.transform.scale(item_img, (new_width, new_height))

                # --- CENTRAGE DYNAMIQUE ---
                # On calcule la position pour que l'image soit bien au milieu du slot de 60px
                x_slot = start_x - (i * (slot_size + gap))

                # Offset = (Taille du slot - Taille de l'image) / 2
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
        # Gravité
        self.y_vel += self.GRAVITY

        # --- Mouvement horizontal ---
        self.hitbox.x += self.x_vel
        self.rect.topleft = self.hitbox.topleft

        # --- Mouvement vertical ---
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
            self.inventory.append((obj.filename, obj.scale)) # <--- On stocke le nom du fichier image
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
        # On charge l'image du plot
        path = join("assets", "Other", "Plot.png")
        img = pygame.image.load(path).convert_alpha()

        # On redimensionne l'image pour qu'elle corresponde à la taille voulue
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

        # On stocke le nom du fichier pour pouvoir le réutiliser lors du lancer
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
            if isinstance(obj, Block):  # ← collision seulement avec les blocs
                if self.rect.colliderect(obj.rect):
                    self.rect.bottom = obj.rect.top
                    self.y_vel = 0
                    break

    def update(self, objects):

        # --- GRAVITÉ seulement si pas au sol ---
        if not self.on_ground:
            self.y_vel += self.GRAVITY

        # --- FRICTION AIR ---
        self.x_vel *= self.FRICTION

        # =====================
        #   MOUVEMENT X
        # =====================
        self.pos_x += self.x_vel
        self.rect.x = int(self.pos_x)

        for obj in objects:
            if isinstance(obj, Block) and self.rect.colliderect(obj.rect):

                if self.x_vel > 0:
                    self.rect.right = obj.rect.left
                elif self.x_vel < 0:
                    self.rect.left = obj.rect.right

                self.pos_x = self.rect.x

                # rebond mur
                self.x_vel *= -self.BOUNCE_DAMPING

        # =====================
        #   MOUVEMENT Y
        # =====================
        self.pos_y += self.y_vel
        self.rect.y = int(self.pos_y)

        self.on_ground = False

        for obj in objects:
            if isinstance(obj, Block) and self.rect.colliderect(obj.rect):

                # --- SOL ---
                if self.y_vel > 0:
                    self.rect.bottom = obj.rect.top
                    self.pos_y = self.rect.y

                    self.y_vel *= -self.BOUNCE_DAMPING
                    self.x_vel *= 0.8

                    # Si rebond trop faible → stop total
                    if abs(self.y_vel) < self.STOP_THRESHOLD:
                        self.y_vel = 0
                        self.x_vel = 0
                        self.on_ground = True

                # --- PLAFOND ---
                elif self.y_vel < 0:
                    self.rect.top = obj.rect.bottom
                    self.pos_y = self.rect.y
                    self.y_vel *= -self.BOUNCE_DAMPING

        if self.on_ground:
            self.is_launched = False
            self.x_vel *= 0.9  # Friction au sol pour l'arrêter plus vite

class Block(Object):
    def __init__(self, x, y, size_y, name, size_x=96):
        super().__init__(x, y, size_x, size_y)
        # On récupère l'image redimensionnée
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
    # 1. On dessine le fond Parallax (remplace la boucle for i in range...)
    # Cette méthode va blit 'sky', 'houses' et 'road' avec leurs propres calculs de boucle
    bg_parallax.draw(offset_x)

    for obj in objects:
        if isinstance(obj, Water):
            obj.draw(window, offset_x)


    # 2. Dessin des objets du monde (inchangé)
    for obj in objects:
        if isinstance(obj, Water):
            continue
        if isinstance(obj, ShadowBlock):
            continue
        if hasattr(obj, "collected") and obj.collected:
            continue
        obj.draw(window, offset_x)

    # 3. Dessin du joueur et de ses barres d'état (inchangé)
    player.draw(window, offset_x)
    player.draw_health_bar(window, offset_x)
    player.draw_trajectory(window, offset_x)
    player.draw_inventory(window)

    pygame.display.update()

def handle_vertical_collision(player, objects):
    collided = []

    for obj in objects:
        if player.hitbox.colliderect(obj.rect):

            # Collision sol
            if player.y_vel > 0:
                player.hitbox.bottom = obj.rect.top
                player.y_vel = 0
                player.jump_count = 0

            # Collision plafond
            elif player.y_vel < 0:
                player.hitbox.top = obj.rect.bottom
                player.y_vel = 0

            if isinstance(obj, Water):
                player.make_hit()

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

    # --- MOUVEMENTS HORIZONTAUX ---
    if keys[pygame.K_q] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_d] and not collide_right:
        player.move_right(PLAYER_VEL)

    # --- COLLISIONS VERTICALES ---
    handle_vertical_collision(player, objects)

    # --- RAMASSAGE DES DÉCHETS (Touche E) ---
    for obj in objects:
        if isinstance(obj, Waste):  # Détecte tous les types de déchets
            # On vérifie si le joueur est proche de l'objet
            if player.hitbox.colliderect(obj.rect.inflate(20, 20)):
                if keys[pygame.K_e]:
                    # On ramasse l'objet et on l'ajoute à l'inventaire du joueur
                    if player.collect_trash(obj, objects):
                        break  # On ne ramasse qu'un objet à la fois par appui

    # --- LANCER DES DÉCHETS (Shift + Clic Gauche) ---
    if keys[pygame.K_LSHIFT] and player.trash_collected > 0 and player.throw_cooldown == 0:
        if mouse_buttons[0]:
            # Calcul de la position de la souris par rapport au joueur
            m_x, m_y = pygame.mouse.get_pos()
            player_screen_x = player.hitbox.centerx - offset_x

            # Calcul de la force du lancer
            v_x = (m_x - player_screen_x) * 0.05
            v_y = (m_y - player.hitbox.centery) * 0.12

            # Limitation de la vitesse max
            MAX_SPEED = 30
            v_x = max(min(v_x, MAX_SPEED), -MAX_SPEED)
            v_y = max(min(v_y, MAX_SPEED), -MAX_SPEED)

            # Position de départ du déchet lancé (gauche ou droite du joueur)
            if m_x > player_screen_x:
                spawn_x = player.hitbox.right + 10
            else:
                spawn_x = player.hitbox.left - 60
            spawn_y = player.hitbox.top + 10

            # --- LOGIQUE DYNAMIQUE ---
            # On récupère le nom du fichier de l'objet ramassé en dernier
            if len(player.inventory) > 0:
                last_item_file,scale = player.inventory.pop()

                # On crée le nouveau projectile avec la BONNE image
                launched_item = Waste(spawn_x, spawn_y, last_item_file, scale,vel_x=v_x, vel_y=v_y)
                objects.append(launched_item)

                player.trash_collected -= 1
                player.throw_cooldown = 30


class Avion(Object):
    # 0.5 secondes à 60 FPS = 30 frames
    OPEN_DURATION = 30

    def __init__(self, x, y, direction=1, speed=3):
        # --- CHARGEMENT DES IMAGES ---
        # On construit le chemin : assets/Items/Plane/planeClosed.png
        path_closed = join("assets", "Items", "Plane", "planeClosed.png")
        path_open = join("assets", "Items", "Plane", "planeOpen.png")

        self.img_closed = pygame.image.load(path_closed).convert_alpha()
        self.img_open = pygame.image.load(path_open).convert_alpha()

        # On redimensionne (x3 pour que ce soit bien visible)
        scale = 3
        self.img_closed = pygame.transform.scale_by(self.img_closed, scale)
        self.img_open = pygame.transform.scale_by(self.img_open, scale)

        width = self.img_closed.get_width()
        height = self.img_closed.get_height()

        super().__init__(x, y, width, height, "avion")

        self.direction = direction  # 1 = droite, -1 = gauche
        self.speed = speed

        # Timers pour le largage
        self.reset_drop_timer()
        self.is_open = False
        self.post_drop_timer = 0

    def reset_drop_timer(self):
        # L'avion lâche un truc toutes les 2 à 5 secondes
        self.drop_timer = random.randint(120, 300)

    def move(self):
        self.rect.x += self.speed * self.direction

    def update(self, objects):
        self.move()
        self.drop_timer -= 1

        # 1. On ouvre 0.5s (30 frames) AVANT le largage
        if self.drop_timer <= self.OPEN_DURATION:
            self.is_open = True

        # 2. Le moment du largage
        if self.drop_timer <= 0:
            self.drop_waste(objects)
            self.reset_drop_timer()
            self.post_drop_timer = self.OPEN_DURATION  # On garde ouvert 0.5s APRES

        # 3. Gestion de la fermeture après le délai
        if self.post_drop_timer > 0:
            self.post_drop_timer -= 1
        elif self.drop_timer > self.OPEN_DURATION:
            # On ne referme que si on n'est pas déjà dans la phase "avant largage"
            self.is_open = False

    def drop_waste(self, objects):
        # On fait apparaître le déchet au niveau de la soute (arrière de l'avion)
        # Si direction = -1 (gauche), l'arrière est à droite de l'image
        trash_x = self.rect.right - 20 if self.direction == -1 else self.rect.left + 20
        trash_y = self.rect.bottom - 15

        random_file = random.choice(["tire.png", "bottle.png", "glassBottle.png", "trashBag.png", "cardboard.png"])

        # Petit ajustement de scale selon l'objet pour que ce soit réaliste
        scales = {"tire.png": 3, "glassBottle.png": 1, "cardboard.png": 2.7}
        s = scales.get(random_file, 2)

        trash = Waste(trash_x, trash_y, random_file, scale=s, vel_x=self.speed * self.direction, vel_y=2)
        objects.append(trash)

    def draw(self, win, offset_x):
        # Choix de l'image selon l'état soute ouverte/fermée
        sprite = self.img_open if self.is_open else self.img_closed

        # Ton dessin original pointe vers la gauche.
        # Si direction = 1 (droite), on flippe l'image horizontalement.
        if self.direction == 1:
            sprite = pygame.transform.flip(sprite, True, False)

        win.blit(sprite, (self.rect.x - offset_x, self.rect.y))


def spawn_avion(objects, x):
    direction = random.choice([-1, 1])
    if direction == 1:
        spawn_x = x - 200
    else:
        spawn_x = x + WIDTH + 200

    avion = Avion(spawn_x, 0, direction, speed=random.randint(2, 5))
    objects.append(avion)


class Bridge(Object):
    def __init__(self, x, y, width, bottom_img, top_img):
        # On définit la hauteur totale basée sur le bottom_img pour la collision
        super().__init__(x, y, width, bottom_img.get_height(), "bridge")
        self.bottom_img = bottom_img
        self.top_img = top_img
        # Le rect de collision sera calé sur le haut du bottomBridge
        self.rect = pygame.Rect(x, y, width, 20) # 20px d'épaisseur pour marcher dessus

    def draw(self, win, offset_x):
        # On dessine le bas (le support)
        win.blit(self.bottom_img, (self.rect.x - offset_x, self.rect.y))
        # On dessine le haut (la rambarde) juste au dessus
        # On soustrait la hauteur de la rambarde pour qu'elle soit posée sur le pont
        win.blit(self.top_img, (self.rect.x - offset_x, self.rect.y - self.top_img.get_height() + 3))

class ParallaxBackground:
    def __init__(self, win):
        self.window = win
        self.width = win.get_width()
        # On définit le décalage vertical : -96 pour monter
        self.y_offset = -96

        # Chargement des images
        self.layers = [
            {"img": pygame.image.load(join("assets", "Background", "sky.png")).convert_alpha(), "speed": 0.1},
            {"img": pygame.image.load(join("assets", "Background", "houses.png")).convert_alpha(), "speed": 0.4},
            {"img": pygame.image.load(join("assets", "Background", "road.png")).convert_alpha(), "speed": 0.7}
        ]

    def draw(self, offset_x):
        for layer in self.layers:
            # On calcule le décalage horizontal selon la vitesse du calque
            rel_x = (offset_x * layer["speed"]) % self.width

            # On dessine l'image principale avec le décalage Y de -96
            self.window.blit(layer["img"], (-rel_x, self.y_offset))

            # On dessine la copie à côté avec le même décalage Y
            if rel_x > 0:
                self.window.blit(layer["img"], (self.width - rel_x, self.y_offset))
            else:
                self.window.blit(layer["img"], (-self.width - rel_x, self.y_offset))


class Water(Object):
    ANIMATION_DELAY = 10  # Environ 6 FPS (60 FPS / 10 = 6 images par seconde)
    SURFACE_COLOR = (116, 163, 59)  # Couleur hexa #74a33b convertie en RGB

    def __init__(self, y, height, speed=1):
        # On définit une largeur très grande pour couvrir le niveau
        # Et la hauteur totale de la masse d'eau
        super().__init__(-5000, y, 15000, height, "water")

        # Chargement de la feuille de sprite
        path = join("assets", "Other", "water.png")  # Assure-toi du chemin/nom du fichier
        sprite_sheet = pygame.image.load(path).convert_alpha()

        # Découpage des 4 frames (200x50 chacune)
        self.sprites = []
        for i in range(4):
            surface = pygame.Surface((200, 50), pygame.SRCALPHA)
            surface.blit(sprite_sheet, (0, 0), pygame.Rect(0, i * 50, 200, 50))
            # surface = pygame.transform.scale2x(surface) # Décommente pour agrandir l'écume
            self.sprites.append(surface)

        self.image = self.sprites[0]
        self.animation_count = 0
        self.speed = speed

    def update(self):
        # Gestion du cycle d'animation
        self.animation_count += 1
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(self.sprites)
        self.image = self.sprites[sprite_index]

    def draw(self, win, offset_x):
        # --- ÉTAPE 1 : Le gros rectangle de couleur unie #74a33b ---
        # Il remplit toute la zone de l'eau
        pygame.draw.rect(
            win,
            self.SURFACE_COLOR,
            (self.rect.x - offset_x, self.rect.y + 50, self.rect.width, self.rect.height + 800)
        )

        # --- ÉTAPE 2 : La ligne d'écume animée tout en haut ---
        # On dessine l'image en boucle (tiling) UNIQUEMENT sur la première ligne
        sprite_w = self.image.get_width()

        # On remplit horizontalement, mais y reste fixe à la surface (self.rect.y)
        for x in range(0, self.rect.width, sprite_w):
            win.blit(self.image, (self.rect.x + x - offset_x, self.rect.y))

    def up(self, dy):
        self.rect.y -= dy * self.speed


def main(window):
    clock = pygame.time.Clock()

    parallax_bg = ParallaxBackground(window)
    offset_x = 0
    scroll_area_width = 400  # Zone où la caméra commence à suivre le joueur
    block_size = 96

    generated_until = block_size * 36  #utilisation gen aleatoire
    segment_length = block_size * 8

    img_top = pygame.image.load(join("assets", "Terrain", "topBridge.png")).convert_alpha()
    img_bottom = pygame.image.load(join("assets", "Terrain", "bottomBridge.png")).convert_alpha()

    # On scale pour que ça fasse exactement la largeur de 3 blocs (3 * 96 = 288)
    # sans changer la hauteur pour respecter ton souhait
    bridge_width = 308


    # Positionnement au niveau du trou (index 3)
    bridge_x = 3 * block_size - 10
    bridge_y = HEIGHT - block_size * 2 # Aligné sur le haut du sol

    bridge = Bridge(bridge_x, bridge_y, bridge_width, img_bottom, img_top)

    player = Player(150, 100, 60, 96)
    floor = [Block(i * block_size, HEIGHT - block_size * 2, block_size, "dirtGrassBlock.png") for i in range(-10, WIDTH * 10 // block_size) if i not in [3, 4, 5]]
    bottom_floor = [Block(i * block_size, HEIGHT - block_size, block_size,"dirtBlock.png") for i in range(-10, WIDTH * 10 // block_size) if i not in [3, 4, 5]]
    left_wall = [Block(-960, i * block_size, block_size,"dirtBlock.png") if i != 0 else Block(-960, i * block_size, block_size,"dirtGrassBlock.png") for i in range(-5,9)]
    left_left__wall = [Block(-1056, j * block_size, block_size,"dirtBlock.png") if j != 0 else Block(-1056, j * block_size, block_size,"dirtGrassBlock.png") for j in range(-5,9)]
    left_left_left_wall = [Block(-1152, i * block_size, block_size,"dirtBlock.png") if i != 0 else Block(-1152, i * block_size, block_size,"dirtGrassBlock.png") for i in range(-5,9)]


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
        Plot(-148, 536, 48, 72),

        Waste(block_size * 10, HEIGHT - block_size * 4 - 75,"tire.png",3),
        Waste(block_size * 11.5, HEIGHT - block_size * 4 - 75,"bottle.png",2),
        Waste(block_size * 12, HEIGHT - block_size * 4 - 75, "glassBottle.png", 1),
        Waste(block_size * 13, HEIGHT - block_size * 4 - 75,"trashBag.png"),
        Waste(block_size * 14, HEIGHT - block_size * 4 - 75,"cardboard.png",2.7),

    ]

    water = Water(HEIGHT - 100, 200, 0.3)
    objects.append(water)

    offset_x = 0
    scroll_area_width = 200
    scroll = 0

    camera_shifted = False
    saved_offset_x = 0
    saved_scroll = 0

    cpt = 0

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

        handle_move(player, objects, offset_x)
        player.loop(FPS)
        handle_vertical_collision(player, objects)

        # Dictionnaire de correspondance : Fichier -> Couleur de poubelle
        WASTE_TYPES = {
            "glassBottle.png": "green",
            "cardboard.png": "yellow",
            "bottle.png": "yellow",
            "tire.png": "black",
            "trashBag.png": "black"
        }

        for obj in objects[:]:  # Utilise [:] pour copier la liste car on va supprimer des éléments

            if isinstance(obj, Water):
                obj.update()

            if isinstance(obj, Waste):
                obj.update(objects)

                for other in objects:
                    if isinstance(other, TrashBin):
                        # On vérifie la collision avec la hitbox de la poubelle
                        if obj.rect.colliderect(other.hitbox):
                            correct_color = WASTE_TYPES.get(obj.filename)

                            if correct_color == other.color:
                                # BONNE POUBELLE
                                objects.remove(obj)
                            else:
                                # MAUVAISE POUBELLE
                                # On fait monter l'eau (on réduit sa coordonnée Y)
                                water.up(80)
                                objects.remove(obj)
                            break

        if random.randint(1, 180) == 1 and cpt % 5 == 0:
            spawn_avion(objects, player.hitbox.x)

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

            # --- AJOUT ETAPE 4 : CAMÉRA NORMALE ---
        if not camera_shifted:
            if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                    (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
                offset_x += player.x_vel
                scroll -= player.x_vel

            if abs(scroll) > WIDTH:
                scroll = 0

        # --- AJOUT ETAPE 5 : DESSIN ---
        draw(window, parallax_bg, player, objects, offset_x)




    pygame.quit()
    quit()

if __name__ == "__main__":
    main(window)
