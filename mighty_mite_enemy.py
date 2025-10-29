import pygame
import math
import random
from enemy import Enemy

class MightyMite(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, health=400)
        self.x = x
        self.y = y
        self.speed = 70
        self.charge_speed = 500
        self.state = "idle"
        self.size = 50

        # Detection/attack properties
        self.detection_radius = 700
        self.charge_range = 300
        self.charge_timer = 0
        self.recover_timer = 0
        self.charge_duration = 1
        self.prep_time = 0.5
        self.recover_time = 1.5

        # Visual setup
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill((120, 100, 60))  # dark brown/gray
        self.rect = self.image.get_rect(center=(x, y))

        # Movement
        self.vel_x = 0
        self.vel_y = 0
        self.direction = random.uniform(0, 2 * math.pi)

    def update(self, dt, player):
        player_dx = player.rect.centerx - self.x
        player_dy = player.rect.centery - self.y
        distance_to_player = math.hypot(player_dx, player_dy)

        if self.state == "idle":
            self.wander(dt)
            if distance_to_player < self.detection_radius:
                self.state = "chase"

        elif self.state == "chase":
            if distance_to_player > self.detection_radius * 1.5:
                self.state = "idle"
            elif distance_to_player < self.charge_range:
                self.state = "charging_prep"
                self.charge_timer = 0
            else:
                self.move_toward(player.rect.center, self.speed, dt)

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
            self.x += self.vel_x * dt
            self.y += self.vel_y * dt
            self.charge_timer += dt
            if self.charge_timer >= self.charge_duration:
                self.state = "recover"
                self.charge_timer = 0
                self.vel_x = self.vel_y = 0

        elif self.state == "recover":
            self.recover_timer += dt
            if self.recover_timer >= self.recover_time:
                self.recover_timer = 0
                if distance_to_player < self.detection_radius:
                    self.state = "chase"
                else:
                    self.state = "idle"

        # Sync visual position
        self.rect.center = (self.x, self.y)
        self.update_burning(dt)

    def wander(self, dt):
        # Random slow wandering behavior
        if random.random() < 0.01:
            self.direction = random.uniform(0, 2 * math.pi)
        self.x += math.cos(self.direction) * self.speed * 0.25 * dt
        self.y += math.sin(self.direction) * self.speed * 0.25 * dt
        self.rect.center = (self.x, self.y)

    def move_toward(self, target_pos, speed, dt):
        dx = target_pos[0] - self.x
        dy = target_pos[1] - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            dx /= dist
            dy /= dist
            self.x += dx * speed * dt
            self.y += dy * speed * dt
            self.rect.center = (self.x, self.y)
