import pygame
import math
from rifle import Rifle
from minigun import Minigun
from plasma_cannon import PlasmaCannon, PlasmaBlob
from flamethrower import Flamethrower

class Player:
    def __init__(self, x=400, y=300):
        self.max_health = 100
        self.health = self.max_health 
        self.x = x
        self.y = y
        self.size = 30
        self.rect = pygame.Rect(self.x - self.size / 2, self.y - self.size / 2, self.size, self.size)
        self.speed = 300
        self.bullets = []
        self.weapons = [Rifle(), Minigun(), PlasmaCannon(), Flamethrower()]
        self.current_weapon_index = 0
        self.current_weapon = self.weapons[self.current_weapon_index]
        
        # Weapon switch cooldown
        self.switch_cooldown = 0.3
        self.switch_timer = 0

        # Camera offset (used later for drawing)
        self.camera_x = 0
        self.camera_y = 0

    # ⬇️ Updated to handle map boundaries and camera
    def handle_input(self, dt, keys, level_width, level_height):
        if self.switch_timer > 0:
            self.switch_timer -= dt

        dx, dy = 0, 0
        if keys[pygame.K_w]:
            dy -= self.speed * dt
        if keys[pygame.K_s]:
            dy += self.speed * dt
        if keys[pygame.K_a]:
            dx -= self.speed * dt
        if keys[pygame.K_d]:
            dx += self.speed * dt

        # Update position
        self.x += dx
        self.y += dy

        # Clamp to level boundaries
        self.x = max(self.size / 2, min(level_width - self.size / 2, self.x))
        self.y = max(self.size / 2, min(level_height - self.size / 2, self.y))

        # Camera centers on player
        self.camera_x = self.x - 600  # half of window width (1200 / 2)
        self.camera_y = self.y - 400  # half of window height (800 / 2)

        # Keep camera inside the level
        self.camera_x = max(0, min(self.camera_x, level_width - 1200))
        self.camera_y = max(0, min(self.camera_y, level_height - 800))

        # Weapon switching
        if keys[pygame.K_q] and self.switch_timer <= 0:
            self.switch_weapon()
            self.switch_timer = self.switch_cooldown

        # Face toward mouse (screen space)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_mouse_x = mouse_x + self.camera_x
        world_mouse_y = mouse_y + self.camera_y
        self.facing_angle = math.atan2(world_mouse_y - self.y, world_mouse_x - self.x)

    def switch_weapon(self):
        self.current_weapon_index = (self.current_weapon_index + 1) % len(self.weapons)
        self.current_weapon = self.weapons[self.current_weapon_index]
        print(f"Switched to {self.current_weapon.__class__.__name__}")

    def shoot(self, mouse_pos):
        self.current_weapon.fire(self.x, self.y, mouse_pos, self.bullets)

    def update(self, dt, puddles):
        self.current_weapon.update(dt)
        self.rect.center = (self.x, self.y)

        for bullet in self.bullets:
            if isinstance(bullet, PlasmaBlob):
                bullet.update(dt, puddles)
            else:
                bullet.update(dt)

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        print(f"Player took {amount} damage! Health: {self.health}/{self.max_health}")

    def draw(self, surface):
        # Adjust draw position for camera offset
        screen_x = self.x - self.camera_x
        screen_y = self.y - self.camera_y

        pygame.draw.rect(surface, (0, 255, 0), (screen_x - 15, screen_y - 15, 30, 30))

        # Health bar
        bar_width, bar_height = 60, 8
        bar_x = screen_x - bar_width / 2
        bar_y = screen_y - 40

        pygame.draw.rect(surface, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, (0, 255, 0),
                         (bar_x, bar_y, bar_width * (self.health / self.max_health), bar_height))

        # Bullets (camera offset)
        for bullet in self.bullets:
            bullet.draw(surface, self.camera_x, self.camera_y)
