import pygame

BURN_FRAMES = None

def load_burn_frames():
    global BURN_FRAMES
    BURN_FRAMES = {
        "start": [pygame.image.load(f"assets/fire/burning_start_{i}.png").convert_alpha() for i in range(4)],
        "loop": [pygame.image.load(f"assets/fire/burning_loop_{i}.png").convert_alpha() for i in range(8)],
        "end": [pygame.image.load(f"assets/fire/burning_end_{i}.png").convert_alpha() for i in range(5)],
    }

class Enemy:
    def __init__(self, x: float, y: float, health: int = 50, speed: float = 100.0):
        self.x = x
        self.y = y
        self.health = health
        self.speed = speed
        self.size = 30
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill((255, 0, 0))  # red default enemy color
        self.rect = self.image.get_rect(center=(x, y))

        # Burn animation control
        self.is_burning = False
        self.burn_state = None  # 'start', 'loop', 'end', or None
        self.burn_timer = 0.0
        self.burn_frame = 0

    def update(self, dt: float, player=None):
        # Basic AI: chase the player if one is given
        if player:
            direction = pygame.Vector2(player.x - self.x, player.y - self.y)
            if direction.length_squared() > 0:
                direction = direction.normalize()
                self.x += direction.x * self.speed * dt
                self.y += direction.y * self.speed * dt
                self.rect.center = (int(self.x), int(self.y))

    def draw(self, surface, camera_offset):
        """Draw the enemy relative to the camera offset."""
        cam_x, cam_y = camera_offset
        screen_x = self.x - cam_x
        screen_y = self.y - cam_y
        rect = self.image.get_rect(center=(screen_x, screen_y))
        surface.blit(self.image, rect)

        # --- Burn animation overlay ---
        if self.is_burning and self.burn_state:
            frames = BURN_FRAMES[self.burn_state]
            frame_index = min(int(self.burn_frame), len(frames) - 1)
            frame = frames[frame_index]

            # 🔥 Scale burn sprite based on enemy size
            base_flame_size = 30  # good for rat-sized enemies
            scale_factor = self.size / 20.0  # 20 = rat baseline
            scaled_size = int(base_flame_size * scale_factor)

            scaled_frame = pygame.transform.scale(frame, (scaled_size, scaled_size))

            # Center the scaled flame over the enemy with a small vertical offset
            flame_rect = scaled_frame.get_rect(center=(screen_x, screen_y))
            flame_rect.centery -= self.size // 4  # move flame slightly upward

            surface.blit(scaled_frame, flame_rect)

    def take_damage(self, dmg: int):
        self.health -= dmg

    def is_alive(self) -> bool:
        return self.health > 0

    def update_burning(self, dt):
        if not self.is_burning:
            return

        frames = BURN_FRAMES[self.burn_state]
        frame_count = len(frames)
        frame_speed = 10  # frames per second

        self.burn_timer += dt * frame_speed

        # Advance animation frames
        if self.burn_timer >= 1:
            self.burn_frame += int(self.burn_timer)
            self.burn_timer %= 1  # keep fractional time

            if self.burn_state == "start" and self.burn_frame >= frame_count:
                self.burn_state = "loop"
                self.burn_frame = 0

            elif self.burn_state == "end" and self.burn_frame >= frame_count:
                self.is_burning = False
                self.burn_state = None
                self.burn_frame = 0

        # Wrap looping frames
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
