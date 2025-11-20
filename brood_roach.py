import pygame
import math
import random
from enemy import Enemy


class BroodRoach(Enemy):
    """Large roach that bursts into several small roachlings on death."""

    def __init__(self, x, y):
        super().__init__(x, y, health=120, speed=90.0)
        self.size = 40
        self.damage = 8
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill((100, 60, 30))  # dark brown shell
        self.rect = self.image.get_rect(center=(x, y))

        # Behavior control
        self.state = "wander"
        self.timer = 0
        self.attack_cooldown = 0.0

        # Wandering movement
        self.wander_dir = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
        self.wander_timer = random.uniform(1.5, 3.0)

        # Memory for chasing
        self.last_known_pos = None

        # Attack behavior
        self.detection_range = 400
        self.attack_range = 50
        self.windup_time = 0.4
        self.attack_duration = 0.35
        self.recover_time = 0.6
        self.lunge_speed = 160
        self.has_attacked = False
        self.spawned_babies = False
        
    def take_damage(self, amount):
        """Handle taking damage and spawn babies immediately on death."""
        super().take_damage(amount)

        # spawn immediately when health drops to zero
        if self.health <= 0 and not self.spawned_babies:
            # find enemies list from a reference if available
            enemies_list = getattr(self, "enemies_ref", None)
            if enemies_list is not None:
                print("BroodRoach died! Spawning babies...")
                self.spawn_babies(enemies_list)
            else:
                print("BroodRoach died but has no enemies_ref!")
            self.spawned_babies = True


    def distance_to(self, target):
        dx = target.rect.centerx - self.rect.centerx
        dy = target.rect.centery - self.rect.centery
        return math.hypot(dx, dy)

    def move_toward_point(self, target_pos, speed, dt, walls=None, barricades=None):
        """Basic directional move with inherited collision logic."""
        direction = pygame.Vector2(target_pos[0] - self.x, target_pos[1] - self.y)
        if direction.length_squared() == 0:
            return
        direction = direction.normalize()
        new_x = self.x + direction.x * speed * dt
        new_y = self.y + direction.y * speed * dt

        # Use unified obstacle list
        obstacles = list(walls or [])
        if barricades:
            obstacles += [b.rect for b in barricades if getattr(b, "active", False)]

        rect_x = pygame.Rect(new_x - self.size / 2, self.y - self.size / 2, self.size, self.size)
        if not any(rect_x.colliderect(o) for o in obstacles):
            self.x = new_x
        rect_y = pygame.Rect(self.x - self.size / 2, new_y - self.size / 2, self.size, self.size)
        if not any(rect_y.colliderect(o) for o in obstacles):
            self.y = new_y
        self.rect.center = (self.x, self.y)

    def wander(self, dt, walls=None, barricades=None):
        self.move_toward_point(
            (self.x + self.wander_dir.x * 40, self.y + self.wander_dir.y * 40),
            self.speed * 0.4,
            dt,
            walls,
            barricades,
        )
        self.wander_timer -= dt
        if self.wander_timer <= 0:
            self.wander_dir = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
            self.wander_timer = random.uniform(1.5, 3.0)

    def update(self, dt, player=None, walls=None, enemies=None, barricades=None, **kwargs):
        """Main AI state machine for BroodRoach, with shared movement handling."""
        # Run base Enemy logic for LOS + collision memory
        super().update(dt, player=player, walls=walls, barricades=barricades)
        self.enemies_ref = enemies
        if enemies is None:
            print("BroodRoach update called without enemies list!")


        dist = self.distance_to(player)
        can_see = True
        if hasattr(self, "last_known"):
            # the base class sets self.last_known when player is seen
            can_see = self.last_known is not None

        # --- STATE MACHINE ---
        if self.state == "wander":
            self.wander(dt, walls, barricades)
            if dist < self.detection_range and can_see:
                self.state = "chase"

        elif self.state == "chase":
            target = (player.x, player.y) if can_see else self.last_known_pos
            if not target:
                self.state = "wander"
            else:
                if dist > self.attack_range:
                    self.move_toward_point(target, self.speed, dt, walls, barricades)
                else:
                    if self.attack_cooldown <= 0:
                        self.state = "windup"
                        self.timer = self.windup_time

        elif self.state == "windup":
            self.timer -= dt
            if self.timer <= 0:
                self.state = "attack"
                self.timer = self.attack_duration
                self.has_attacked = False

        elif self.state == "attack":
            self.move_toward_point(player.rect.center, self.lunge_speed, dt, walls, barricades)
            if not self.has_attacked and self.rect.colliderect(player.rect):
                player.take_damage(self.damage)
                self.has_attacked = True

            self.timer -= dt
            if self.timer <= 0:
                self.state = "recover"
                self.timer = self.recover_time
                self.attack_cooldown = 1.0

        elif self.state == "recover":
            self.timer -= dt
            if self.timer <= 0:
                if dist < self.detection_range and can_see:
                    self.state = "chase"
                else:
                    self.state = "wander"

        # --- Burning animation + cooldown ---
        self.update_burning(dt)
        self.attack_cooldown = max(0, self.attack_cooldown - dt)

    def spawn_babies(self, enemies):
        """Spawns multiple small roachlings around the death location."""
        for _ in range(random.randint(4, 6)):
            offset_x = random.randint(-40, 40)
            offset_y = random.randint(-40, 40)
            enemies.append(Roachling(self.x + offset_x, self.y + offset_y))
            print("Spawned roachlings!", len(enemies))


class Roachling(Enemy):
    """Fast, weak, erratic roach that sometimes attacks or flees."""

    def __init__(self, x, y):
        super().__init__(x, y, health=15, speed=230.0)
        self.size = 15
        self.damage = 3
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill((150, 90, 45))  # lighter brown
        self.rect = self.image.get_rect(center=(x, y))

        # Behavior
        self.state = random.choice(["attack", "flee"])
        self.timer = random.uniform(1.0, 2.0)

    def distance_to(self, target):
        dx = target.rect.centerx - self.rect.centerx
        dy = target.rect.centery - self.rect.centery
        return math.hypot(dx, dy)

    def move_toward_point(self, target_pos, dt, walls=None, barricades=None):
        direction = pygame.Vector2(target_pos[0] - self.x, target_pos[1] - self.y)
        if direction.length_squared() == 0:
            return
        direction = direction.normalize()
        new_x = self.x + direction.x * self.speed * dt
        new_y = self.y + direction.y * self.speed * dt

        obstacles = list(walls or [])
        if barricades:
            obstacles += [b.rect for b in barricades if getattr(b, "active", False)]

        rect_x = pygame.Rect(new_x - self.size / 2, self.y - self.size / 2, self.size, self.size)
        if not any(rect_x.colliderect(o) for o in obstacles):
            self.x = new_x
        rect_y = pygame.Rect(self.x - self.size / 2, new_y - self.size / 2, self.size, self.size)
        if not any(rect_y.colliderect(o) for o in obstacles):
            self.y = new_y
        self.rect.center = (self.x, self.y)

    def move_away(self, target_pos, dt, walls=None, barricades=None):
        direction = pygame.Vector2(self.x - target_pos[0], self.y - target_pos[1])
        if direction.length_squared() == 0:
            return
        direction = direction.normalize()
        new_x = self.x + direction.x * self.speed * dt
        new_y = self.y + direction.y * self.speed * dt

        obstacles = list(walls or [])
        if barricades:
            obstacles += [b.rect for b in barricades if getattr(b, "active", False)]

        rect_x = pygame.Rect(new_x - self.size / 2, self.y - self.size / 2, self.size, self.size)
        if not any(rect_x.colliderect(o) for o in obstacles):
            self.x = new_x
        rect_y = pygame.Rect(self.x - self.size / 2, new_y - self.size / 2, self.size, self.size)
        if not any(rect_y.colliderect(o) for o in obstacles):
            self.y = new_y
        self.rect.center = (self.x, self.y)

    def update(self, dt, player=None, walls=None, enemies=None, barricades=None, **kwargs):
        """Erratic flee/attack pattern."""
        self.update_burning(dt)

        self.timer -= dt
        if self.timer <= 0:
            # switch behavior every few seconds
            self.state = random.choice(["attack", "flee"])
            self.timer = random.uniform(1.0, 2.5)

        if self.state == "attack":
            self.move_toward_point(player.rect.center, dt, walls, barricades)
            if self.rect.colliderect(player.rect):
                player.take_damage(self.damage)
                self.state = "flee"
                self.timer = 1.0

        elif self.state == "flee":
            self.move_away(player.rect.center, dt, walls, barricades)

        self.update_burning(dt)
