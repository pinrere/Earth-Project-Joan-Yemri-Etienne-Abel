import pygame
from os.path import join
from src.classes.waste import Waste
from src.fonctions.load_sprites_from_folder import load_sprites_from_folder

WIDTH, HEIGHT = 1400, 800

class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 0.8
    ANIMATION_DELAY = 4

    def __init__(self, x, y, width, height):
        super().__init__()
        self.SPRITES = load_sprites_from_folder("MainCharacters", "MaleChar", 3, True)
        self.HEART_IMG = pygame.image.load(join("assets", "Other", "heart.png")).convert_alpha()
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
