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


def get_block(size):
    # On charge directement ton nouveau fichier extrait
    path = join("assets", "Terrain", "dirtBlock.png")
    image = pygame.image.load(path).convert_alpha()

    # On redimensionne l'image à la taille voulue pour le jeu
    # (Si block_size est 96, elle restera en 96x96)
    return pygame.transform.scale(image, (size, size))

class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 0.8
    SPRITES = load_sprites_from_folder("MainCharacters", "MaleChar",3, True)
    ANIMATION_DELAY = 4

    def __init__(self, x, y, width, height):
        super().__init__()
        self.hitbox = pygame.Rect(x, y, width, height)
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

    def draw_health_bar(self, win, offset_x):
        bar_x = self.hitbox.x - offset_x
        bar_y = self.hitbox.y - 20
        bar_width = self.hitbox.width
        bar_height = 10

        pygame.draw.rect(win, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))

        color = (0, 255, 0)
        if self.health < 50: color = (255, 165, 0)
        if self.health < 20: color = (255, 0, 0)
        health_ratio = self.health / self.max_health

        current_health_width = bar_width * health_ratio

        if self.health > 0:
            pygame.draw.rect(win, color, (bar_x, bar_y, current_health_width, bar_height))

        pygame.draw.rect(win, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height), 2)

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

    def draw_trash_bar(self, win, offset_x):
        bar_x = self.hitbox.x - offset_x
        bar_y = self.hitbox.y - 30  # au-dessus de la barre de vie

        for i in range(self.MAX_TRASH):
            x = bar_x + i * (self.trash_icon_size + self.trash_icon_spacing) + 10
            y = bar_y
            color = (255, 30, 45) if i < self.trash_collected else (50, 50, 50)  # vert si collecté, gris sinon
            pygame.draw.rect(win, color, (x, y, self.trash_icon_size, self.trash_icon_size))
            pygame.draw.rect(win, (0, 0, 0), (x, y, self.trash_icon_size, self.trash_icon_size), 2)  # bordure noire

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
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        # On récupère l'image redimensionnée
        self.image = get_block(size)
        self.rect = pygame.Rect(x, y, size, size)

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

    # 2. Dessin des objets du monde (inchangé)
    for obj in objects:
        if hasattr(obj, "collected") and obj.collected:
            continue
        obj.draw(window, offset_x)

    # 3. Dessin du joueur et de ses barres d'état (inchangé)
    # Note : J'ai gardé ta hitbox rouge (rect) pour tes tests
    pygame.draw.rect(
        window,
        (255, 0, 0),
        player.hitbox.move(-offset_x, 0),
        2
    )
    player.draw(window, offset_x)
    player.draw_health_bar(window, offset_x)
    player.draw_trash_bar(window, offset_x)
    player.draw_trajectory(window, offset_x)

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
    if keys[pygame.K_LSHIFT] and player.trash_collected > 0:
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

                # Petit délai pour éviter de lancer tout l'inventaire en un clic
                pygame.time.delay(200)

class Avion(Object):
    WIDTH = 120
    HEIGHT = 40
    COLOR = (255, 0, 0)

    def __init__(self, x, y, direction=1, speed=3):
        super().__init__(x, y, self.WIDTH, self.HEIGHT, "avion")
        self.direction = direction  # 1 = droite, -1 = gauche
        self.speed = speed
        self.reset_drop_timer()
        self.image.fill(self.COLOR)

    def reset_drop_timer(self):
        self.drop_timer = random.randint(60, 240)

    def move(self):
        self.rect.x += self.speed * self.direction

    def try_drop_trash(self, objects):
        self.drop_timer -= 1
        if self.drop_timer <= 0:
            trash_x = self.rect.centerx
            trash_y = self.rect.bottom
            trash = Waste(trash_x, trash_y, 0, 0)
            objects.append(trash)
            self.reset_drop_timer()

    def update(self, objects):
        self.move()
        self.try_drop_trash(objects)

    def draw(self, win, offset_x):
        pygame.draw.rect(
            win,
            self.COLOR,
            (self.rect.x - offset_x, self.rect.y, self.rect.width, self.rect.height)
        )

def spawn_avion(objects, x):
    direction = random.choice([-1, 1])
    if direction == 1:
        spawn_x = x - 200
    else:
        spawn_x = x + WIDTH + 200

    avion = Avion(spawn_x, 0, direction, speed=random.randint(2, 5))
    objects.append(avion)


class ParallaxBackground:
    def __init__(self, win):
        self.window = win
        self.width = win.get_width()

        # Chargement des images (assure-toi qu'elles sont dans assets/Background/)
        # Ordre : Arrière-plan -> Premier plan
        self.layers = [
            {"img": pygame.image.load(join("assets", "Background", "sky.png")).convert_alpha(), "speed": 0.1},
            {"img": pygame.image.load(join("assets", "Background", "houses.png")).convert_alpha(), "speed": 0.4},
            {"img": pygame.image.load(join("assets", "Background", "road.png")).convert_alpha(), "speed": 0.7}
        ]

    def draw(self, offset_x):
        for layer in self.layers:
            # On calcule le décalage selon la vitesse du calque
            # Le modulo (%) permet de faire boucler l'image à l'infini
            rel_x = (offset_x * layer["speed"]) % self.width

            # On dessine l'image principale
            self.window.blit(layer["img"], (-rel_x, 0))

            # On dessine une copie à côté pour combler le vide lors du défilement
            if rel_x > 0:
                self.window.blit(layer["img"], (self.width - rel_x, 0))
            else:
                self.window.blit(layer["img"], (-self.width - rel_x, 0))

class Water(Object):
    def __init__(self, y, height, speed = 1):
        super().__init__(-5000, y, 10000, height, "water")
        self.speed = speed
        self.image.fill((120, 80, 200))
    def update(self, dy):
        self.rect.y -= self.speed * dy


def main(window):
    clock = pygame.time.Clock()

    parallax_bg = ParallaxBackground(window)
    offset_x = 0
    scroll_area_width = 400  # Zone où la caméra commence à suivre le joueur
    block_size = 96

    generated_until = block_size * 36  #utilisation gen aleatoire
    segment_length = block_size * 8

    player = Player(100, 100, 60, 96)
    floor = [Block(i * block_size, HEIGHT - block_size, block_size) for i in range(-WIDTH * 10 // block_size, WIDTH * 10 // block_size)]
    objects = [
        *floor,

        TrashBin(-800, HEIGHT - 175, "green"),
        TrashBin(-640, HEIGHT - 175, "yellow"),
        TrashBin(-480, HEIGHT - 175, "black"),

        ShadowBlock(-180, 0, 80, HEIGHT),

        Waste(block_size * 5, HEIGHT - block_size * 4 - 75,"tire.png",3.4),
        Waste(block_size * 7, HEIGHT - block_size * 6 - 75,"bottle.png",2),
        Waste(block_size * 8, HEIGHT - block_size * 3 - 75, "glassBottle.png", 1),
        Waste(block_size * 9, HEIGHT - block_size * 5 - 75,"trashBag.png"),
        Waste(block_size * 11, HEIGHT - block_size * 3 - 75,"cardboard.png",2.7),

    ]

    water = Water(HEIGHT + 200, 200, 0.5)
    objects.append(water)

    offset_x = 0
    scroll_area_width = 200
    scroll = 0

    camera_shifted = False
    saved_offset_x = 0
    saved_scroll = 0

    run = True
    while run:
        clock.tick(FPS)

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

        if not any(isinstance(obj, Waste) and obj.filename == "trashBag.png" for obj in objects) and not any(
                item[0] == "trashBag.png" for item in player.inventory):
            objects.append(Waste(-50,HEIGHT - block_size * 4 - 75 , "trashBag.png"))

        for obj in objects[:]:  # Utilise [:] pour copier la liste car on va supprimer des éléments
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
                                water.rect.y -= 30
                                objects.remove(obj)
                            break

        """if random.randint(1, 180) == 1:
            spawn_avion(objects, player.hitbox.x)"""

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
