import math
import pygame

class Minigun:
    def __init__(self):
        self.fire_rate = 0.1  # fast fire
        self.cooldown = 0

    def update(self, dt):
        if self.cooldown > 0:
            self.cooldown -= dt

    def fire(self, x, y, mouse_pos, bullet_list, mouse_held):
        # Fires continuously while mouse held
        if self.cooldown <= 0 and mouse_held:
            angle = math.atan2(mouse_pos[1] - y, mouse_pos[0] - x)
            bullet_list.append(MinigunBullet(x, y, angle))
            self.cooldown = self.fire_rate


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
        """
        Draws the bullet relative to camera offset.
        Example:
            bullet.draw(screen, camera_offset[0], camera_offset[1])
        """
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        pygame.draw.circle(surface, self.color, (screen_x, screen_y), self.radius)
