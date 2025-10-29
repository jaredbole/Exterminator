import pygame
import random
from player import Player
from level import Level
from enemy import Enemy
from rat_enemy import RatEnemy
from bedbug_enemy import BedbugEnemy
from mighty_mite_enemy import MightyMite
from plasma_cannon import PlasmaBlob, PlasmaPuddle
from flamethrower import Flamethrower

pygame.init()
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

from enemy import load_burn_frames
load_burn_frames()

# Entities
player = Player(600, 400)  # Start near center
enemies: list[Enemy] = []

# Global puddle list
puddles: list[PlasmaPuddle] = []
burns: dict = {}

# --- CAMERA FUNCTION ---
def get_camera_offset(player, level_width, level_height, screen_width, screen_height):
    x = player.x - screen_width // 2
    y = player.y - screen_height // 2

    x = max(0, min(x, level_width - screen_width))
    y = max(0, min(y, level_height - screen_height))
    return (x, y)

# --- LEVEL SETUP ---
levels = [
    Level(
        name="Infested Apartment Complex",
        background_path="assets/backgrounds/apartment.png",
        width=3000,
        height=2000,
        enemy_types=[RatEnemy],
        spawn_interval=3.0,
        max_enemies=10,
        objective_text="Exterminate the roaches and clear the building!"
    ),
    Level(
        name="Sewer Depths",
        background_path="assets/backgrounds/sewer.png",
        width=3200,
        height=2200,
        enemy_types=[RatEnemy, BedbugEnemy],
        spawn_interval=2.5,
        max_enemies=12,
        objective_text="Use your flashlight to clear the tunnels of bedbugs."
    ),
    Level(
        name="BioLab Reactor Core",
        background_path="assets/backgrounds/biolab.png",
        width=3500,
        height=2300,
        enemy_types=[MightyMite],
        spawn_interval=1.5,
        max_enemies=15,
        objective_text="Shut down the Hive Core before it spreads!"
    ),
]

current_level_index = 0
current_level = levels[current_level_index]

running = True
while running:
    dt = clock.tick(60) / 1000  # delta time in seconds


# --- CAMERA ---
    camera_offset = get_camera_offset(player, current_level.width, current_level.height, WIDTH, HEIGHT)

    # --- Events ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    player.handle_input(dt, keys, current_level.width, current_level.height)

    # --- Weapon firing ---
    mouse_held = pygame.mouse.get_pressed()[0]
    screen_mouse = pygame.mouse.get_pos()
    mouse_pos = (screen_mouse[0] + camera_offset[0], screen_mouse[1] + camera_offset[1])

    if isinstance(player.current_weapon, Flamethrower):
        player.current_weapon.fire(player.x, player.y, mouse_pos, player.bullets, mouse_held, enemies, burns)
    else:
        player.current_weapon.fire(player.x, player.y, mouse_pos, player.bullets, mouse_held)

    if hasattr(player.current_weapon, "reset_trigger") and not mouse_held:
        player.current_weapon.reset_trigger()

    # --- Update ---
    player.update(dt, puddles)
    for enemy in enemies:
        enemy.update(dt, player=player)

    # --- Bullet collisions ---
    for bullet in list(player.bullets):
        for enemy in enemies:
            if enemy.rect.collidepoint(bullet.x, bullet.y):
                if isinstance(bullet, PlasmaBlob):
                    enemy.take_damage(bullet.damage)
                    bullet.explode(puddles)
                else:
                    enemy.take_damage(getattr(bullet, "damage", 0))
                if not isinstance(bullet, PlasmaBlob) or bullet.exploded:
                    if bullet in player.bullets:
                        player.bullets.remove(bullet)
                break

    # --- Puddle and burn updates ---
    for puddle in list(puddles):
        puddle.update(dt)
        for enemy in enemies:
            dx = enemy.x - puddle.x
            dy = enemy.y - puddle.y
            if (dx**2 + dy**2)**0.5 <= puddle.radius:
                enemy.take_damage(puddle.damage_per_second * dt)
        if not puddle.is_alive():
            puddles.remove(puddle)

    for enemy, state in list(burns.items()):
        if enemy not in enemies or not enemy.is_alive():
            enemy.stop_burning()
            burns.pop(enemy, None)
            continue
        enemy.take_damage(state['dps'] * dt)
        state['remaining'] -= dt
        if state['remaining'] <= 0:
            enemy.stop_burning()
            burns.pop(enemy, None)
        elif not enemy.is_burning:
            enemy.start_burning()

    enemies = [e for e in enemies if e.is_alive()]

    # --- Level update ---
    new_enemies = current_level.update(dt, player)
    if new_enemies:
        enemies.extend(new_enemies)

    # --- Check level completion ---
    if current_level.completed:
        current_level_index += 1
        if current_level_index < len(levels):
            current_level = levels[current_level_index]
        else:
            print("You win!")
            running = False

    
    # --- DRAW ---
    current_level.draw(screen, camera_offset)
    player.draw(screen)
    for enemy in enemies:
        enemy.draw(screen, camera_offset)
    for puddle in puddles:
        puddle.draw(screen, camera_offset[0], camera_offset[1])

    # Flamethrower cone
    if isinstance(player.current_weapon, Flamethrower) and pygame.mouse.get_pressed()[0]:
        player.current_weapon.draw_cone(screen, player.x, player.y, mouse_pos, camera_offset)

    pygame.display.flip()

pygame.quit()
