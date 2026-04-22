import os
import random
import pygame
from os.path import join
from src.classes.block import Block
from src.classes.waste import Waste

WIDTH, HEIGHT = 1400, 800


class Boss:
    """Le boss final : PDG de la pollution."""

    ANIMATION_DELAY = 6
    MAX_HP = 10
    STOP_DISTANCE = 350  # Distance à laquelle il s'arrête pour tirer
    WALK_SPEED = 3
    WALK_SPEED_RAGE = 6

    def __init__(self, x, y):
        self.sprites = {}
        boss_path = join("assets", "MainCharacters", "Boss")

        for subfolder in ["player-stand", "player-run", "player-hurt", "player-shoot"]:
            folder_path = join(boss_path, subfolder)
            files = sorted([f for f in os.listdir(folder_path) if f.endswith(".png")])
            frames = []
            for f in files:
                img = pygame.image.load(join(folder_path, f)).convert_alpha()
                img = pygame.transform.scale_by(img, 4)
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

        # --- NOUVEAU : États d'apparition et de mort ---
        self.state = "spawning"
        self.death_timer = 300  # L'explosion va durer environ 2.5 secondes

        self.hurt_timer = 0
        self.shoot_timer = 0
        self.shoot_anim_timer = 0
        self.shoot_cooldown = 120
        self.alive = True

        self.sprite = self.sprites["player-stand_left"][0]

    @property
    def is_rage(self):
        return self.hp <= self.MAX_HP // 2

    def take_hit(self):
        """Appelé quand un déchet touche le boss."""
        # Invincible pendant l'animation hurt, l'apparition ou la mort
        if self.state in ["hurt", "spawning", "dying"]:
            return

        self.hp -= 1
        self.state = "hurt"
        self.hurt_timer = 40
        self.animation_count = 0

        if self.hp <= 0:
            self.state = "dying"  # Déclenche l'explosion au lieu de mourir direct

    def update(self, player, objects):
        trigger_shake = 0  # Permet de dire à la caméra de trembler

        # --- CINÉMATIQUE D'APPARITION (Tombe du ciel) ---
        if self.state == "spawning":
            self.hitbox.y += 25  # Il tombe très vite !
            self._animate("player-stand")

            # Quand il touche le sol...
            for obj in objects:
                if obj.__class__.__name__ in ["Block", "Platform"] and self.hitbox.colliderect(obj.rect):
                    self.hitbox.bottom = obj.rect.top
                    self.state = "stand"
                    trigger_shake = 90  # Fait trembler l'écran pendant 30 frames !
                    self.shoot_timer = 60  # Laisse une petite pause au joueur
                    break
            return trigger_shake

        # --- CINÉMATIQUE DE MORT (Explosions en chaîne) ---
        if self.state == "dying":
            self.death_timer -= 1

            if self.death_timer > 180:
                # PHASE 1 (2 secondes) : Au sol, douleur, tremblement
                self._animate("player-hurt")
                return 15  # L'écran tremble fortement
            else:
                # PHASE 2 (3 secondes) : Ombre qui s'envole, plus de tremblement
                self.hitbox.y -= 3  # S'envole vers le ciel

                if self.death_timer <= 0:
                    self.alive = False

                return 0

        # --- TIMER HURT ---
        if self.state == "hurt":
            self.hurt_timer -= 1
            if self.hurt_timer <= 0:
                self.state = "walk"
            self._animate("player-hurt")
            return trigger_shake

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
                    self.shoot_anim_timer = 25
                    self._shoot(player, objects)
                    self.shoot_timer = cooldown

        # --- Gravité basique ---
        self.hitbox.y += 8
        for obj in objects:
            if obj.__class__.__name__ in ["Block", "Platform"] and self.hitbox.colliderect(obj.rect):
                self.hitbox.bottom = obj.rect.top
                break

        return trigger_shake

    def _shoot(self, player, objects):
        spawn_x = self.hitbox.centerx
        spawn_y = self.hitbox.centery - 20

        dx = player.hitbox.centerx - spawn_x
        dy = player.hitbox.centery - spawn_y

        nb_dechets = 1
        flight_time = 45.0
        spread = 1.0
        special_straight_shot = False

        if self.hp <= 3:
            nb_dechets = 3
            flight_time = 32.0
            spread = 4.0
            if random.random() < 0.7:
                special_straight_shot = True

        elif self.hp <= 5:
            nb_dechets = 2
            flight_time = 22.0
            spread = 1.5
            if random.random() < 0.5:
                special_straight_shot = True

        elif self.hp <= 8:
            nb_dechets = 2
            flight_time = 40.0
            spread = 1.5

        gravity = Waste.GRAVITY

        base_vx = dx / flight_time
        base_vy = (dy / flight_time) - (0.5 * gravity * flight_time)

        base_vx = max(min(base_vx, 25), -25)
        base_vy = max(min(base_vy, 10), -35)

        for _ in range(nb_dechets):
            r_file = random.choice(["tire.png", "glassBottle.png", "cardboard.png", "bottle.png", "trashBag.png"])
            scales = {"tire.png": 3, "glassBottle.png": 1, "cardboard.png": 2.7, "bottle.png": 2, "trashBag.png": 3}

            vx_final = base_vx + random.uniform(-spread, spread)
            vy_final = base_vy + random.uniform(-spread, spread / 2)

            trash = Waste(spawn_x, spawn_y, r_file, scale=scales.get(r_file, 3), vel_x=vx_final, vel_y=vy_final)
            objects.append(trash)

        if special_straight_shot:
            r_file = "tire.png"
            scale = 3
            fast_flight_time = 12.0
            straight_vx = dx / fast_flight_time
            straight_vy = (dy / fast_flight_time) - (0.5 * gravity * fast_flight_time)
            straight_vx = max(min(straight_vx, 40), -40)
            straight_vy = max(min(straight_vy, 10), -20)
            fast_trash = Waste(spawn_x, spawn_y, r_file, scale=scale, vel_x=straight_vx, vel_y=straight_vy)
            objects.append(fast_trash)

    def _animate(self, anim_name):
        key = next((k for k in self.sprites if anim_name in k and k.endswith("_" + self.direction)), None)
        if key is None:
            key = next((k for k in self.sprites if anim_name in k and k.endswith("_left")), None)
        sprites = self.sprites[key]
        idx = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[idx]
        self.animation_count += 1

    def draw(self, win, offset_x):
        draw_x = self.hitbox.x - offset_x - self.hitbox.width // 2
        draw_y = self.hitbox.y + 67

        # --- EFFET VISUEL D'EXPLOSION ---
        if self.state == "dying":
            if self.death_timer > 180:
                # PHASE 1 : Rendu normal du robot avec des explosions
                win.blit(self.sprite, (draw_x, draw_y))
                for _ in range(4):
                    ex = draw_x + random.randint(-20, self.hitbox.width * 2)
                    ey = draw_y + random.randint(-20, self.hitbox.height * 2)
                    r = random.randint(20, 70)
                    color = random.choice([(255, 100, 0), (255, 50, 0), (255, 255, 0), (200, 200, 200)])
                    pygame.draw.circle(win, color, (ex, ey), r)
            else:
                # PHASE 2 : Rendu en ombre noire transparente
                shadow = self.sprite.copy()
                shadow.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)

                # Le timer restant est sur 180 frames, on calcule la transparence
                alpha = max(0, int((self.death_timer / 180) * 255))
                shadow.set_alpha(alpha)
                win.blit(shadow, (draw_x, draw_y))
        else:
            # Rendu normal s'il est vivant
            win.blit(self.sprite, (draw_x, draw_y))
            self._draw_health_bar(win)
    def _draw_health_bar(self, win):
        bar_width = 300
        bar_height = 22
        bar_x = WIDTH // 2 - bar_width // 2
        bar_y = 140

        pygame.draw.rect(win, (60, 0, 0), (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4), border_radius=6)
        pygame.draw.rect(win, (30, 30, 30), (bar_x, bar_y, bar_width, bar_height), border_radius=5)

        ratio = max(0, self.hp / self.MAX_HP)
        color = (220, 50, 50) if not self.is_rage else (255, 120, 0)
        filled_w = int(bar_width * ratio)
        if filled_w > 0:
            pygame.draw.rect(win, color, (bar_x, bar_y, filled_w, bar_height), border_radius=5)

        pygame.draw.rect(win, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 2, border_radius=5)

        font = pygame.font.SysFont("arial", 20, bold=True)
        label = font.render(f"PDG DE LA POLLUTION  {self.hp} / {self.MAX_HP}", True, (255, 255, 255))
        win.blit(label, (bar_x + bar_width // 2 - label.get_width() // 2, bar_y + 2))