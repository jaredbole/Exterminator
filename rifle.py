import math
import pygame

class Rifle:
    def __init__(self):
        self.fire_rate = 0.5  # seconds between shots
        self.cooldown = 0
        self.triggered = False  # track if mouse was pressed for semi-auto

    def update(self, dt):
        if self.cooldown > 0:
            self.cooldown -= dt

    def fire(self, x, y, mouse_pos, bullet_list, mouse_held):
        if self.cooldown > 0:
            return

        # Semi-auto: only fire if mouse was just pressed
        if mouse_held:
            if not self.triggered:
                self.triggered = True
                self.cooldown = self.fire_rate

                dx = mouse_pos[0] - x
                dy = mouse_pos[1] - y
                angle = math.atan2(dy, dx)

                bullet_list.append(RifleBullet(x, y, angle))
        else:
            # Reset trigger when mouse released
            self.triggered = False

    def reset_trigger(self):
        self.triggered = False


class RifleBullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 1000
        self.radius = 8
        self.color = (255, 255, 255)
        self.damage = 40

    def update(self, dt):
        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt

    def draw(self, surface, camera_x=0, camera_y=0):
        """
        Draws the bullet relative to the camera offset.
        Usage: bullet.draw(screen, camera_offset[0], camera_offset[1])
        """
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        pygame.draw.circle(surface, self.color, (screen_x, screen_y), self.radius)
