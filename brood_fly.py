import pygame
import math
import random
from enemy_ai_utils import has_line_of_sight
from enemy import Enemy

# ---------------------- AUDIO ----------------------
try:
    FLY_BUZZ = pygame.mixer.Sound("assets/audio/flyBuzz.wav")
    FLY_BUZZ.set_volume(0.1)
except:
    FLY_BUZZ = None


# ================================================================
#  UTILITY: LOAD ANIMATION FRAMES
# ================================================================

def load_animation(prefix, count, scale=None):
    frames = []
    for i in range(count):
        path = f"assets/fly/{prefix}_{i}.png"
        try:
            img = pygame.image.load(path).convert_alpha()
            if scale:
                img = pygame.transform.scale(img, scale)
            frames.append(img)
        except:
            print(f"Warning: missing animation file {path}")
    return frames


# ================================================================
#  ACID PROJECTILE
# ================================================================

class AcidProjectile(pygame.sprite.Sprite):
    """Projectile spat by the BroodFly."""

    def __init__(self, x, y, target_pos, speed=360, lifetime=3.0, damage=8):
        super().__init__()

        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (100, 255, 80), (5, 5), 5)
        self.rect = self.image.get_rect(center=(x, y))

        dx, dy = target_pos[0] - x, target_pos[1] - y
        dist = math.hypot(dx, dy)
        self.vel = pygame.Vector2((dx / dist) * speed, (dy / dist) * speed) if dist else pygame.Vector2()
        self.timer = lifetime
        self.damage = damage

    def update(self, dt, player=None, walls=None):
        self.rect.x += self.vel.x * dt
        self.rect.y += self.vel.y * dt

        self.timer -= dt
        if self.timer <= 0:
            self.kill()
            return

        if player and self.rect.colliderect(player.rect):
            player.take_damage(self.damage)
            self.kill()
            return

        if walls and any(self.rect.colliderect(w) for w in walls):
            self.kill()


# ================================================================
#  BROOD FLY (MAIN ENEMY)
# ================================================================

class BroodFly(Enemy):

    DETECTION_RANGE = 600
    MIN_ATTACK_RANGE = 300
    MAX_ATTACK_RANGE = 500
    SHOOT_COOLDOWN = 2.2
    WINDUP_TIME = 0.5
    WANDER_INTERVAL = (1.0, 2.2)

    def __init__(self, x, y, scale=1.8):
        super().__init__(x, y, health=100, speed=120)

        # Hitbox vs sprite size
        self.hitbox_size = 40
        self.sprite_size = int(48 * scale)
        self.visual_scale = scale
        self.rect = pygame.Rect(x - 20, y - 20, 40, 40)

        # Animations
        size = (self.sprite_size, self.sprite_size)
        self.animations = {
            "idle":   load_animation("flyIdle",   4, size),
            "attack": load_animation("flyAttack", 4, size),
            "death":  load_animation("flyDeath",  6, size),
        }

        self.image = self.animations["idle"][0]
        self.facing_left = False
        self.frame_index = 0
        self.anim_timer = 0

        # Buzz channel
        self.buzz = pygame.mixer.find_channel(True)
        if FLY_BUZZ and self.buzz:
            self.buzz.play(FLY_BUZZ, loops=-1)
            self.buzz.set_volume(0)

        # Combat
        self.projectiles = pygame.sprite.Group()
        self.attack_cooldown = 0

        # Wandering
        self._choose_new_wander_dir()

        # Dying state
        self.dying = False
        self.spawned_larvae = False
        self.death_timer = 0
        self.death_speed = 0.12

    # ---------------------------------------------------------
    def _choose_new_wander_dir(self):
        """Pick a random wandering direction."""
        angle = random.uniform(0, math.tau)
        self.wander_dir = pygame.Vector2(math.cos(angle), math.sin(angle))
        self.wander_speed = random.uniform(self.speed * 0.2, self.speed * 0.4)
        self.wander_timer = random.uniform(*self.WANDER_INTERVAL)

    # ---------------------------------------------------------
    def disable_collision(self):
        self.rect.size = (1, 1)

    # ---------------------------------------------------------
    def is_alive(self):
        if self.dying and not self.spawned_larvae:
            return True
        return self.health > 0

    # ---------------------------------------------------------
    def take_damage(self, amount, player):
        super().take_damage(amount, player)

        if self.health <= 0 and not self.dying:
            self.dying = True
            self.frame_index = 0
            self.anim_timer = 0
            self.disable_collision()

    # ---------------------------------------------------------
    def spawn_larva(self, enemies, count=4, walls=None):
        from brood_fly import Larva   # avoid circular import

        enemy_size = 24
        radius = 50

        for _ in range(count):
            for _ in range(10):  # max attempts
                angle = random.uniform(0, math.tau)
                dist = random.uniform(20, radius)
                sx = self.x + math.cos(angle) * dist
                sy = self.y + math.sin(angle) * dist

                rect = pygame.Rect(sx - 12, sy - 12, enemy_size, enemy_size)
                if walls and any(rect.colliderect(w) for w in walls):
                    continue

                enemies.append(Larva(sx, sy))
                break

    # ---------------------------------------------------------
    def animate(self, dt):
        frames = self.animations["death"] if self.dying else self.animations["idle"]
        self.anim_timer += dt

        if self.anim_timer >= 0.15:
            self.anim_timer = 0
            if self.dying:
                self.frame_index = min(self.frame_index + 1, len(frames) - 1)
            else:
                self.frame_index = (self.frame_index + 1) % len(frames)

        frame = frames[self.frame_index]
        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)
        self.image = frame

    # ---------------------------------------------------------
    def update(self, dt, player=None, walls=None, enemies=None, barricades=None, **kw):

        # Buzz volume
        if player and self.buzz:
            dist = pygame.Vector2(self.x - player.x, self.y - player.y).length()
            volume = max(0.0, min(1, 1 - dist / 600))
            self.buzz.set_volume(volume * 0.4)

        # Death animation + larvae spawn
        if self.dying:
            self.animate(dt)
            self.death_timer += dt

            if self.frame_index == len(self.animations["death"]) - 1 and not self.spawned_larvae:
                if enemies is not None:
                    self.spawn_larva(enemies, walls=walls)
                self.spawned_larvae = True

            return

        super().update(dt, player=player, walls=walls, barricades=barricades)
        self.projectiles.update(dt, player, walls)

        # ======================================================
        # WANDERING MOVEMENT
        # ======================================================
        self.wander_timer -= dt
        if self.wander_timer <= 0:
            self._choose_new_wander_dir()

        drift = self.wander_dir + pygame.Vector2(random.uniform(-0.5, 0.5),
                                                 random.uniform(-0.5, 0.5))
        drift = drift.normalize()

        new_x = self.x + drift.x * self.wander_speed * dt
        new_y = self.y + drift.y * self.wander_speed * dt

        obstacles = list(walls or [])
        if barricades:
            obstacles += [b.rect for b in barricades if b.active]

        # X movement
        test = pygame.Rect(new_x - 20, self.y - 20, 40, 40)
        if not any(test.colliderect(o) for o in obstacles):
            self.x = new_x

        # Y movement
        test = pygame.Rect(self.x - 20, new_y - 20, 40, 40)
        if not any(test.colliderect(o) for o in obstacles):
            self.y = new_y

        self.rect.center = (self.x, self.y)

        # ======================================================
        # SHOOTING
        # ======================================================
        dx, dy = player.x - self.x, player.y - self.y
        dist = math.hypot(dx, dy)
        can_see = has_line_of_sight(self, player, walls)

        if can_see and dist < self.DETECTION_RANGE:
            self.attack_cooldown -= dt
            if self.attack_cooldown <= 0:
                self.projectiles.add(AcidProjectile(self.x, self.y, player.rect.center))
                self.attack_cooldown = self.SHOOT_COOLDOWN

        # Small hover bob
        self.y += math.sin(pygame.time.get_ticks() * 0.005 + self.x * 0.01) * 0.4
        self.rect.centery = self.y

        self.animate(dt)



# ================================================================
#  LARVA (GROUND MELEE ENEMY)
# ================================================================

class Larva(Enemy):

    DETECT_RANGE = 100
    WINDUP_TIME = 0.75
    LUNGE_SPEED = 200
    DAMAGE = 4

    def __init__(self, x, y, scale=1.6):
        super().__init__(x, y, health=20, speed=100)

        self.hitbox_size = 20
        self.sprite_size = int(24 * scale)
        self.rect = pygame.Rect(x - 10, y - 10, 20, 20)

        # Attack state
        self.lunging = False
        self.windup_timer = 0
        self.lunge_dir = pygame.Vector2()

        # Animations
        size = (self.sprite_size, self.sprite_size)
        self.animations = {
            "idle":  load_animation("larvaIdle", 6, size),
            "move":  load_animation("larvaMove", 6, size),
            "dmg":   load_animation("larvaDmg", 6, size),
            "death": load_animation("larvaDeath", 6, size),
        }

        self.state = "move"
        self.frame_index = 0
        self.anim_speed = 0.15
        self.anim_timer = 0
        self.facing_left = False

        # Death state
        self.dying = False
        self.death_done = False

    # ---------------------------------------------------------
    def disable_collision(self):
        self.rect.size = (1, 1)

    def is_alive(self):
        return (self.dying and not self.death_done) or self.health > 0

    def take_damage(self, amt, player):
        super().take_damage(amt, player)

        if self.health <= 0 and not self.dying:
            self.dying = True
            self.state = "death"
            self.frame_index = 0
            self.anim_timer = 0
            self.disable_collision()

        elif not self.dying:
            self.state = "dmg"
            self.frame_index = 0
            self.anim_timer = 0

    # ---------------------------------------------------------
    def animate(self, dt):
        frames = self.animations[self.state]
        self.anim_timer += dt

        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0

            if self.dying:
                if self.frame_index < len(frames) - 1:
                    self.frame_index += 1
                else:
                    self.death_done = True
            else:
                self.frame_index = (self.frame_index + 1) % len(frames)

        frame = frames[self.frame_index]
        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)
        self.image = frame

    # ---------------------------------------------------------
    def update(self, dt, player=None, walls=None, barricades=None, **kw):

        if self.dying:
            self.animate(dt)
            return

        dx, dy = player.x - self.x, player.y - self.y
        dist = math.hypot(dx, dy)

        # WINDUP
        if not self.lunging and dist < self.DETECT_RANGE and self.windup_timer <= 0:
            self.state = "idle"
            self.windup_timer = self.WINDUP_TIME
            self.lunge_dir = pygame.Vector2(dx, dy).normalize()
            self.lunging = True

        # Countdown
        if self.lunging and self.windup_timer > 0:
            self.windup_timer -= dt

        # LUNGE
        if self.lunging and self.windup_timer <= 0:
            self.x += self.lunge_dir.x * self.LUNGE_SPEED * dt
            self.y += self.lunge_dir.y * self.LUNGE_SPEED * dt
            self.rect.center = (self.x, self.y)

            # Hit player
            if self.rect.colliderect(player.rect):
                player.take_damage(self.DAMAGE)
                self.take_damage(self.health, player)
                return

            # Hit walls
            obstacles = list(walls or [])
            if barricades:
                obstacles += [b.rect for b in barricades if b.active]

            if any(self.rect.colliderect(o) for o in obstacles):
                self.lunging = False
                self.state = "idle"
                return

        # NORMAL CHASE
        if not self.lunging:
            super().update(dt, player=player, walls=walls, barricades=barricades)

        self.animate(dt)
