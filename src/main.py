import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join
from collections import defaultdict
pygame.init()


pygame.display.set_caption("Eco Guardian")


WIDTH, HEIGHT = 1200, 800
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
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)

class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
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
        # On affiche la trajectoire seulement si SHIFT est pressé et qu'on a des sacs
        keys = pygame.key.get_pressed()
        if not (keys[pygame.K_LSHIFT] and self.trash_collected > 0):
            return

        # Point de départ : centre du joueur
        start_x = self.hitbox.centerx - offset_x
        start_y = self.hitbox.centery

        # Calcul du vecteur force basé sur la position de la souris
        m_x, m_y = pygame.mouse.get_pos()
        # On divise par 10 pour que la puissance ne soit pas démesurée
        vel_x = (m_x - start_x) * 0.1
        vel_y = (m_y - start_y) * 0.1

        # Simulation de la courbe
        for i in range(1, 15):
            t = i * 1.5  # Intervalle de temps simulé
            # Formule : Position = Vitesse * Temps + 0.5 * Gravité * Temps^2
            px = start_x + vel_x * t
            py = start_y + vel_y * t + 0.5 * TrashBag.GRAVITY * (t ** 2)

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
        self.y_vel = -self.GRAVITY * 8 #changer la valeur si on veut sauter moins haut
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
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

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
            if obj in objects:
                objects.remove(obj)
            return True  # pour savoir qu’on a collecté
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

class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.x = x
        self.image.blit(block, (0,0))

class TrashBag(Object):
    GRAVITY = 1  # intensité de la gravité

    def __init__(self, x, y, vel_x=0, vel_y=0):
        width = 18 * 3
        height = 25 * 3
        super().__init__(x, y, width, height, "trashbag")

        # Chargement de l'image
        img = pygame.image.load(join("assets", "Items", "Waste", "trashBag.png")).convert_alpha()
        self.image.blit(pygame.transform.scale(img, (width, height)), (0, 0))

        self.collected = False
        self.y_vel = vel_y  # Vitesse verticale initiale
        self.x_vel = vel_x  # Vitesse horizontale initiale
        self.is_launched = (vel_x != 0 or vel_y != 0)

    def hit_vertical(self, objects):
        self.rect.y += self.y_vel
        for obj in objects:
            if isinstance(obj, Block):  # ← collision seulement avec les blocs
                if self.rect.colliderect(obj.rect):
                    self.rect.bottom = obj.rect.top
                    self.y_vel = 0
                    break

    def update(self, objects):
        # 1. On applique la gravité à la vitesse
        self.y_vel += self.GRAVITY

        # 2. On déplace le sac selon ses vitesses
        self.rect.y += self.y_vel
        self.rect.x += self.x_vel

        # 3. On gère les collisions avec les blocs
        for obj in objects:
            if isinstance(obj, Block) and self.rect.colliderect(obj.rect):
                # Collision par le haut (le sac se pose)
                if self.y_vel > 0:
                    self.rect.bottom = obj.rect.top
                    self.y_vel = 0
                    self.x_vel = 0  # Le sac s'arrête de glisser
                    self.is_launched = False
                    break


def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    nb_tiles = math.ceil(WIDTH / width) + 2


    return image, width, nb_tiles

def draw(window, bg_image,width_bg, nb_tiles, scroll, player, objects, offset_x):

    for i in range(-1,nb_tiles):
        window.blit(bg_image, (i*width_bg + scroll,0))

    for obj in objects:
        if hasattr(obj, "collected") and obj.collected:
            continue
        obj.draw(window, offset_x)

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

def handle_vertical_collision(player, objects, dy):
    collided = []

    for obj in objects:
        if player.hitbox.colliderect(obj.rect):
            if dy > 0:  # chute
                player.hitbox.bottom = obj.rect.top
                player.y_vel = 0
                player.fall_count = 0
                player.jump_count = 0
            elif dy < 0:  # plafond
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


def handle_move(player, objects, offset_x):  # Ajout de offset_x ici
    keys = pygame.key.get_pressed()
    mouse_buttons = pygame.mouse.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    # Déplacement (Q et D)
    if keys[pygame.K_q] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_d] and not collide_right:
        player.move_right(PLAYER_VEL)

    # Collisions verticales
    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

    for obj in to_check:
        if obj is None:
            continue

        if obj.name == "fire":
            player.make_hit()

        # COLLECTE : Ramasser le sac avec E
        if obj.name == "trashbag" and keys[pygame.K_e]:
            # On vérifie si le sac n'est pas déjà en plein vol
            if hasattr(obj, 'is_launched') and not obj.is_launched:
                player.collect_trash(obj, objects)

    # LANCER : Shift + Clic Gauche
    if keys[pygame.K_LSHIFT] and player.trash_collected > 0:
        if mouse_buttons[0]:  # Clic gauche enfoncé
            m_x, m_y = pygame.mouse.get_pos()

            # Ajustement de la position de la souris par rapport au scrolling
            # start_x est la position du joueur à l'écran
            start_x = player.hitbox.centerx - offset_x
            start_y = player.hitbox.centery

            # Calcul de la force (multiplié par 0.1 pour un lancer réaliste)
            v_x = (m_x - start_x) * 0.08
            v_y = (m_y - start_y) * 0.08

            # Création du sac avec les vitesses initiales
            launched_bag = TrashBag(player.hitbox.centerx, player.hitbox.centery, v_x, v_y)
            objects.append(launched_bag)

            player.trash_collected -= 1

            # Petit délai pour éviter de spammer les lancers
            pygame.time.delay(200)


def main(window):
    clock = pygame.time.Clock()
    bg_image,width_bg,nb_tiles = get_background("Polluted.png") #pour changer le background, juste changez la couleur. Par exemple écrivez Yellow.png

    block_size = 96

    generated_until = block_size * 36  #utilisation gen aleatoire
    segment_length = block_size * 8

    player = Player(100, 100, 60, 96)
    floor = [Block(i * block_size, HEIGHT - block_size, block_size) for i in range(-WIDTH * 10 // block_size, WIDTH * 10 // block_size)]
    objects = [
        *floor,

        Block(-block_size * 6, HEIGHT - block_size * 2, block_size),
        Block(-block_size * 4, HEIGHT - block_size * 4, block_size),
        Block(-block_size * 2, HEIGHT - block_size * 7, block_size),
        Block(block_size * 1, HEIGHT - block_size * 5, block_size),

        Block(block_size * 3, HEIGHT - block_size * 7, block_size),
        Block(block_size * 5, HEIGHT - block_size * 3, block_size),
        Block(block_size * 7, HEIGHT - block_size * 6, block_size),

        Block(block_size * 9, HEIGHT - block_size * 4, block_size),
        Block(block_size * 11, HEIGHT - block_size * 7, block_size),
        Block(block_size * 13, HEIGHT - block_size * 5, block_size),

        Block(block_size * 15, HEIGHT - block_size * 6, block_size),
        Block(block_size * 17, HEIGHT - block_size * 2, block_size),

        Block(block_size * 19, HEIGHT - block_size * 7, block_size),
        Block(block_size * 21, HEIGHT - block_size * 4, block_size),

        Block(block_size * 23, HEIGHT - block_size * 6, block_size),
        Block(block_size * 25, HEIGHT - block_size * 3, block_size),

        Block(block_size * 27, HEIGHT - block_size * 7, block_size),
        Block(block_size * 29, HEIGHT - block_size * 5, block_size),

        Block(block_size * 31, HEIGHT - block_size * 6, block_size),
        Block(block_size * 33, HEIGHT - block_size * 4, block_size),
        Block(-block_size * 36, HEIGHT - block_size * 2, block_size),
        Block(block_size * 35, HEIGHT - block_size * 4, block_size),
        Block(block_size * 34, HEIGHT - block_size * 4, block_size),

        TrashBag(block_size * 5, HEIGHT - block_size * 4 - 75),
        TrashBag(block_size * 13, HEIGHT - block_size * 6 - 75),
        TrashBag(block_size * 22, HEIGHT - block_size * 5 - 75),
        TrashBag(block_size * 27, HEIGHT - block_size * 3 - 75),
    ]

    offset_x = 0
    scroll_area_width = 200
    scroll = 0

    run = True
    while run:
        clock.tick(FPS) #comme ça on est sur que ça tourne en 60fps

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)
        handle_move(player, objects, offset_x)
        for obj in objects:
            if isinstance(obj, TrashBag):
                obj.update(objects)

        draw(window, bg_image, width_bg, nb_tiles, scroll, player, objects, offset_x)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            scroll -= player.x_vel
        if abs(scroll) > width_bg:
            scroll = 0

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

        #generation blocs aleatoire mettre condition
        #pour programation plus propre et vers la gauche aussi
        if player.hitbox.x + WIDTH > generated_until:
            start_x = generated_until
            end_x = generated_until + segment_length
            for i in range(random.randint(3, 7)):
                x = random.randint(start_x, end_x) // block_size * block_size
                height_level = random.choice([2, 3, 4, 5, 6])
                y = HEIGHT - block_size * height_level
                objects.append(Block(x, y, block_size))
            generated_until += segment_length

    pygame.quit()
    quit()

if __name__ == "__main__":
    main(window)
