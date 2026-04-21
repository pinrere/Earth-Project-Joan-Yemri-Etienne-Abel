import math
import pygame

WIDTH, HEIGHT = 1400, 800


class Water:
    ANIMATION_DELAY = 10
    SURFACE_COLOR = (116, 163, 59)

    def __init__(self, y, height, speed=1):
        from os.path import join
        self.rect = pygame.Rect(-5000, y, 15000, height)
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

        # Montée progressive
        self.base_y = float(y)      # position réelle actuelle (float pour interpolation douce)
        self.target_y = float(y)    # position cible
        self.flash_timer = 0        # flash rouge lors d'une montée

    def update(self):
        self.animation_count += 1
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(self.sprites)
        self.image = self.sprites[sprite_index]

        # Interpolation douce vers target_y (1.5px/frame → ~50 frames pour 75px)
        if self.base_y > self.target_y:
            self.base_y -= 1.5
            if self.base_y < self.target_y:
                self.base_y = self.target_y
            self.rect.y = int(self.base_y)

        if self.flash_timer > 0:
            self.flash_timer -= 1

    def draw(self, win, offset_x):
        # Flash rouge sur tout l'écran quand l'eau vient de monter
        if self.flash_timer > 0:
            alpha = int((self.flash_timer / 45) * 100)
            flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((255, 0, 0, alpha))
            win.blit(flash_surf, (0, 0))

        pygame.draw.rect(win, self.SURFACE_COLOR,
                         (self.rect.x - offset_x, self.rect.y + 50,
                          self.rect.width, self.rect.height + 800))
        sprite_w = self.image.get_width()
        for x in range(0, self.rect.width, sprite_w):
            win.blit(self.image, (self.rect.x + x - offset_x, self.rect.y))

    def up(self, block_size=96):
        """
        Appelé uniquement pour current_level >= 1.
        Paliers :
          1-4 erreurs  → montée cosmétique de 18px à chaque fois (visible mais pas mortelle)
          5  erreurs   → palier 1 : atteint la zone basse (HEIGHT - 3*block_size)
          6-9 erreurs  → montée intermédiaire de 14px à chaque fois
          10 erreurs   → palier 2 : atteint le niveau du spawn (HEIGHT - 2*block_size)
        """
        self.mistakes += 1
        self.flash_timer = 45  # déclenche le flash visuel

        if self.mistakes == 5:
            # Palier 1 : inonde la zone basse (un bloc sous le spawn)
            self.target_y = HEIGHT - block_size * 3 - 50
        elif self.mistakes == 10:
            # Palier 2 : atteint le niveau du spawn → danger maximal
            self.target_y = HEIGHT - block_size * 2 - 50
        elif self.mistakes < 5:
            # Montée cosmétique progressive avant le palier 5
            self.target_y = self.base_y - 18
        else:
            # Entre 6 et 9 : montée intermédiaire entre les deux paliers
            self.target_y = self.target_y - 14