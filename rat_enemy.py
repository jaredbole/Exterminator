# rat_enemy.py
import pygame
import math
import random
from enemy import Enemy

class RatEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, health=30)
        self.x = x
        self.y = y
        self.speed = 180.0
        self.size = 20
        self.damage = 5

        # --- Load directional frames ---
        self.animations = {d: [] for d in range(4)}  # 0=N, 1=E, 2=S, 3=W
        for direction in range(4):
            for frame in range(3):
                img = pygame.image.load(f"assets/rat/rat_{direction}{frame}.png").convert_alpha()
                self.animations[direction].append(img)

        self.direction = random.choice([0, 1, 2, 3])  # random initial facing
        self.current_frame = 0
        self.frame_timer = 0
        self.frame_speed = 0.15  # seconds per frame
        self.image = self.animations[self.direction][self.current_frame]
        self.rect = self.image.get_rect(center=(x, y))

        # AI behavior states
        self.state = "wander"
        self.timer = 0
        self.attack_cooldown = 0.0

        # Behavior tuning
        self.detection_range = 300
        self.attack_range = 45
        self.windup_time = 0.35
        self.attack_duration = 0.25
        self.recover_time = 0.6
        self.lunge_speed = 280

        # Movement vector
        self.vel_x = 0
        self.vel_y = 0
        # Wander movement
        self.wander_dir = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
        self.wander_timer = random.uniform(1.5, 3.0)
        
        self.has_attacked = False
        
    # --- Direction calculation ---
    def get_direction_from_angle(self, dx, dy):
        angle = math.degrees(math.atan2(-dy, dx))  # note: pygame y-axis is flipped
        if -45 <= angle < 45:
            return 1  # East
        elif 45 <= angle < 135:
            return 0  # North
        elif -135 <= angle < -45:
            return 2  # South
        else:
            return 3  # West

    def distance_to(self, target):
        dx = target.rect.centerx - self.rect.centerx
        dy = target.rect.centery - self.rect.centery
        return math.hypot(dx, dy)

    def move_toward(self, target_pos, speed, dt):
        dx = target_pos[0] - self.rect.centerx
        dy = target_pos[1] - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist != 0:
            dx /= dist
            dy /= dist
        self.rect.x += dx * speed * dt
        self.x += dx * speed * dt
        self.rect.y += dy * speed * dt
        self.y += dy * speed * dt
        # Update facing direction
        self.direction = self.get_direction_from_angle(dx, dy)
        
    def wander(self, dt):
        self.rect.x += self.wander_dir.x * self.speed * 0.4 * dt
        self.rect.y += self.wander_dir.y * self.speed * 0.4 * dt
        self.x = self.rect.centerx
        self.y = self.rect.centery
        self.wander_timer -= dt
        if self.wander_timer <= 0:
            self.wander_dir = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
            self.wander_timer = random.uniform(1.5, 3.0)
        self.direction = self.get_direction_from_angle(self.wander_dir.x, self.wander_dir.y)

    def animate(self, dt):
        self.frame_timer += dt
        if self.frame_timer >= self.frame_speed:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.animations[self.direction])
            self.image = self.animations[self.direction][self.current_frame]

    def stop_movement(self):
        self.vel_x = 0
        self.vel_y = 0

    def update(self, dt, player):
        dist = self.distance_to(player)

        # --- STATE MACHINE ---
        if self.state == "wander":
            self.wander(dt)
            if dist < self.detection_range:
                self.state = "chase"

        elif self.state == "chase":
            # Move toward player, but stop if in range
            if dist > self.attack_range:
                self.move_toward(player.rect.center, self.speed, dt)
            else:
                if self.attack_cooldown <= 0:
                    self.state = "windup"
                    self.timer = self.windup_time

        elif self.state == "windup":
            self.stop_movement()
            self.timer -= dt
            if self.timer <= 0:
                self.state = "attack"
                self.timer = self.attack_duration
                self.has_attacked = False

        elif self.state == "attack":
            # Lunge forward
            self.move_toward(player.rect.center, self.lunge_speed, dt)

            # Check for collision
            if not self.has_attacked and self.rect.colliderect(player.rect):
                player.take_damage(self.damage)
                self.has_attacked = True

            self.timer -= dt
            if self.timer <= 0:
                self.state = "recover"
                self.timer = self.recover_time
                self.attack_cooldown = 0.8

        elif self.state == "recover":
            self.stop_movement()
            self.timer -= dt
            if self.timer <= 0:
                if dist < self.detection_range:
                    self.state = "chase"
                else:
                    self.state = "wander"

        # Cooldown decrement
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        self.animate(dt)
        
        self.update_burning(dt)
