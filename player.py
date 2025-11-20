import pygame
import math
from rifle import Rifle
from minigun import Minigun
from plasma_cannon import PlasmaCannon, PlasmaBlob
from flamethrower import Flamethrower

# --- Player Damage Sound ---
try:
    PLAYER_HIT_SOUND = pygame.mixer.Sound("assets/audio/playerDamage.wav")
    PLAYER_HIT_SOUND.set_volume(0.3)
except Exception as e:
    print("Failed to load PLAYER_HIT_SOUND:", e)
    PLAYER_HIT_SOUND = None


class Player:
    def __init__(self, x=400, y=300):
        # --- Core Stats ---
        self.max_health = 100
        self.health = self.max_health
        self.x = x
        self.y = y
        self.size = 30
        self.speed = 250
        self.rect = pygame.Rect(self.x - self.size / 2, self.y - self.size / 2, self.size, self.size)

        # --- Weapons ---
        self.weapons = [Rifle(), Minigun(), PlasmaCannon(), Flamethrower()]
        self.current_weapon_index = 0
        self.current_weapon = self.weapons[self.current_weapon_index]
        self.bullets = []

        # --- State ---
        self.move_angle = 0.0
        self.is_moving = False
        self.facing_angle = 0.0

        # --- Weapon Switch Timing ---
        self.switch_cooldown = 0.3
        self.switch_timer = 0.0

        # --- Camera ---
        self.camera_x = 0
        self.camera_y = 0

        # --- Animation ---
        self.walk_frames = [
            pygame.image.load(f"assets/mech/mechWalk_{i:02}.png").convert_alpha()
            for i in range(13)
        ]
        self.head_image = pygame.image.load("assets/mech/mechHead.png").convert_alpha()
        self.anim_timer = 0.0
        self.anim_speed = 10.0  # frames per second
        self.anim_index = 0

    # -------------------------------------------------------------------------
    def handle_input(self, dt, keys, level_width, level_height, walls=None, barricades=None):
        """Handles movement, collision, and weapon switching."""
        if self.switch_timer > 0:
            self.switch_timer -= dt

        # --- Adjust movement speed for heavy weapons ---
        base_speed = self.speed
        if isinstance(self.current_weapon, Minigun):
            spin = getattr(self.current_weapon, "spin_progress", 0)
            base_speed *= (1.0 - 0.6 * spin)
            base_speed *= (self.current_weapon.reload_slow_factor if self.current_weapon.reloading else 1.0)

        # --- Movement input ---
        dx = dy = 0
        if keys[pygame.K_w]:
            dy -= base_speed * dt
        if keys[pygame.K_s]:
            dy += base_speed * dt
        if keys[pygame.K_a]:
            dx -= base_speed * dt
        if keys[pygame.K_d]:
            dx += base_speed * dt

        # --- Movement & Collision ---
        obstacles = list(walls or [])
        if barricades:
            obstacles += [b.rect for b in barricades if getattr(b, "active", False)]

        # Horizontal movement
        if dx != 0:
            new_x = self.x + dx
            player_rect = pygame.Rect(new_x - self.size / 2, self.y - self.size / 2, self.size, self.size)
            for obstacle in obstacles:
                if player_rect.colliderect(obstacle):
                    new_x = obstacle.left - self.size / 2 if dx > 0 else obstacle.right + self.size / 2
            self.x = new_x

        # Vertical movement
        if dy != 0:
            new_y = self.y + dy
            player_rect = pygame.Rect(self.x - self.size / 2, new_y - self.size / 2, self.size, self.size)
            for obstacle in obstacles:
                if player_rect.colliderect(obstacle):
                    new_y = obstacle.top - self.size / 2 if dy > 0 else obstacle.bottom + self.size / 2
            self.y = new_y

        # --- Animation ---
        if dx != 0 or dy != 0:
            self.is_moving = True
            self.anim_timer += dt * self.anim_speed
            if self.anim_timer >= 1:
                self.anim_index = (self.anim_index + 1) % len(self.walk_frames)
                self.anim_timer = 0
            self.move_angle = math.atan2(dy, dx)
        else:
            self.is_moving = False

        # --- Clamp player to level boundaries ---
        self.x = max(self.size / 2, min(level_width - self.size / 2, self.x))
        self.y = max(self.size / 2, min(level_height - self.size / 2, self.y))

        # --- Camera centers on player ---
        self.camera_x = max(0, min(self.x - 600, level_width - 1200))
        self.camera_y = max(0, min(self.y - 400, level_height - 800))

        # --- Weapon Switching ---
        if keys[pygame.K_q] and self.switch_timer <= 0:
            self.switch_weapon()
            self.switch_timer = self.switch_cooldown

        # --- Update facing direction (toward mouse) ---
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_mouse_x = mouse_x + self.camera_x
        world_mouse_y = mouse_y + self.camera_y
        self.facing_angle = math.atan2(world_mouse_y - self.y, world_mouse_x - self.x)

        # Update rect position for collisions
        self.rect.center = (self.x, self.y)

    # -------------------------------------------------------------------------
    def switch_weapon(self):
        """Cycle through available weapons and stop any ongoing weapon sounds."""
        # Stop any looping audio from the current weapon before switching
        if hasattr(self.current_weapon, "stop_sounds"):
            self.current_weapon.stop_sounds()

        # Switch to next weapon
        self.current_weapon_index = (self.current_weapon_index + 1) % len(self.weapons)
        self.current_weapon = self.weapons[self.current_weapon_index]
        print(f"Switched to {self.current_weapon.__class__.__name__}")

    # -------------------------------------------------------------------------
    def shoot(self, mouse_pos):
        """Delegate firing to the current weapon."""
        self.current_weapon.fire(self.x, self.y, mouse_pos, self.bullets)

    # -------------------------------------------------------------------------
    def update(self, dt, puddles):
        """Update player, bullets, and weapon state."""
        self.current_weapon.update(dt)
        self.rect.center = (self.x, self.y)

        for bullet in list(self.bullets):
            if isinstance(bullet, PlasmaBlob):
                bullet.update(dt, puddles)
            else:
                bullet.update(dt)

    # -------------------------------------------------------------------------
    def take_damage(self, amount):
        self.health = max(0, self.health - amount)

        # Play damage sound
        if PLAYER_HIT_SOUND:
            chan = pygame.mixer.find_channel(True)
            if chan:
                chan.play(PLAYER_HIT_SOUND)

        print(f"Player took {amount} damage! Health: {self.health}/{self.max_health}")


    # -------------------------------------------------------------------------
    def draw(self, surface):
        """Draw player, mech animation, and bullets."""
        screen_x = self.x - self.camera_x
        screen_y = self.y - self.camera_y

        # --- Legs (movement animation) ---
        frame = self.walk_frames[self.anim_index if self.is_moving else 0]
        legs_angle = -math.degrees(self.move_angle) - 90
        rotated_legs = pygame.transform.rotate(frame, legs_angle)
        legs_rect = rotated_legs.get_rect(center=(screen_x, screen_y))
        surface.blit(rotated_legs, legs_rect)

        # --- Head (rotates toward mouse) ---
        angle_degrees = -math.degrees(self.facing_angle) - 90
        rotated_head = pygame.transform.rotate(self.head_image, angle_degrees)
        head_rect = rotated_head.get_rect(center=(screen_x, screen_y))
        surface.blit(rotated_head, head_rect)

        # --- Draw Bullets ---
        for bullet in self.bullets:
            bullet.draw(surface, self.camera_x, self.camera_y)
