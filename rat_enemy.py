import pygame
import math
import random
from enemy import Enemy

# --- Load squeak sounds --
RAT_SQUEAK_SOUNDS = []
for i in range(5):
    path = f"assets/audio/ratSqueak_{i}.wav"
    try:
        snd = pygame.mixer.Sound(path)
        snd.set_volume(0.4)  # make it loud enough
        RAT_SQUEAK_SOUNDS.append(snd)
        print("Loaded rat squeak:", path)
    except Exception as e:
        print("FAILED to load:", path, e)
        RAT_SQUEAK_SOUNDS.append(None)



class RatEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, health=30)
        self.speed = 180.0
        self.size = 20
        self.damage = 5

        # --- Load directional frames ---
        self.animations = {d: [] for d in range(4)}  # 0=N, 1=E, 2=S, 3=W
        for direction in range(4):
            for frame in range(3):
                img = pygame.image.load(f"assets/rat/rat_{direction}{frame}.png").convert_alpha()
                self.animations[direction].append(img)

        self.direction = random.choice([0, 1, 2, 3])
        self.current_frame = 0
        self.frame_timer = 0
        self.frame_speed = 0.15
        self.image = self.animations[self.direction][self.current_frame]
        self.rect = self.image.get_rect(center=(x, y))

        # --- AI behavior states ---
        self.state = "wander"
        self.timer = 0
        self.attack_cooldown = 0.0

        # --- Behavior tuning ---
        self.detection_range = 300
        self.attack_range = 45
        self.windup_time = 0.35
        self.attack_duration = 0.25
        self.recover_time = 0.6
        self.lunge_speed = 280

        # --- Wandering ---
        self.wander_dir = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
        self.wander_timer = random.uniform(1.5, 3.0)
        self.has_attacked = False

        # --- Line-of-sight memory ---
        self.last_seen_player = None
        
        self.squeak_cooldown = random.uniform(2.0, 5.0)  # each rat has its own timer


    # --- Helpers ---
    def get_direction_from_angle(self, dx, dy):
        angle = math.degrees(math.atan2(dy, dx))
        if -45 <= angle < 45:
            return 1  # East
        elif 45 <= angle < 135:
            return 2  # South
        elif -135 <= angle < -45:
            return 0  # North
        else:
            return 3  # West

    def distance_to(self, target):
        dx = target.rect.centerx - self.rect.centerx
        dy = target.rect.centery - self.rect.centery
        return math.hypot(dx, dy)

    def move_toward_point(self, target_pos, speed, dt, walls=None, barricades=None):
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
        if not any(rect_x.colliderect(o) for o in obstacles):
            self.x = new_x
        rect_y = pygame.Rect(self.x - self.size / 2, new_y - self.size / 2, self.size, self.size)
        if not any(rect_y.colliderect(o) for o in obstacles):
            self.y = new_y

        self.rect.center = (self.x, self.y)
        self.direction = self.get_direction_from_angle(dx, dy)

    def wander(self, dt, walls=None, barricades=None):
        dx, dy = self.wander_dir.x, self.wander_dir.y
        self.move_toward_point(
            (self.x + dx * 40, self.y + dy * 40),
            self.speed * 0.4,
            dt,
            walls,
            barricades,
        )
        self.wander_timer -= dt
        if self.wander_timer <= 0:
            self.wander_dir = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
            self.wander_timer = random.uniform(1.5, 3.0)
        self.direction = self.get_direction_from_angle(dx, dy)

    def animate(self, dt):
        self.frame_timer += dt
        if self.frame_timer >= self.frame_speed:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.animations[self.direction])
            self.image = self.animations[self.direction][self.current_frame]

    def try_squeak(self, dt, player):
        # Reduce cooldown
        self.squeak_cooldown -= dt

        # Only squeak if cooldown expired
        if self.squeak_cooldown > 0:
            return

        # Only squeak if rat is close to player
        if self.distance_to(player) > 500:   # only close rats play sounds
            return

        # Small chance to squeak (1–2% per check)
        if random.random() < 0.015:  
            snd = random.choice(RAT_SQUEAK_SOUNDS)
            if snd:
                snd.play()

            # Reset cooldown (2–5 seconds)
            self.squeak_cooldown = random.uniform(2.0, 5.0)


    # --- Main AI ---
    def update(self, dt, player=None, walls=None, enemies=None, barricades=None, **kwargs):
        """Handle rat AI behavior and attacks with visible windup."""
        # Only update LOS memory manually (don’t move via base)
        if walls is not None:
            from enemy_ai_utils import has_line_of_sight
            can_see = has_line_of_sight(self, player, (walls or []) + [b.rect for b in (barricades or []) if b.active])
        else:
            can_see = True

        if can_see:
            self.last_seen_player = (player.x, player.y)

        dist = self.distance_to(player)

        # --- STATE MACHINE ---
        if self.state == "wander":
            self.wander(dt, walls, barricades)
            if dist < self.detection_range and can_see:
                self.state = "chase"

        elif self.state == "chase":
            target = (player.x, player.y) if can_see else self.last_seen_player
            if not target:
                self.state = "wander"
                return
            if dist > self.attack_range:
                self.move_toward_point(target, self.speed, dt, walls, barricades)
            else:
                if self.attack_cooldown <= 0:
                    # enter windup state
                    self.state = "windup"
                    self.timer = self.windup_time

        elif self.state == "windup":
            # hold position — no movement
            self.timer -= dt
            if self.timer <= 0:
                self.state = "attack"
                self.timer = self.attack_duration
                self.has_attacked = False

        elif self.state == "attack":
            # fast lunge toward player
            self.move_toward_point(player.rect.center, self.lunge_speed, dt, walls, barricades)
            if not self.has_attacked and self.rect.colliderect(player.rect):
                player.take_damage(self.damage)
                self.has_attacked = True
            self.timer -= dt
            if self.timer <= 0:
                self.state = "recover"
                self.timer = self.recover_time
                self.attack_cooldown = 0.8

        elif self.state == "recover":
            self.timer -= dt
            if self.timer <= 0:
                self.state = "chase" if dist < self.detection_range else "wander"

        # --- Animation + cooldown ---
        self.try_squeak(dt, player)
        
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        self.animate(dt)
        self.update_burning(dt)
