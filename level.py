# level.py
import pygame
import random
from rat_enemy import RatEnemy
from bedbug_enemy import BedbugEnemy
from mighty_mite_enemy import MightyMite

class Level:
    def __init__(self, name, background_path, width, height, enemy_types, spawn_interval, max_enemies, objective_text):
        self.name = name
        self.background = pygame.image.load(f"assets/maps/apartmentComplex.jpg").convert()
        self.width = width
        self.height = height
        self.enemy_types = enemy_types  # list of classes (RatEnemy, etc.)
        self.spawn_interval = spawn_interval
        self.max_enemies = max_enemies
        self.objective_text = objective_text

        self.spawn_timer = 0
        self.enemies = []
        self.completed = False

    def update(self, dt, player):
        """Handle spawning and update all enemies."""
        new_enemies = []

        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval and len(self.enemies) < self.max_enemies:
            self.spawn_timer = 0
            enemy_class = random.choice(self.enemy_types)
            spawn_x = random.randint(50, self.width - 50)
            spawn_y = random.randint(50, self.height - 50)
            new_enemy = enemy_class(spawn_x, spawn_y)
            self.enemies.append(new_enemy)
            new_enemies.append(new_enemy)

        for enemy in list(self.enemies):
            enemy.update(dt, player=player)
            if not enemy.is_alive():
                self.enemies.remove(enemy)

        if len(self.enemies) == 0 and self.spawn_interval < 0.5:
            self.completed = True

        return new_enemies

    def draw(self, screen, camera_offset):
        """Draw level and enemies relative to camera."""
        screen.blit(self.background, (-camera_offset[0], -camera_offset[1]))
        for enemy in self.enemies:
            enemy.draw(screen, camera_offset)
