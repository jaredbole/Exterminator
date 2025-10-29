# main.py
import math
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pygame

# ---------------------------
# Settings & simple helpers
# ---------------------------
WIDTH, HEIGHT = 1200, 800
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 30, 30)
GREEN = (30, 200, 30)


def load_image_stub(size: Tuple[int, int], color=(100, 100, 100)) -> pygame.Surface:
    """Placeholder for images — returns a colored rect surface."""
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill(color)
    return surf


# ---------------------------
# Base classes
# ---------------------------
class GameObject(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float, image: Optional[pygame.Surface] = None):
        super().__init__()
        self.original_image = image if image else load_image_stub((40, 40))
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.angle = 0.0  # degrees

    def update(self, dt: float):
        self.pos += self.vel * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))


# ---------------------------
# Projectile / Bullet
# ---------------------------
@dataclass
class BulletStats:
    speed: float = 900.0
    damage: int = 10
    lifetime: float = 2.0  # seconds


class Bullet(GameObject):
    def __init__(self, x: float, y: float, direction: pygame.Vector2, stats: BulletStats):
        image = load_image_stub((8, 16), color=(220, 220, 30))
        super().__init__(x, y, image=image)
        self.direction = direction.normalize()
        self.speed = stats.speed
        self.damage = stats.damage
        self.lifetime = stats.lifetime
        self.age = 0.0
        # rotate sprite so it points along direction
        self.angle = math.degrees(math.atan2(-self.direction.y, self.direction.x)) - 90
        self.rotate_image(self.angle)

    def rotate_image(self, angle):
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, dt: float):
        self.pos += self.direction * self.speed * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.age += dt
        if self.age >= self.lifetime:
            self.kill()


# ---------------------------
# Weapon system
# ---------------------------
class Weapon:
    def __init__(self, name: str, bullet_stats: BulletStats, cooldown: float):
        self.name = name
        self.bullet_stats = bullet_stats
        self.cooldown = cooldown
        self._cooldown_timer = 0.0

    def can_fire(self) -> bool:
        return self._cooldown_timer <= 0.0

    def update(self, dt: float):
        if self._cooldown_timer > 0.0:
            self._cooldown_timer -= dt

    def fire(self, x: float, y: float, aim_dir: pygame.Vector2, bullet_group: pygame.sprite.Group):
        if not self.can_fire():
            return None
        self._cooldown_timer = self.cooldown
        bullet = Bullet(x, y, aim_dir, self.bullet_stats)
        bullet_group.add(bullet)
        return bullet


# ---------------------------
# Player (Mech)
# ---------------------------
class Player(GameObject):
    def __init__(self, x: float, y: float):
        image = load_image_stub((48, 56), color=(50, 120, 200))
        super().__init__(x, y, image=image)
        self.speed = 320.0
        self.health = 100
        self.max_health = 100

        # weapons / inventory
        self.weapon_slots: List[Optional[Weapon]] = [None] * 4
        # basic starter weapon in slot 0
        self.weapon_slots[0] = Weapon("Rifle", BulletStats(speed=1000, damage=12, lifetime=1.8), cooldown=0.18)
        self.active_slot = 0

    def handle_input(self, keys: pygame.key.ScancodeWrapper, dt: float):
        move = pygame.Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move.x += 1
        if move.length_squared() > 0:
            move = move.normalize()
        self.vel = move * self.speed

    def update(self, dt: float):
        # update movement
        super().update(dt)
        # bound to screen
        self.pos.x = max(0, min(WIDTH, self.pos.x))
        self.pos.y = max(0, min(HEIGHT, self.pos.y))
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        # update active weapon cooldowns
        for w in self.weapon_slots:
            if w:
                w.update(dt)

    def take_damage(self, amount: int):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            # TODO: dispatch death event
            print("Player died (placeholder)")

    def heal(self, amount: int):
        self.health = min(self.max_health, self.health + amount)


# ---------------------------
# Enemy skeleton
# ---------------------------
class Enemy(GameObject):
    def __init__(self, x: float, y: float, hp=30):
        image = load_image_stub((40, 40), color=(200, 80, 80))
        super().__init__(x, y, image=image)
        self.health = hp
        self.speed = 100.0

    def update(self, dt: float):
        # Basic placeholder behavior: stand still or add AI here
        super().update(dt)

    def take_damage(self, amount: int):
        self.health -= amount
        if self.health <= 0:
            self.kill()


# ---------------------------
# UI: Health bar
# ---------------------------
class HealthBar:
    def __init__(self, target: Player, size=(200, 18), offset=(0, -40)):
        self.target = target
        self.size = size
        self.offset = pygame.Vector2(offset)

    def draw(self, surface: pygame.Surface):
        x = int(self.target.pos.x + self.offset.x - self.size[0] // 2)
        y = int(self.target.pos.y + self.offset.y)
        # background
        pygame.draw.rect(surface, (60, 60, 60), (x, y, self.size[0], self.size[1]), border_radius=4)
        # foreground
        ratio = max(0.0, self.target.health / self.target.max_health)
        fg_w = int(self.size[0] * ratio)
        pygame.draw.rect(surface, GREEN, (x + 2, y + 2, fg_w - 4 if fg_w > 4 else 0, self.size[1] - 4), border_radius=3)
        # border
        pygame.draw.rect(surface, BLACK, (x, y, self.size[0], self.size[1]), 2, border_radius=4)


# ---------------------------
# Main Game class
# ---------------------------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Top-Down Mech — Prototype")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()

        # Player
        self.player = Player(WIDTH // 2, HEIGHT // 2)
        self.all_sprites.add(self.player)
        self.health_bar = HealthBar(self.player)

    def spawn_enemy(self, pos):
        enemy = Enemy(pos[0], pos[1])
        self.enemies.add(enemy)
        self.all_sprites.add(enemy)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # seconds per frame
            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.shoot()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:  # spawn test enemy
                    self.spawn_enemy((WIDTH // 2, HEIGHT // 3))
                elif pygame.K_1 <= event.key <= pygame.K_4:
                    self.player.active_slot = event.key - pygame.K_1

    def shoot(self):
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        aim_dir = mouse_pos - self.player.pos
        if aim_dir.length_squared() > 0:
            weapon = self.player.weapon_slots[self.player.active_slot]
            if weapon:
                bullet = weapon.fire(
                    self.player.pos.x,
                    self.player.pos.y,
                    aim_dir,
                    self.bullets,
                )
                if bullet:
                    self.all_sprites.add(bullet)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys, dt)

        self.all_sprites.update(dt)

        # Bullet collisions
        for bullet in self.bullets:
            hits = pygame.sprite.spritecollide(bullet, self.enemies, False)
            for enemy in hits:
                enemy.take_damage(bullet.damage)
                bullet.kill()

    def draw(self):
        self.screen.fill((20, 20, 20))
        self.all_sprites.draw(self.screen)
        self.health_bar.draw(self.screen)
        pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()

