import math
import pygame

pygame.mixer.init()

# --- Load sounds ---
MINIGUN_FIRE_SOUND_SLOW = pygame.mixer.Sound("assets/audio/minigun_slow.wav")
MINIGUN_FIRE_SOUND_MED = pygame.mixer.Sound("assets/audio/minigun_med.wav")
MINIGUN_FIRE_SOUND_FAST = pygame.mixer.Sound("assets/audio/minigun_fast.wav")

for snd in (MINIGUN_FIRE_SOUND_SLOW, MINIGUN_FIRE_SOUND_MED, MINIGUN_FIRE_SOUND_FAST):
    snd.set_volume(0.3)
    
try:
    MINIGUN_RELOAD_SOUND = pygame.mixer.Sound("assets/audio/minigunReload.wav")
    MINIGUN_RELOAD_SOUND.set_volume(0.4)
except:
    MINIGUN_RELOAD_SOUND = None

class Minigun:
    def __init__(self):
        # --- Fire control ---
        self.base_fire_rate = 0.15  # slow start
        self.min_fire_rate = 0.05   # fastest spin
        self.fire_rate = self.base_fire_rate
        self.cooldown = 0

        # --- Spin behavior ---
        self.firing = False
        self.spin_progress = 0.0     # 0–1 progress of spin
        self.spin_up_time = 5.0      # seconds to reach full spin
        self.spin_down_time = 0.5    # seconds to wind down

        # --- Audio state ---
        self.current_sound = None

        # --- Ammo system ---
        self.max_ammo = 150
        self.ammo = self.max_ammo
        self.reload_time = 3.0      # seconds
        self.reload_timer = 0.0
        self.reloading = False

        # Used by player to scale speed when reloading
        self.reload_slow_factor = 0.5  

    def update(self, dt):
        # Handle reloading
        if self.reloading:
            self.reload_timer -= dt
            if self.reload_timer <= 0:
                self.ammo = self.max_ammo
                self.reloading = False
                # End reload sound if needed
                if MINIGUN_RELOAD_SOUND:
                    MINIGUN_RELOAD_SOUND.stop()
            # While reloading, no spinning
            self.firing = False
            if self.current_sound:
                self.current_sound.stop()
                self.current_sound = None
            return
        # --- Handle spin-up and spin-down ---
        if self.firing:
            self.spin_progress = min(1.0, self.spin_progress + dt / self.spin_up_time)
        else:
            self.spin_progress = max(0.0, self.spin_progress - dt / self.spin_down_time)

        # --- Update fire rate based on spin ---
        self.fire_rate = self.base_fire_rate - (
            (self.base_fire_rate - self.min_fire_rate) * self.spin_progress
        )

        # --- Choose sound stage ---
        new_sound = None
        if self.spin_progress < 0.33:
            new_sound = MINIGUN_FIRE_SOUND_SLOW
        elif self.spin_progress < 0.66:
            new_sound = MINIGUN_FIRE_SOUND_MED
        else:
            new_sound = MINIGUN_FIRE_SOUND_FAST

        # --- Handle switching sounds smoothly ---
        if new_sound != self.current_sound:
            if self.current_sound:
                self.current_sound.stop()
            if self.firing:  # only loop if actually firing
                new_sound.play(loops=-1)
            self.current_sound = new_sound

        # --- Cooldown timer ---
        if self.cooldown > 0:
            self.cooldown -= dt
            
    # ----------------------------
    # Manual reload trigger
    # ----------------------------
    def start_reload(self):
        if not self.reloading:
            self.reloading = True
            self.reload_timer = self.reload_time
            if MINIGUN_RELOAD_SOUND:
                MINIGUN_RELOAD_SOUND.play()

    def fire(self, x, y, mouse_pos, bullet_list, mouse_held):
        # If out of ammo and not reloading, start reload
        if self.ammo <= 0 and not self.reloading:
            self.start_reload()
            return
        # Start spinning when mouse pressed
        if mouse_held and not self.firing and not self.reloading:
            self.firing = True
            # start appropriate sound for current spin (usually slow)
            if self.current_sound:
                self.current_sound.stop()
            MINIGUN_FIRE_SOUND_SLOW.play(loops=-1)
            self.current_sound = MINIGUN_FIRE_SOUND_SLOW

        # Stop spinning when released
        elif not mouse_held and self.firing:
            self.firing = False
            if self.current_sound:
                self.current_sound.stop()
                self.current_sound = None

        # Fire bullets according to spin rate
        if self.cooldown <= 0 and mouse_held and not self.reloading:
            if self.ammo > 0:
                angle = math.atan2(mouse_pos[1] - y, mouse_pos[0] - x)
                bullet_list.append(MinigunBullet(x, y, angle))
                self.cooldown = self.fire_rate
                self.ammo -= 1
            else:
                # Auto reload trigger when dry
                self.start_reload()
            
    def stop_sounds(self):
        """Stops any active minigun sounds."""
        if self.current_sound:
            self.current_sound.stop()
            
    # ----------------------------
    # Get HUD-friendly ammo info
    # ----------------------------
    def get_ammo_status(self):
        """Returns tuple (current_ammo, max_ammo, reloading_bool)"""
        return self.ammo, self.max_ammo, self.reloading

class MinigunBullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 600
        self.radius = 3
        self.color = (255, 255, 0)
        self.damage = 10

    def update(self, dt):
        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt

    def draw(self, surface, camera_x=0, camera_y=0):
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        pygame.draw.circle(surface, self.color, (screen_x, screen_y), self.radius)
