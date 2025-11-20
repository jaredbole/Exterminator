# enemy.py
import pygame
import math
from enemy_ai_utils import has_line_of_sight  # ✅ Use your existing AI utility

BURN_FRAMES = None

# --- Damage sound ---
try:
    ENEMY_HIT_SOUND = pygame.mixer.Sound("assets/audio/enemyDamage.wav")
    ENEMY_HIT_SOUND.set_volume(0.1)  # tweak volume as needed
except:
    ENEMY_HIT_SOUND = None


def load_burn_frames():
    """Preload flame animation frames."""
    global BURN_FRAMES
    BURN_FRAMES = {
        "start": [pygame.image.load(f"assets/fire/burning_start_{i}.png").convert_alpha() for i in range(4)],
        "loop":  [pygame.image.load(f"assets/fire/burning_loop_{i}.png").convert_alpha() for i in range(8)],
        "end":   [pygame.image.load(f"assets/fire/burning_end_{i}.png").convert_alpha() for i in range(5)],
    }


class Enemy:
    def __init__(self, x: float, y: float, health: int = 50, speed: float = 100.0):
        self.x = x
        self.y = y
        self.health = health
        self.speed = speed
        self.size = 30
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(center=(x, y))

        # Burning animation
        self.is_burning = False
        self.burn_state = None
        self.burn_timer = 0.0
        self.burn_frame = 0

        # Memory of last seen player position
        self.last_known = None

        # 🧊 NEW — Plasma puddle slow system
        self.speed_multiplier = 1.0
        self.in_puddle = False
        self.puddle_slow = 1.0
        self.puddle_tick_timer = 0.0


    # 🧠 Centralized AI + movement for all enemies
    def update(self, dt: float, player=None, walls=None, barricades=None):
        """
        Handles AI movement, wall + barricade collisions, and LOS detection.
        Backward compatible with older calls that omit barricades.
        """
        if not player:
            return

        # --- Combine static walls with active barricades (if any) ---
        obstacles = list(walls or [])
        if barricades:
            obstacles += [b.rect for b in barricades if getattr(b, "active", False)]

        # --- Line of sight using shared AI utility ---
        can_see = has_line_of_sight(self, player, obstacles)
        if can_see:
            self.last_known = (player.x, player.y)
        elif not self.last_known:
            return  # hasn't seen player yet

        # --- Move toward target (visible or last known) ---
        tx, ty = (player.x, player.y) if can_see else self.last_known
        direction = pygame.Vector2(tx - self.x, ty - self.y)
        if direction.length_squared() == 0:
            return
        direction = direction.normalize()

        # ✔ USE SPEED MULTIPLIER HERE
        actual_speed = self.speed * self.speed_multiplier

        new_x = self.x + direction.x * actual_speed * dt
        new_y = self.y + direction.y * actual_speed * dt

        # Horizontal collision
        new_rect_x = pygame.Rect(new_x - self.size / 2, self.y - self.size / 2, self.size, self.size)
        if not any(new_rect_x.colliderect(o) for o in obstacles):
            self.x = new_x

        # Vertical collision
        new_rect_y = pygame.Rect(self.x - self.size / 2, new_y - self.size / 2, self.size, self.size)
        if not any(new_rect_y.colliderect(o) for o in obstacles):
            self.y = new_y

        self.rect.center = (int(self.x), int(self.y))
        
        self.puddle_tick_timer = max(0.0, self.puddle_tick_timer - dt)
        # 🔄 Reset puddle flags each frame (main.py will set them again)
        self.in_puddle = False

    # 🧯 Universal burn effects for all enemies
    def update_burning(self, dt):
        if not self.is_burning:
            return

        frames = BURN_FRAMES[self.burn_state]
        frame_count = len(frames)
        frame_speed = 10  # frames per second
        self.burn_timer += dt * frame_speed

        if self.burn_timer >= 1:
            self.burn_frame += int(self.burn_timer)
            self.burn_timer %= 1

            if self.burn_state == "start" and self.burn_frame >= frame_count:
                self.burn_state = "loop"
                self.burn_frame = 0
            elif self.burn_state == "end" and self.burn_frame >= frame_count:
                self.is_burning = False
                self.burn_state = None
                self.burn_frame = 0

        if self.burn_state == "loop":
            self.burn_frame %= frame_count

    def start_burning(self):
        if not self.is_burning:
            self.is_burning = True
            self.burn_state = "start"
            self.burn_frame = 0
            self.burn_timer = 0.0

    def stop_burning(self):
        if self.is_burning and self.burn_state != "end":
            self.burn_state = "end"
            self.burn_frame = 0
            self.burn_timer = 0.0

    # Health and status
    def take_damage(self, dmg: int, player=None):
        if dmg <= 0:
            return

        self.health -= dmg

        # Distance-based volume falloff
        if ENEMY_HIT_SOUND and self.is_alive() and player is not None:
            # compute distance
            dx = self.x - player.x
            dy = self.y - player.y
            dist = math.hypot(dx, dy)

            # max hearable distance
            max_dist = 800  # adjust as needed

            # linear falloff
            vol = max(0.0, min(0.3, 0.3 - 0.3*(dist / max_dist)))

            # temporarily set volume
            ENEMY_HIT_SOUND.set_volume(vol)

            # play on a free channel
            ENEMY_HIT_SOUND.play()



    def is_alive(self) -> bool:
        return self.health > 0

    # 🎨 Drawing (includes burn overlay)
    def draw(self, surface, camera_offset):
        cam_x, cam_y = camera_offset
        screen_x = self.x - cam_x
        screen_y = self.y - cam_y

        rect = self.image.get_rect(center=(screen_x, screen_y))
        surface.blit(self.image, rect)

        # 🔥 Burn overlay
        if self.is_burning and self.burn_state and BURN_FRAMES:
            frames = BURN_FRAMES[self.burn_state]
            frame_index = min(int(self.burn_frame), len(frames) - 1)
            frame = frames[frame_index]

            scale_factor = self.size / 20.0
            scaled_size = int(30 * scale_factor)
            scaled_frame = pygame.transform.scale(frame, (scaled_size, scaled_size))
            flame_rect = scaled_frame.get_rect(center=(screen_x, screen_y - self.size // 4))
            surface.blit(scaled_frame, flame_rect)
