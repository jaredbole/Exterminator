import math
import pygame

pygame.mixer.init()
# Load sound once at module import
RIFLE_FIRE_SOUND = pygame.mixer.Sound("assets/audio/rifle.mp3")
RIFLE_FIRE_SOUND.set_volume(0.15)  # adjust 0–1 for loudness

class Rifle:
    def __init__(self):
        self.fire_rate = 0.4  # seconds between shots
        self.cooldown = 0
        self.triggered = False  # track if mouse was pressed for semi-auto

    def update(self, dt):
        if self.cooldown > 0:
            self.cooldown -= dt

    def fire(self, x, y, mouse_pos, bullet_list, mouse_held):
        if self.cooldown > 0:
            return

        if mouse_held:
            if not self.triggered:
                self.triggered = True
                self.cooldown = self.fire_rate

                dx = mouse_pos[0] - x
                dy = mouse_pos[1] - y
                angle = math.atan2(dy, dx)
                
                RIFLE_FIRE_SOUND.play()

                # You can adjust this number for testing (e.g., 3 pierces)
                bullet = RifleBullet(x, y, angle, pierce_count=3)
                bullet_list.append(bullet)
        else:
            self.triggered = False


    def reset_trigger(self):
        self.triggered = False


class RifleBullet:
    def __init__(self, x, y, angle, pierce_count=3):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 1000
        self.radius = 8
        self.color = (255, 255, 255)
        self.damage = 40
        self.pierce_count = pierce_count  # how many enemies the bullet can go through
        self.alive = True  # track if bullet should remain in play

    def update(self, dt):
        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt

    def draw(self, surface, camera_x=0, camera_y=0):
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        pygame.draw.circle(surface, self.color, (screen_x, screen_y), self.radius)

