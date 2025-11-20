# level.py
import math
import pygame
import random
from apartment_walls import APARTMENT_WALLS
from rat_enemy import RatEnemy
from bedbug_enemy import BedbugEnemy
from mighty_mite_enemy import MightyMite

class Level:
    def __init__(self, name, background_path, width, height, enemy_types, spawn_interval, max_enemies, objective_text, walls=None):
        self.name = name
        self.background = pygame.image.load(f"assets/maps/apartmentComplex.png").convert()
        
        bg_rect = self.background.get_rect()
        bg_w, bg_h = bg_rect.width, bg_rect.height
        
        self.width = bg_w
        self.height = bg_h
        self.enemy_types = enemy_types  # list of classes (RatEnemy, etc.)
        self.spawn_interval = spawn_interval
        self.max_enemies = max_enemies
        self.objective_text = objective_text

        self.spawn_timer = 0
        self.enemies = []
        self.completed = False
        self.walls = list(walls) if walls else []
        
        self.ambient_sound = pygame.mixer.Sound("assets/audio/florescentHum.wav")
        self.ambient_sound.set_volume(0.2)
        self.ambient_channel = self.ambient_sound.play(loops=-1)

    def update(self, dt, player, existing_enemies):
        """Handle spawning and update all enemies."""
        new_enemies = []
        self.spawn_timer += dt
        
#         # only spawn if under limit
#         if self.spawn_timer >= self.spawn_interval and len(existing_enemies) < self.max_enemies:
#             self.spawn_timer = 0
#             enemy_class = random.choice(self.enemy_types)
# 
#             # ensure spawn doesn’t overlap walls
#             for _ in range(10):  # up to 10 tries
#                 spawn_x = random.randint(50, self.width - 50)
#                 spawn_y = random.randint(50, self.height - 50)
#                 enemy_rect = pygame.Rect(spawn_x - 15, spawn_y - 15, 30, 30)
#                 if not any(enemy_rect.colliderect(w) for w in self.walls):
#                     new_enemy = enemy_class(spawn_x, spawn_y)
#                     new_enemies.append(new_enemy)
#                     break
# 
#         # if the game design requires "clear all enemies" win condition:
#         if len(existing_enemies) == 0 and self.spawn_interval < 0.5:
#             self.completed = True
# 
#         return new_enemies
    
    def draw(self, surface, camera_offset=(0, 0)):
        """Draw the background and any static elements like walls."""
        cam_x, cam_y = camera_offset

        # Draw background image offset by camera
        surface.blit(self.background, (-cam_x, -cam_y))

        # Optional: draw walls for debugging (red boxes)
#         for wall in self.walls:
#             wall_rect = pygame.Rect(
#                 wall.x - cam_x,
#                 wall.y - cam_y,
#                 wall.width,
#                 wall.height
#             )
#             pygame.draw.rect(surface, (200, 0, 0), wall_rect, 2)


        return
    
    def stop_ambient(self):
        """Stops the ambient background sound."""
        if self.ambient_channel:
            self.ambient_sound.stop()
            self.ambient_channel = None
