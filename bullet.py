import pygame
import math
from stats import BulletStats

class Bullet:
    def __init__(self, x: float, y: float, angle: float, stats: BulletStats):
        self.x = x
        self.y = y
        self.angle = angle
        self.stats = stats
        self.lifetime = stats.lifetime
        self.size = 6

    def update(self, dt: float):
        self.x += math.cos(self.angle) * self.stats.speed * dt
        self.y += math.sin(self.angle) * self.stats.speed * dt
        self.lifetime -= dt

    def draw(self, surface):
        pygame.draw.circle(surface, (255, 255, 0), (int(self.x), int(self.y)), self.size)

    def is_alive(self) -> bool:
        return self.lifetime > 0
