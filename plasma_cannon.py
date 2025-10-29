import math
import pygame

class PlasmaCannon:
    def __init__(self):
        self.fire_rate = 1.0  # 1 shot per second
        self.cooldown = 0
        self.triggered = False  # tracks if trigger was pulled

    def fire(self, x, y, mouse_pos, bullet_list, mouse_held=False):
        if self.cooldown <= 0 and mouse_held and not self.triggered:
            angle = math.atan2(mouse_pos[1] - y, mouse_pos[0] - x)
            blob = PlasmaBlob(x, y, angle)
            bullet_list.append(blob)
            self.cooldown = self.fire_rate
            self.triggered = True  # prevent firing again until button released

    def update(self, dt):
        if self.cooldown > 0:
            self.cooldown -= dt

    def reset_trigger(self):
        self.triggered = False


class PlasmaBlob:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 400
        self.radius = 8
        self.color = (0, 200, 255)
        self.damage = 50        # direct hit damage
        self.lifetime = 1.0     # how long the projectile exists before disappearing
        self.exploded = False   # track if it already exploded

    def update(self, dt, puddle_list):
        if not self.exploded:
            # Move the projectile
            self.x += math.cos(self.angle) * self.speed * dt
            self.y += math.sin(self.angle) * self.speed * dt
            self.lifetime -= dt
            # Lifetime expired → explode
            if self.lifetime <= 0:
                self.explode(puddle_list)

    def explode(self, puddle_list):
        if not self.exploded:
            self.exploded = True
            # Leave a puddle at current location
            puddle_list.append(PlasmaPuddle(self.x, self.y))

    def draw(self, surface, camera_x=0, camera_y=0):
        """Draw plasma blob relative to the camera offset."""
        if not self.exploded:
            screen_x = int(self.x - camera_x)
            screen_y = int(self.y - camera_y)
            pygame.draw.circle(surface, self.color, (screen_x, screen_y), self.radius)


class PlasmaPuddle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 20
        self.color = (0, 150, 255, 100)  # optional transparency
        self.damage_per_second = 10
        self.duration = 5.0  # how long puddle lasts

    def update(self, dt):
        self.duration -= dt

    def is_alive(self):
        return self.duration > 0

    def draw(self, surface, camera_x=0, camera_y=0):
        """Draw semi-transparent puddle relative to the camera offset."""
        s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, self.color, (self.radius, self.radius), self.radius)
        surface.blit(s, (int(self.x - self.radius - camera_x),
                         int(self.y - self.radius - camera_y)))
