import pygame
import math
from enemy import Enemy

class BedbugEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, health=100)
        self.x = x
        self.y = y
        self.speed = 180.0
        self.size = 30
        self.damage = 15

        # Visual setup
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill((150, 150, 50))
        self.rect = self.image.get_rect(center=(x, y))

        # --- AI behavior states ---
        self.state = "idle"
        self.timer = 0
        self.attack_cooldown = 0.0
        self.has_attacked = False

        # --- Behavior tuning ---
        self.detection_range = 1000
        self.attack_range = 45
        self.windup_time = 0.35
        self.attack_duration = 0.25
        self.recover_time = 0.6
        self.lunge_speed = 450
        self.vision_angle_threshold = 45  # degrees of player's vision cone
        self.safe_distance = 500          # distance to maintain while hiding
        
        # Hiding stats
        self.max_visible_distance = 200
        self.min_visible_distance = 100
        self.current_alpha = 255

        # Movement vector
        self.vel_x = 0
        self.vel_y = 0

    # ==========================
    # Utility & Behavior Helpers
    # ==========================

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
        self.rect.y += dy * speed * dt
        self.x, self.y = self.rect.center

    def stop_movement(self):
        self.vel_x = 0
        self.vel_y = 0

    def is_in_player_vision(self, player):
        """Check if this bedbug is within the player's vision cone."""
        player_dir = pygame.Vector2(math.cos(player.facing_angle), math.sin(player.facing_angle))
        to_enemy = pygame.Vector2(self.rect.centerx - player.rect.centerx,
                                  self.rect.centery - player.rect.centery)
        if to_enemy.length() == 0:
            return False
        to_enemy = to_enemy.normalize()

        angle_between = math.degrees(math.acos(max(-1, min(1, player_dir.dot(to_enemy)))))
        return angle_between < self.vision_angle_threshold

    # ==========================
    # State Machine
    # ==========================

    def update(self, dt, player):
        dist = self.distance_to(player)
        sees_player = self.is_in_player_vision(player)
        
        if dist <= self.min_visible_distance:
            alpha = 255
        elif dist >= self.max_visible_distance:
            alpha = 0
        else:
            alpha = int(255 * (1-(dist-self.min_visible_distance)/(self.max_visible_distance-self.min_visible_distance)))
            
        self.current_alpha = max(0, min(255,alpha))
        self.image.set_alpha(self.current_alpha)

        # --- STATE MACHINE ---
        if self.state == "idle":
            self.image.fill((150, 150, 50))
            if dist < self.detection_range:
                if sees_player:
                    self.state = "hide"
                else:
                    self.state = "stalk"

        elif self.state == "hide":
            # Move away from player while visible
            self.image.fill((80, 80, 80))
            if sees_player:
                if dist < self.safe_distance:
                # Move opposite direction from player
                    away_vec = pygame.Vector2(self.rect.centerx - player.rect.centerx,
                                              self.rect.centery - player.rect.centery)
                    if away_vec.length() > 0:
                        away_vec = away_vec.normalize()
                        self.rect.centerx += away_vec.x * self.speed * dt
                        self.rect.centery += away_vec.y * self.speed * dt
            else:
                # Once hidden, start stalking
                self.state = "stalk"

        elif self.state == "stalk":
            # Sneak toward player but only from behind
            self.image.fill((100, 100, 150))
            if sees_player:
                self.state = "hide"
            elif dist > self.attack_range * 2:
                self.move_toward(player.rect.center, self.speed * 0.7, dt)
            else:
                if self.attack_cooldown <= 0:
                    self.state = "windup"
                    self.timer = self.windup_time

        elif self.state == "windup":
            # Brief charge before lunge
            self.image.fill((200, 80, 50))
            self.stop_movement()
            self.timer -= dt
            if self.timer <= 0:
                self.state = "attack"
                self.timer = self.attack_duration
                self.has_attacked = False

        elif self.state == "attack":
            # Lunge forward
            self.image.fill((255, 50, 50))
            self.move_toward(player.rect.center, self.lunge_speed, dt)

            # Deal damage once
            if not self.has_attacked and self.rect.colliderect(player.rect):
                player.take_damage(self.damage)
                self.has_attacked = True

            self.timer -= dt
            if self.timer <= 0:
                self.state = "recover"
                self.timer = self.recover_time
                self.attack_cooldown = 1.2
                self.image.fill((150, 150, 50))

        elif self.state == "recover":
            self.stop_movement()
            self.timer -= dt
            if self.timer <= 0:
                if dist < self.detection_range:
                    self.state = "stalk"
                else:
                    self.state = "idle"

        # Cooldown timer
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        
        self.update_burning(dt)
