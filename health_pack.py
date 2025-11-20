# health_pack.py
import pygame
import random

class HealthPack:
    def __init__(self, x, y, heal_amount=35):
        self.x = x
        self.y = y
        self.heal_amount = heal_amount
        self.size = 24
        self.rect = pygame.Rect(x - self.size/2, y - self.size/2, self.size, self.size)
        self.collected = False

        # Load sprite
        try:
            self.image = pygame.image.load("assets/healthPack.png").convert_alpha()
        except:
            self.image = pygame.Surface((self.size, self.size))
            self.image.fill((200, 30, 30))  # fallback red box

        # Optional pickup sound
        try:
            self.pickup_sound = pygame.mixer.Sound("assets/audio/health_pickup.wav")
        except:
            self.pickup_sound = None

    def update(self, player):
        """Check if player collects the health pack."""
        if not self.collected and self.rect.colliderect(player.rect):
            player.health = min(player.max_health, player.health + self.heal_amount)
            self.collected = True
            if self.pickup_sound:
                self.pickup_sound.play()

    def draw(self, screen, camera_offset=(0, 0)):
        if not self.collected:
            screen.blit(self.image, (self.rect.x - camera_offset[0], self.rect.y - camera_offset[1]))
