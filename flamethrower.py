# flamethrower.py
import math
import pygame
from base_weapon import Weapon

class Flamethrower(Weapon):
    def __init__(self,
                 fire_rate=30.0,        # how many "checks" per second while holding (higher -> smoother)
                 cone_angle_deg=45.0,   # full cone angle (degrees)
                 max_range=200.0,       # px
                 max_damage=18.0,       # direct damage at point-blank (applied per hit-check)
                 min_damage=3.0,        # damage at max_range (instant)
                 burn_dps=6.0,          # damage per second from burn
                 burn_duration=4.0      # seconds of burn applied/refreshed on hit
                 ):
        super().__init__(fire_rate=fire_rate)

        # cone parameters
        self.cone_half_rad = math.radians(cone_angle_deg / 2.0)
        self.max_range = float(max_range)

        # damage parameters (instant + DoT)
        self.max_damage = float(max_damage)
        self.min_damage = float(min_damage)
        self.burn_dps = float(burn_dps)
        self.burn_duration = float(burn_duration)

        # visual settings
        self.cone_color = (255, 160, 40, 90)  # RGBA for drawing cone
        self.outline_color = (255, 200, 80)

    def update(self, dt: float):
        super().update(dt)

    def _point_in_cone(self, src_x, src_y, aim_dx, aim_dy, px, py):
        """Return (in_cone (bool), distance (float))"""
        vx = px - src_x
        vy = py - src_y
        dist = math.hypot(vx, vy)
        if dist <= 0:
            return True, 0.0
        if dist > self.max_range:
            return False, dist

        # normalize
        vxn = vx / dist
        vyn = vy / dist
        aim_len = math.hypot(aim_dx, aim_dy)
        if aim_len == 0:
            adx, ady = 0.0, -1.0
        else:
            adx, ady = aim_dx / aim_len, aim_dy / aim_len

        dot = max(-1.0, min(1.0, vxn * adx + vyn * ady))
        angle = math.acos(dot)
        return (angle <= self.cone_half_rad), dist

    def _calc_instant_damage(self, distance: float):
        """Linear falloff from max_damage at distance 0 to min_damage at max_range."""
        t = max(0.0, min(1.0, distance / max(0.0001, self.max_range)))
        return self.max_damage * (1.0 - t) + self.min_damage * t

    def fire(self, x, y, mouse_pos, bullet_list, mouse_held: bool, enemies: list, burns: dict):
        """Applies area-of-effect damage + burn within a cone."""
        if not mouse_held or not self.can_fire():
            return

        aim_dx = mouse_pos[0] - x
        aim_dy = mouse_pos[1] - y

        for enemy in list(enemies):
            ex = enemy.x + enemy.size / 2.0
            ey = enemy.y + enemy.size / 2.0
            in_cone, dist = self._point_in_cone(x, y, aim_dx, aim_dy, ex, ey)
            if in_cone:
                damage = self._calc_instant_damage(dist)
                enemy.take_damage(damage)
                burns[enemy] = {'remaining': self.burn_duration, 'dps': self.burn_dps}

        self.timer = self.cooldown

    def draw_cone(self, surface, x, y, mouse_pos, camera_offset=(0, 0)):
        """
        Draw a translucent cone relative to the camera.
        mouse_pos is expected to be in world coordinates.
        """
        cam_x, cam_y = camera_offset

        # Convert player and mouse to screen-space for drawing
        screen_x = x - cam_x
        screen_y = y - cam_y
        screen_mouse_x = mouse_pos[0] - cam_x
        screen_mouse_y = mouse_pos[1] - cam_y

        aim_dx = screen_mouse_x - screen_x
        aim_dy = screen_mouse_y - screen_y
        aim_angle = math.atan2(aim_dy, aim_dx)

        left_angle = aim_angle - self.cone_half_rad
        right_angle = aim_angle + self.cone_half_rad

        left_x = screen_x + math.cos(left_angle) * self.max_range
        left_y = screen_y + math.sin(left_angle) * self.max_range
        right_x = screen_x + math.cos(right_angle) * self.max_range
        right_y = screen_y + math.sin(right_angle) * self.max_range

        tri_points = [
            (int(screen_x), int(screen_y)),
            (int(left_x), int(left_y)),
            (int(right_x), int(right_y))
        ]

        # Draw on temporary surface with alpha
        bbox_size = int(self.max_range * 2) + 8
        surf = pygame.Surface((bbox_size, bbox_size), pygame.SRCALPHA)
        offset_x = screen_x - (bbox_size // 2)
        offset_y = screen_y - (bbox_size // 2)

        rel_points = [(px - offset_x, py - offset_y) for (px, py) in tri_points]
        pygame.draw.polygon(surf, self.cone_color, rel_points)
        pygame.draw.polygon(surf, self.outline_color, rel_points, 1)
        surface.blit(surf, (offset_x, offset_y))

