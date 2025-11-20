import pygame
import math
import random


def has_line_of_sight(enemy, player, walls):
    """Return True if no wall blocks a straight line between enemy and player."""
    ex, ey = enemy.x, enemy.y
    px, py = player.x, player.y
    dx, dy = px - ex, py - ey
    dist = math.hypot(dx, dy)
    if dist < 1e-3:
        return True

    step = 8
    steps = max(1, int(dist / step))
    nx, ny = dx / dist, dy / dist

    for i in range(steps + 1):
        x = ex + nx * i * step
        y = ey + ny * i * step
        point = pygame.Rect(x, y, 2, 2)
        if any(point.colliderect(w) for w in walls):
            return False

    return True


def move_away_from_player(enemy, player, speed, dt, walls=None, barricades=None, jitter=0.1):
    """
    Move smoothly away from the player with optional jitter to prevent stalling.
    """
    # Vector pointing from player → enemy
    direction = pygame.Vector2(enemy.x - player.x, enemy.y - player.y)
    if direction.length_squared() == 0:
        # random direction if overlapping
        direction = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
    direction = direction.normalize()

    # ✅ Small random jitter angle to avoid freezing on straight axis
    jitter_angle = random.uniform(-jitter, jitter)
    direction.rotate_ip(math.degrees(jitter_angle))

    new_x = enemy.x + direction.x * speed * dt
    new_y = enemy.y + direction.y * speed * dt

    obstacles = list(walls or [])
    if barricades:
        obstacles += [b.rect for b in barricades if getattr(b, "active", False)]

    # Slide on X
    rect_x = pygame.Rect(new_x - enemy.rect.width / 2, enemy.y - enemy.rect.height / 2,
                         enemy.rect.width, enemy.rect.height)
    if not any(rect_x.colliderect(o) for o in obstacles):
        enemy.x = new_x

    # Slide on Y
    rect_y = pygame.Rect(enemy.x - enemy.rect.width / 2, new_y - enemy.rect.height / 2,
                         enemy.rect.width, enemy.rect.height)
    if not any(rect_y.colliderect(o) for o in obstacles):
        enemy.y = new_y

    enemy.rect.center = (enemy.x, enemy.y)


def maintain_range_from_player(enemy, player, min_dist, max_dist, speed, dt, walls=None, barricades=None):
    """
    Keeps the enemy roughly between [min_dist, max_dist].
    Adds continuous gentle retreat when too close, instead of stopping.
    """
    dx = enemy.x - player.x
    dy = enemy.y - player.y
    dist = math.hypot(dx, dy)

    inner_soft = min_dist - 20  # start backing up before getting too close
    outer_soft = max_dist + 50

    if dist < inner_soft:
        # retreat harder the closer you are
        retreat_factor = 2.0 + (inner_soft - dist) / inner_soft
        move_away_from_player(enemy, player, speed * retreat_factor, dt, walls, barricades)
    elif dist > outer_soft:
        # move toward player only if well outside range
        direction = pygame.Vector2(player.x - enemy.x, player.y - enemy.y)
        if direction.length_squared() == 0:
            return dist
        direction = direction.normalize()
        new_x = enemy.x + direction.x * (speed * 0.7) * dt
        new_y = enemy.y + direction.y * (speed * 0.7) * dt

        obstacles = list(walls or [])
        if barricades:
            obstacles += [b.rect for b in barricades if getattr(b, "active", False)]

        rect_x = pygame.Rect(new_x - enemy.rect.width / 2, enemy.y - enemy.rect.height / 2,
                             enemy.rect.width, enemy.rect.height)
        if not any(rect_x.colliderect(o) for o in obstacles):
            enemy.x = new_x

        rect_y = pygame.Rect(enemy.x - enemy.rect.width / 2, new_y - enemy.rect.height / 2,
                             enemy.rect.width, enemy.rect.height)
        if not any(rect_y.colliderect(o) for o in obstacles):
            enemy.y = new_y

        enemy.rect.center = (enemy.x, enemy.y)

    else:
        # gentle drift to maintain distance if within comfort zone
        enemy.rect.center = (enemy.x, enemy.y)

    return dist
