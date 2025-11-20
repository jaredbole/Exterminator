import pygame
import math
import random
from enemy import Enemy


class MightyMite(Enemy):
    """Tanky enemy that charges at the player once within range."""

    def __init__(self, x, y):
        super().__init__(x, y, health=400)
        self.speed = 70
        self.charge_speed = 500
        self.state = "idle"
        self.size = 50

        # Detection and attack properties
        self.detection_radius = 700
        self.charge_range = 300
        self.charge_timer = 0
        self.recover_timer = 0
        self.charge_duration = 1.0
        self.prep_time = 0.5
        self.recover_time = 1.5

        # Visual setup
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill((120, 100, 60))  # dark brown/gray
        self.rect = self.image.get_rect(center=(x, y))

        # Movement state
        self.vel_x = 0
        self.vel_y = 0
        self.direction = random.uniform(0, 2 * math.pi)

    def update(self, dt, player=None, walls=None, enemies=None, barricades=None, **kwargs):
        """Handle Mighty Mite AI states while using shared collision + LOS."""
        # Shared base update for wall + barricade collisions
        super().update(dt, player=player, walls=walls, barricades=barricades)

        player_dx = player.rect.centerx - self.x
        player_dy = player.rect.centery - self.y
        distance_to_player = math.hypot(player_dx, player_dy)

        # --- STATE MACHINE ---
        if self.state == "idle":
            self.wander(dt, walls, barricades)
            if distance_to_player < self.detection_radius:
                self.state = "chase"

        elif self.state == "chase":
            if distance_to_player > self.detection_radius * 1.5:
                self.state = "idle"
            elif distance_to_player < self.charge_range:
                self.state = "charging_prep"
                self.charge_timer = 0
            else:
                self.move_toward_point(player.rect.center, self.speed, dt, walls, barricades)

        elif self.state == "charging_prep":
            self.charge_timer += dt
            if self.charge_timer >= self.prep_time:
                self.state = "charge_attack"
                self.charge_timer = 0
                # Lock in charge direction
                angle = math.atan2(player_dy, player_dx)
                self.vel_x = math.cos(angle) * self.charge_speed
                self.vel_y = math.sin(angle) * self.charge_speed

        elif self.state == "charge_attack":
            # Predict new position
            new_x = self.x + self.vel_x * dt
            new_y = self.y + self.vel_y * dt

            obstacles = list(walls or [])
            if barricades:
                obstacles += [b.rect for b in barricades if getattr(b, "active", False)]

            rect_x = pygame.Rect(new_x - self.size / 2, self.y - self.size / 2, self.size, self.size)
            rect_y = pygame.Rect(self.x - self.size / 2, new_y - self.size / 2, self.size, self.size)

            # Simple collision stop if charge hits a wall/barricade
            blocked = any(rect_x.colliderect(o) or rect_y.colliderect(o) for o in obstacles)
            if not blocked:
                self.x = new_x
                self.y = new_y
            else:
                # Stop early on impact
                self.state = "recover"
                self.charge_timer = 0
                self.vel_x = self.vel_y = 0

            self.charge_timer += dt
            if self.charge_timer >= self.charge_duration:
                self.state = "recover"
                self.charge_timer = 0
                self.vel_x = self.vel_y = 0

            # Damage player if collided during charge
            if self.rect.colliderect(player.rect):
                player.take_damage(25)  # heavy damage
                self.state = "recover"
                self.vel_x = self.vel_y = 0

        elif self.state == "recover":
            self.recover_timer += dt
            if self.recover_timer >= self.recover_time:
                self.recover_timer = 0
                if distance_to_player < self.detection_radius:
                    self.state = "chase"
                else:
                    self.state = "idle"

        # Update visual + burning animation
        self.rect.center = (self.x, self.y)
        self.update_burning(dt)

    def wander(self, dt, walls=None, barricades=None):
        """Slow random wandering behavior, respecting walls/barricades."""
        if random.random() < 0.01:
            self.direction = random.uniform(0, 2 * math.pi)

        dx = math.cos(self.direction)
        dy = math.sin(self.direction)
        new_x = self.x + dx * self.speed * 0.25 * dt
        new_y = self.y + dy * self.speed * 0.25 * dt

        obstacles = list(walls or [])
        if barricades:
            obstacles += [b.rect for b in barricades if getattr(b, "active", False)]

        rect_x = pygame.Rect(new_x - self.size / 2, self.y - self.size / 2, self.size, self.size)
        rect_y = pygame.Rect(self.x - self.size / 2, new_y - self.size / 2, self.size, self.size)
        if not any(rect_x.colliderect(o) for o in obstacles):
            self.x = new_x
        if not any(rect_y.colliderect(o) for o in obstacles):
            self.y = new_y

        self.rect.center = (self.x, self.y)

    def move_toward_point(self, target_pos, speed, dt, walls=None, barricades=None):
        """Move toward a point respecting unified obstacle system."""
        dx = target_pos[0] - self.x
        dy = target_pos[1] - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        dx /= dist
        dy /= dist

        new_x = self.x + dx * speed * dt
        new_y = self.y + dy * speed * dt

        obstacles = list(walls or [])
        if barricades:
            obstacles += [b.rect for b in barricades if getattr(b, "active", False)]

        rect_x = pygame.Rect(new_x - self.size / 2, self.y - self.size / 2, self.size, self.size)
        rect_y = pygame.Rect(self.x - self.size / 2, new_y - self.size / 2, self.size, self.size)
        if not any(rect_x.colliderect(o) for o in obstacles):
            self.x = new_x
        if not any(rect_y.colliderect(o) for o in obstacles):
            self.y = new_y

        self.rect.center = (self.x, self.y)
