import pygame
import math
from bullet import Bullet
from stats import BulletStats

class LightBullet(Bullet):
    def _init_(self,x,y,angle):
        stats = BulletStats(
            speed = 700,
            damage = 5,
            lifetime = 1.0,
            knockback=50.0
            )
        super().__init(x,y,angle,stats)
        
    def draw(self, surface):
        pygame.draw.circle(surface,(200,200,255), (int(self.x),int(self.y)),3)