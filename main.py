import pygame
import random
from player import Player
from level import Level, APARTMENT_WALLS
from rat_nest_spawner import create_rat_nests
from barricade import Barricade
from enemy import Enemy, load_burn_frames
from brood_fly import BroodFly
from rat_enemy import RatEnemy
from plasma_cannon import PlasmaBlob, PlasmaPuddle
from flamethrower import Flamethrower
from minigun import Minigun
from hud import HUD
from fog_of_war import FogOfWar
from pause_menu import PauseMenu

pygame.init()
pygame.mixer.init()
pygame.mixer.set_num_channels(64)
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

load_burn_frames()

# Entities
player = Player(100, 1510)  # Start location
enemies: list[Enemy] = []

health_packs = []

hud = HUD(player, WIDTH, HEIGHT)
pause_menu = PauseMenu(WIDTH, HEIGHT)

# --- EXIT ZONE ---
exit_zone = pygame.Rect(1568, 640, 98, 130) 

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
        background_path="assets/backgrounds/apartmentComplex.png",
        width=2784,
        height=1600,
        enemy_types=[RatEnemy,BroodFly],
        spawn_interval=1.0,
        max_enemies=100,
        objective_text="Exterminate the roaches and clear the building!",
        walls=APARTMENT_WALLS,
    ),
#     Level(
#         name="Sewer Depths",
#         background_path="assets/backgrounds/sewer.png",
#         width=2784,
#         height=1600,
#         enemy_types=[RatEnemy, BedbugEnemy],
#         spawn_interval=2.5,
#         max_enemies=12,
#         objective_text="Use your flashlight to clear the tunnels of bedbugs."
#     ),
#     Level(
#         name="BioLab Reactor Core",
#         background_path="assets/backgrounds/biolab.png",
#         width=2784,
#         height=1600,
#         enemy_types=[MightyMite],
#         spawn_interval=1.5,
#         max_enemies=15,
#         objective_text="Shut down the Hive Core before it spreads!"
#     ),
]

current_level_index = 0
current_level = levels[current_level_index]

rat_nests = create_rat_nests(current_level.name)

barricades = [
    Barricade(1408, 1184, 100, 32, nests_required_to_clear=15),
    Barricade(350, 126, 32, 64, nests_required_to_clear=10),
    Barricade(2656, 674, 100, 32, nests_required_to_clear=4)
]

fog = FogOfWar(current_level.width, current_level.height)


def reset_game():
    global player, enemies, puddles, burns, rat_nests, hud
    player = Player(100, 1510)
    player.health = player.max_health
    player.current_weapon_index = 0
    player.current_weapon = player.weapons[player.current_weapon_index]
    player.bullets.clear()

    enemies.clear()
    puddles.clear()
    burns.clear()
    health_packs.clear()
    rat_nests = create_rat_nests(current_level.name)
    fog = Fog


    for barricade in barricades:
        barricade.active = True
        barricade.has_played_sound = False

    hud = HUD(player, WIDTH, HEIGHT)
    hud.update_objective_progress(0, len(rat_nests))

    current_level.ambient_channel = current_level.ambient_sound.play(loops=-1)
    current_level.ambient_sound.set_volume(0.2)


def game_over_screen(screen):
    """Display Game Over screen until player quits or presses R to restart."""
    font_large = pygame.font.SysFont("consolas", 72)
    font_small = pygame.font.SysFont("consolas", 32)
    
    game_over_text = font_large.render("GAME OVER", True, (255, 0, 0))
    restart_text = font_small.render("Press R to Restart or ESC to Quit", True, (255, 255, 255))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()
                elif event.key == pygame.K_r:
                    return  # Return to restart the game

        screen.fill((0, 0, 0))
        screen.blit(game_over_text, (
            screen.get_width() // 2 - game_over_text.get_width() // 2,
            screen.get_height() // 2 - game_over_text.get_height() // 2 - 40
        ))
        screen.blit(restart_text, (
            screen.get_width() // 2 - restart_text.get_width() // 2,
            screen.get_height() // 2 + 40
        ))

        pygame.display.flip()
        pygame.time.delay(100)
        
def win_screen(screen):
    """Display Win screen until player quits or presses R to restart."""
    font_large = pygame.font.SysFont("consolas", 72)
    font_small = pygame.font.SysFont("consolas", 32)

    win_text = font_large.render("MISSION COMPLETE!", True, (0, 255, 0))
    restart_text = font_small.render("Press R to Replay or ESC to Quit", True, (255, 255, 255))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()
                elif event.key == pygame.K_r:
                    return  # restart the mission

        screen.fill((0, 0, 0))
        screen.blit(win_text, (
            screen.get_width() // 2 - win_text.get_width() // 2,
            screen.get_height() // 2 - win_text.get_height() // 2 - 40
        ))
        screen.blit(restart_text, (
            screen.get_width() // 2 - restart_text.get_width() // 2,
            screen.get_height() // 2 + 40
        ))
        pygame.display.flip()
        pygame.time.delay(100)


running = True
while running:
    dt = clock.tick(60) / 1000  # delta time in seconds

# --- CAMERA ---
    camera_offset = get_camera_offset(player, current_level.width, current_level.height, WIDTH, HEIGHT)

    # --- Events ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Toggle pause on ESC
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pause_menu.toggle()

        # If paused, handle menu navigation
        if pause_menu.active:
            result = pause_menu.handle_input(event)
            if result == "RESUME":
                pause_menu.toggle()
            elif result == "EXIT":
                pygame.quit()
                exit()

    # --- DEBUG: spawn a BroodFly manually ---
        if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
            # Spawn BroodFly near player
            spawn_x = player.x + random.randint(-200, 200)
            spawn_y = player.y + random.randint(-200, 200)
            fly = BroodFly(spawn_x, spawn_y)
            enemies.append(fly)
            print(f"Spawned BroodFly at ({spawn_x:.0f}, {spawn_y:.0f})")

    keys = pygame.key.get_pressed()
    if not pause_menu.active:
        player.handle_input(dt, keys, current_level.width, current_level.height, current_level.walls, barricades)


    if pause_menu.active:
        # Draw level fully darkened behind menu
        current_level.draw(screen, camera_offset)
        player.draw(screen)
        for enemy in enemies:
            enemy.draw(screen, camera_offset)
        for nest in rat_nests:
            nest.draw(screen, camera_offset)
            
        fog.draw(screen, camera_offset)

        # Draw pause menu last
        pause_menu.draw(screen)
        pygame.display.flip()
        continue  # Skip gameplay this frame

    # --- Weapon firing ---
    mouse_held = pygame.mouse.get_pressed()[0]
    screen_mouse = pygame.mouse.get_pos()
    mouse_pos = (screen_mouse[0] + camera_offset[0], screen_mouse[1] + camera_offset[1])
    if isinstance(player.current_weapon, Minigun):
        if keys[pygame.K_r]:
            player.current_weapon.start_reload()


    if isinstance(player.current_weapon, Flamethrower):
        # Fire weapon logic (handles enemies, warmup, cooldown)
        player.current_weapon.fire(
            player.x, player.y, mouse_pos, player.bullets,
            mouse_held, enemies, burns, current_level.walls, player
        )

        # --- Flamethrower damage to nests ---
        if player.current_weapon.firing and player.current_weapon.ready_to_fire:
            for nest in rat_nests:
                if not nest.active:
                    continue

                in_cone, dist, visible_range = player.current_weapon.can_hit_point(
                    player.x, player.y, mouse_pos, nest.x, nest.y, current_level.walls
                )

                if in_cone:
                    damage = player.current_weapon._calc_instant_damage(dist)
                    nest.take_damage(damage * dt, health_packs)
                    nest.start_burning(
                        dps=player.current_weapon.burn_dps,
                        duration=player.current_weapon.burn_duration
                    )

    else:
        player.current_weapon.fire(player.x, player.y, mouse_pos, player.bullets, mouse_held)

    if hasattr(player.current_weapon, "reset_trigger") and not mouse_held:
        player.current_weapon.reset_trigger()
    
    # Reveal area around player
    fog.reveal_circle(player.x, player.y, radius=250)

    # --- Check for Game Over ---
    if player.health <= 0:
        fade = pygame.Surface((WIDTH, HEIGHT))
        fade.fill((0, 0, 0))
        pygame.mixer.stop()   # stop all currently playing
        game_over_screen(screen)
        reset_game()
        continue  # skip the rest of this loop iteration

    # Update nests
    for nest in rat_nests:
        nest.update(dt, enemies, walls=current_level.walls, player=player)
        
    active_nests = sum(1 for nest in rat_nests if nest.active)
    
    # --- Update ---
    player.update(dt, puddles)
    
     # --- Win condition: all nests destroyed and player reaches exit ---
    if active_nests == 0 and exit_zone.colliderect(player.rect):
        fade = pygame.Surface((WIDTH, HEIGHT))
        fade.fill((0, 0, 0))
        pygame.mixer.stop()   # stop all currently playing
        win_screen(screen)
        reset_game()
        continue
    
    for barricade in barricades:
        barricade.update(active_nests)
        
    total_nests = len(rat_nests)
    hud.update_objective_progress(active_nests, total_nests)
    



        
    for enemy in enemies:
        enemy.update(dt, player=player, walls=current_level.walls, enemies=enemies, barricades=barricades)
        if isinstance(enemy, BroodFly):
            enemy.projectiles.draw(screen)
        
    # --- Bullet collisions ---
    for bullet in list(player.bullets):
        bullet_hit = False  # track if bullet should be removed
        
        for nest in rat_nests:
            if nest.active and nest.rect.collidepoint(bullet.x, bullet.y):
                nest.take_damage(getattr(bullet, "damage", 0), health_packs)
                if bullet in player.bullets:
                    player.bullets.remove(bullet)
                break

        # Check collision with enemies
        for enemy in enemies:
            if enemy.rect.collidepoint(bullet.x, bullet.y):
                if isinstance(bullet, PlasmaBlob):
                    enemy.take_damage(bullet.damage, player)
                    bullet.explode(puddles)
                    bullet_hit = True
                    break  # plasma still behaves normally
                else:
                    enemy.take_damage(getattr(bullet, "damage", 0), player)
                    if hasattr(bullet, "pierce_count"):
                        bullet.pierce_count -= 1

                        # visually show weakening — bullet shrinks slightly after each pierce
                        bullet.radius = max(3, 8 - (3 - bullet.pierce_count))
                        bullet.color = (200, 200, 255) if bullet.pierce_count == 1 else (255, 255, 255)

                        if bullet.pierce_count <= 0:
                            bullet_hit = True  # remove after it pierces enough enemies
                    else:
                        bullet_hit = True  # fallback for non-piercing bullets
                # don't break — allow it to pierce multiple enemies

        # Check collision with walls (only if bullet still active)
        if not bullet_hit:
            for wall in current_level.walls:
                if wall.collidepoint(bullet.x, bullet.y):  # ✅ walls are Rects
                    if isinstance(bullet, PlasmaBlob):
                        bullet.explode(puddles)
                    bullet_hit = True
                    break

        # Remove bullet if it hit anything
        if bullet_hit and bullet in player.bullets:
            player.bullets.remove(bullet)

    # --- Puddle and burn updates ---
    for puddle in list(puddles):
        puddle.update(dt)
        
        for enemy in enemies:
            dx = enemy.x - puddle.x
            dy = enemy.y - puddle.y
            dist_sq = dx*dx + dy*dy
            
            if dist_sq <= puddle.radius * puddle.radius:
                # Damage only if cooldown expired
                if enemy.puddle_tick_timer <= 0:
                    # Apply damage per tick
                    tick_damage = puddle.damage_per_second * 0.2
                    enemy.take_damage(tick_damage, player)
                    # Reset tick cooldown
                    enemy.puddle_tick_timer = 0.2
                # Slow effect
                enemy.in_puddle = True
                enemy.puddle_slow = puddle.slow_multiplier
            else:
                # Only unset if enemy is not touching ANY puddle later
                pass

        if not puddle.is_alive():
            puddles.remove(puddle)

    # After checking all puddles, finalize enemy speed multipliers
    for enemy in enemies:
        # Default values (if enemy.x belongs to 0 puddles)
        if not hasattr(enemy, "in_puddle") or not enemy.in_puddle:
            enemy.speed_multiplier = 1.0
        else:
            enemy.speed_multiplier = enemy.puddle_slow

        # Reset markers for next frame
        enemy.in_puddle = False

    for enemy, state in list(burns.items()):
        if enemy not in enemies or not enemy.is_alive():
            enemy.stop_burning()
            burns.pop(enemy, None)
            continue
        enemy.take_damage(state['dps'] * dt, player)
        state['remaining'] -= dt
        if state['remaining'] <= 0:
            enemy.stop_burning()
            burns.pop(enemy, None)
        elif not enemy.is_burning:
            enemy.start_burning()

    enemies = [e for e in enemies if e.is_alive()]

    # --- Level update ---
    new_enemies = current_level.update(dt, player, enemies)
    
    if new_enemies:
        enemies.extend(new_enemies)

    # --- Check level completion ---
    if current_level.completed:
        current_level.stop_ambient()
        current_level_index += 1
        if current_level_index < len(levels):
            current_level = levels[current_level_index]
        else:
            print("You win!")
            running = False
    
    # --- DRAW ---
    current_level.draw(screen, camera_offset)
    player.draw(screen)
    for nest in rat_nests:
        nest.draw(screen, camera_offset)
    for enemy in enemies:
        enemy.draw(screen, camera_offset)
        if isinstance(enemy, BroodFly):
            for proj in enemy.projectiles:
                screen.blit(proj.image, (proj.rect.x - camera_offset[0], proj.rect.y - camera_offset[1]))
    for puddle in puddles:
        puddle.draw(screen, camera_offset[0], camera_offset[1])    
    for barricade in barricades:
        barricade.draw(screen, camera_offset)
        
        # --- DEBUGGING TOOL: Mouse Coordinate Overlay ---
    # Press F3 to toggle on/off
    if not hasattr(pygame, "_show_coords"):
        pygame._show_coords = True  # default on
    if pygame.key.get_pressed()[pygame.K_F3]:
        pygame._show_coords = not getattr(pygame, "_f3_pressed", False)
        pygame._f3_pressed = True
    else:
        pygame._f3_pressed = False

    if getattr(pygame, "_show_coords", False):
        # Get current mouse + world position
        mx, my = pygame.mouse.get_pos()
        world_x = mx + camera_offset[0]
        world_y = my + camera_offset[1]

        # Draw text box at cursor
        font = pygame.font.SysFont("consolas", 18)
        text = font.render(f"({world_x:.0f}, {world_y:.0f})", True, (255, 255, 255))
        bg_rect = text.get_rect(topleft=(mx + 12, my + 12))
        pygame.draw.rect(screen, (0, 0, 0, 150), bg_rect)
        screen.blit(text, (mx + 12, my + 12))

    # Flamethrower cone
    # When drawing:
    if isinstance(player.current_weapon, Flamethrower) and pygame.mouse.get_pressed()[0]:
        player.current_weapon.draw_cone(screen, player.x, player.y, mouse_pos, camera_offset, current_level.walls)


    for pack in health_packs:
        pack.update(player)
        pack.draw(screen, camera_offset)
        
    fog.draw(screen, camera_offset)

    hud.draw(screen)
    
    # Draw exit zone (visual)
    pygame.draw.rect(screen, (0, 255, 0), 
    pygame.Rect(exit_zone.x - camera_offset[0], exit_zone.y - camera_offset[1], exit_zone.width, exit_zone.height), 3)
    pygame.display.flip()

pygame.quit()
