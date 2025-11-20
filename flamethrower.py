# flamethrower.py
import math
import pygame
from base_weapon import Weapon

pygame.mixer.init()
FLAME_START_SOUND = pygame.mixer.Sound("assets/audio/flamethrowerStart.wav")
FLAME_LOOP_SOUND   = pygame.mixer.Sound("assets/audio/flamethrowerLoop.wav")
FLAME_END_SOUND = pygame.mixer.Sound("assets/audio/flamethrowerEnd.wav")

FLAME_START_SOUND.set_volume(0.5)
FLAME_LOOP_SOUND.set_volume(0.4)
FLAME_END_SOUND.set_volume(0.5)

class Flamethrower(Weapon):
    def __init__(self,
                 fire_rate=30.0,
                 cone_angle_deg=20.0,
                 max_range=300.0,
                 max_damage=100.0,
                 min_damage=15.0,
                 burn_dps=20.0,
                 burn_duration=5.0):
        super().__init__(fire_rate=fire_rate)

        self.cone_half_rad = math.radians(cone_angle_deg / 2.0)
        self.max_range = float(max_range)
        self.max_damage = float(max_damage)
        self.min_damage = float(min_damage)
        self.burn_dps = float(burn_dps)
        self.burn_duration = float(burn_duration)

        self.cone_color = (255, 160, 40, 90)
        self.outline_color = (255, 200, 80)
        
        self.warmup_time = 1.356
        self.cooldown_time = 0.6
        self.warming_up = False
        self.firing = False
        self.ready_to_fire = False
        self.warmup_timer = 0.0
        self.cooldown_timer = 0.0
        self.loop_channel = None
        self.warmup_channel = None

        # --- Fuel system ---
        self.max_fuel = 100.0
        self.fuel = self.max_fuel
        self.fuel_depletion_rate = 30.0  # units per second while firing
        self.fuel_refill_rate = 40.0     # units per second when not firing

    # -------------------------------------------------------------------------
    def update(self, dt: float):
        super().update(dt)
        # --- Warmup countdown ---
        if self.warming_up:
            self.warmup_timer += dt
            if self.warmup_timer >= self.warmup_time:
                self.warming_up = False
                self.ready_to_fire = True
                # 🔊 Start the looping flame sound
                self.loop_channel = pygame.mixer.find_channel(True)
                if self.loop_channel:
                    self.loop_channel.play(FLAME_LOOP_SOUND, loops=-1)

        # --- Cooldown countdown ---
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt
            if self.cooldown_timer <= 0:
                self.cooldown_timer = 0
                self.ready_to_fire = False
                
        # --- Fuel regeneration when not firing ---
        if not self.firing and not self.warming_up:
            self.fuel = min(self.max_fuel, self.fuel + self.fuel_refill_rate * dt)

    # -------------------------------------------------------------------------
    def _raycast(self, x0, y0, dx, dy, max_dist, walls):
        """Optimized raycast using coarse stepping and bounding box culling."""
        step = 12  # bigger step = fewer checks
        dist = 0.0

        # Only consider walls within a local bounding box (near player)
        ray_box = pygame.Rect(x0 - max_dist, y0 - max_dist, max_dist * 2, max_dist * 2)
        nearby_walls = [w for w in walls if ray_box.colliderect(w)]

        while dist < max_dist:
            test_x = x0 + dx * dist
            test_y = y0 + dy * dist
            point_rect = pygame.Rect(test_x, test_y, 4, 4)
            for wall in nearby_walls:
                if wall.colliderect(point_rect):
                    return dist
            dist += step

        return max_dist


    def _calc_instant_damage(self, distance: float):
        t = max(0.0, min(1.0, distance / max(0.0001, self.max_range)))
        return self.max_damage * (1.0 - t) + self.min_damage * t

    def _point_in_cone(self, src_x, src_y, aim_dx, aim_dy, px, py, visible_range=None):
        vx = px - src_x
        vy = py - src_y
        dist = math.hypot(vx, vy)
        if dist <= 0:
            return True, 0.0
        if visible_range is not None and dist > visible_range:
            return False, dist
        elif visible_range is None and dist > self.max_range:
            return False, dist
        vxn, vyn = vx / dist, vy / dist
        aim_len = math.hypot(aim_dx, aim_dy)
        if aim_len == 0:
            adx, ady = 0.0, -1.0
        else:
            adx, ady = aim_dx / aim_len, aim_dy / aim_len
        dot = max(-1.0, min(1.0, vxn * adx + vyn * ady))
        angle = math.acos(dot)
        return (angle <= self.cone_half_rad), dist

    # -------------------------------------------------------------------------
    def can_hit_point(self, src_x, src_y, mouse_pos, target_x, target_y, walls):
        """
        Determines if a target at (target_x, target_y) is within the cone
        and not blocked by walls. Returns (in_cone, distance, visible_range).
        """
        aim_dx = mouse_pos[0] - src_x
        aim_dy = mouse_pos[1] - src_y
        aim_angle = math.atan2(aim_dy, aim_dx)
        aim_len = math.hypot(aim_dx, aim_dy)
        if aim_len == 0:
            return False, 0.0, 0.0
        dir_x, dir_y = aim_dx / aim_len, aim_dy / aim_len

        center_dist = self._raycast(src_x, src_y, dir_x, dir_y, self.max_range, walls)
        left_angle = aim_angle - self.cone_half_rad
        right_angle = aim_angle + self.cone_half_rad
        left_dist = self._raycast(src_x, src_y, math.cos(left_angle), math.sin(left_angle),
                                  self.max_range, walls)
        right_dist = self._raycast(src_x, src_y, math.cos(right_angle), math.sin(right_angle),
                                   self.max_range, walls)
        visible_range = min(center_dist, left_dist, right_dist)

        in_cone, dist = self._point_in_cone(src_x, src_y, aim_dx, aim_dy,
                                            target_x, target_y, visible_range)
        return in_cone, dist, visible_range

    # -------------------------------------------------------------------------
    def fire(self, x, y, mouse_pos, bullet_list, mouse_held: bool, enemies: list, burns: dict, walls=None, player=None):
        """Handles warmup start, continuous damage, and cooldown sounds."""
        if mouse_held:
            # Stop if out of fuel
            if self.fuel <= 0:
                self.stop_sounds()
                self.firing = False
                self.ready_to_fire = False
                return
            # --- Begin warmup if not already firing ---
            if not self.firing and not self.warming_up:
                self.warming_up = True
                self.warmup_timer = 0.0
                self.ready_to_fire = False
                # 🔊 Start warmup sound on its own channel
                self.warmup_channel = pygame.mixer.find_channel(True)
                if self.warmup_channel:
                    self.warmup_channel.play(FLAME_START_SOUND)

            self.firing = True

            # 🚫 Don't apply damage or visuals during warmup
            if not self.ready_to_fire:
                return

            # ✅ Only apply damage when warmup is complete and there is fuel
            if self.ready_to_fire and self.can_fire():
                # Deplete fuel
                self.fuel = max(0.0, self.fuel - self.fuel_depletion_rate * (1.0 / self.fire_rate))
                if self.fuel <= 0:
                    # Stop firing if empty
                    self.stop_sounds()
                    self.firing = False
                    self.ready_to_fire = False
                    FLAME_END_SOUND.play()
                    return
                for enemy in list(enemies):
                    ex = enemy.x + enemy.size / 2.0
                    ey = enemy.y + enemy.size / 2.0
                    in_cone, dist, visible_range = self.can_hit_point(
                        x, y, mouse_pos, ex, ey, walls or []
                    )
                    if in_cone:
                        damage = self._calc_instant_damage(dist)
                        enemy.take_damage(damage, player)
                        burns[enemy] = {
                            "remaining": self.burn_duration,
                            "dps": self.burn_dps,
                        }
                self.timer = self.cooldown

        else:
            # --- Fire button released mid-warmup or firing ---
            if self.firing or self.warming_up:
                self.firing = False
                self.warming_up = False
                self.ready_to_fire = False
                self.warmup_timer = 0.0

                # 🔊 Stop warmup sound immediately if it was still playing
                if self.warmup_channel:
                    self.warmup_channel.stop()
                    self.warmup_channel = None

                # 🔊 Stop loop sound if it was running
                if self.loop_channel:
                    self.loop_channel.stop()
                    self.loop_channel = None

                # Play cooldown sound only if it actually reached fire state
                if self.cooldown_timer <= 0 and not self.warming_up:
                    FLAME_END_SOUND.play()
                self.cooldown_timer = self.cooldown_time


    # -------------------------------------------------------------------------
    def stop_sounds(self):
        """Stops any active flamethrower sounds (loop, warmup, cooldown)."""
        if self.warmup_channel:
            self.warmup_channel.stop()
            self.warmup_channel = None
        if self.loop_channel:
            self.loop_channel.stop()
            self.loop_channel = None
    # -------------------------------------------------------------------------
    def get_fuel_ratio(self):
        """Returns a normalized 0–1 value for HUD display."""
        return self.fuel / self.max_fuel

    # -------------------------------------------------------------------------
    def draw_cone(self, surface, x, y, mouse_pos, camera_offset=(0, 0), walls=None):
        # Don't draw during warmup
        if not self.ready_to_fire:
            return
        cam_x, cam_y = camera_offset
        screen_x, screen_y = x - cam_x, y - cam_y
        screen_mouse_x, screen_mouse_y = mouse_pos[0] - cam_x, mouse_pos[1] - cam_y
        aim_dx, aim_dy = screen_mouse_x - screen_x, screen_mouse_y - screen_y
        aim_angle = math.atan2(aim_dy, aim_dx)

        if walls:
            dir_x, dir_y = math.cos(aim_angle), math.sin(aim_angle)
            center_dist = self._raycast(x, y, dir_x, dir_y, self.max_range, walls)
            left_angle = aim_angle - self.cone_half_rad
            right_angle = aim_angle + self.cone_half_rad
            left_dist = self._raycast(x, y, math.cos(left_angle), math.sin(left_angle), self.max_range, walls)
            right_dist = self._raycast(x, y, math.cos(right_angle), math.sin(right_angle), self.max_range, walls)
            visible_range = min(center_dist, left_dist, right_dist)
        else:
            visible_range = self.max_range

        left_angle = aim_angle - self.cone_half_rad
        right_angle = aim_angle + self.cone_half_rad
        left_x = screen_x + math.cos(left_angle) * visible_range
        left_y = screen_y + math.sin(left_angle) * visible_range
        right_x = screen_x + math.cos(right_angle) * visible_range
        right_y = screen_y + math.sin(right_angle) * visible_range

        tri_points = [(int(screen_x), int(screen_y)),
                      (int(left_x), int(left_y)),
                      (int(right_x), int(right_y))]

        bbox_size = int(self.max_range * 2) + 8
        surf = pygame.Surface((bbox_size, bbox_size), pygame.SRCALPHA)
        offset_x, offset_y = screen_x - (bbox_size // 2), screen_y - (bbox_size // 2)
        rel_points = [(px - offset_x, py - offset_y) for (px, py) in tri_points]
        pygame.draw.polygon(surf, self.cone_color, rel_points)
        pygame.draw.polygon(surf, self.outline_color, rel_points, 1)
        surface.blit(surf, (offset_x, offset_y))
