# rat_nest.py
import pygame
import random
import enemy  # dynamically access BURN_FRAMES and use same burn logic
from rat_enemy import RatEnemy
from brood_fly import BroodFly
from enemy_ai_utils import has_line_of_sight
from health_pack import HealthPack

class SmokeParticle:
    """Simple rising smoke particle for angry nest visual."""
    def __init__(self, x, y):
        self.x = x + random.randint(-10, 10)
        self.y = y + random.randint(-5, 5)
        self.radius = random.randint(4, 10)
        self.alpha = 180
        self.lifetime = random.uniform(0.8, 1.6)
        self.elapsed = 0.0
        self.rise_speed = random.uniform(20, 40)
        self.fade_rate = random.uniform(100, 130)

    def update(self, dt):
        self.elapsed += dt
        self.y -= self.rise_speed * dt
        self.alpha -= self.fade_rate * dt
        return self.alpha > 0 and self.elapsed < self.lifetime

    def draw(self, surface, camera_offset=(0, 0)):
        cam_x, cam_y = camera_offset
        if self.alpha > 0:
            s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (80, 80, 80, int(self.alpha)), (self.radius, self.radius), self.radius)
            surface.blit(s, (self.x - self.radius - cam_x, self.y - self.radius - cam_y))

class RatNest:
    def __init__(self, x, y, health=300, spawn_interval=4000, max_spawned_rats=5, max_spawned_flies = 3):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = health
        self.active = True
        self.spawn_interval = spawn_interval
        self.last_spawn_time = pygame.time.get_ticks()
        self.max_spawned_rats = max_spawned_rats
        self.last_fly_spawn_time = pygame.time.get_ticks()
        self.fly_spawn_interval = spawn_interval * 1.8
        self.max_spawned_flies = max_spawned_flies
        # --- Animated Nest Frames ---
        # --- Animated Nest Frames ---
        self.nest_frames = []
        for i in range(6):
            try:
                frame = pygame.image.load(f"assets/ratNest/ratNest_{i}.png").convert_alpha()
                self.nest_frames.append(frame)
            except:
                print(f"⚠ Missing nest frame: ratNest_{i}.png")

        # Fallback (ensure no crashes)
        if not self.nest_frames:
            fallback = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.circle(fallback, (80, 40, 0), (40, 40), 40)
            self.nest_frames = [fallback]

        # --- Animation state ---
        self.frame_speed = 0.34     # normal animation speed
        self.angry_frame_speed = 0.15  # faster animation when angry
        self.frame_timer = 0.0

        # Randomize starting frame so nests are not synced
        self.frame_index = random.randint(0, len(self.nest_frames) - 1)
        self.image = self.nest_frames[self.frame_index]

        self.rect = self.image.get_rect(center=(x, y))


        # 🔥 Borrow burn state system from Enemy
        self.is_burning = False
        self.burn_state = None  # 'start', 'loop', 'end'
        self.burn_timer = 0.0
        self.burn_frame = 0

        # Burn damage parameters
        self.burn_dps = 0.0
        self.burn_duration = 0.0
        
        # Angry state & smoke
        self.is_angry = False
        self.smoke_particles: list[SmokeParticle] = []
        self.smoke_timer = 0.0
        self.smoke_interval = 0.08  # seconds between new smoke particles

    # ----------------------------------------------------------------
    def update(self, dt, enemies_list, walls=None, player=None):
        self.animate(dt)
        # --- Update burning animation + damage ---
        if self.is_burning:
            self.update_burning(dt)
            self.burn_duration -= dt
            self.take_damage(self.burn_dps * dt)
            if self.burn_duration <= 0:
                self.stop_burning()

        if not self.active:
            return

        # --- Adaptive behavior based on player proximity & line of sight ---
        base_interval = self.spawn_interval
        base_range = 500
        effective_interval = base_interval
        effective_range = base_range
        self.is_angry = False

        if player:
            dx = player.x - self.x
            dy = player.y - self.y
            distance = (dx**2 + dy**2)**0.5

            # Check line of sight to player
            can_see_player = has_line_of_sight(self, player, walls) if walls else True

            if can_see_player:
                # When player is visible and near, spawn faster and reduce nearby-rat awareness
                if distance < 600:
                    self.is_angry = True
                    proximity_factor = max(0.3, distance / 600)  # 0.3–1.0 scaling
                    effective_interval = base_interval * proximity_factor
                    effective_range = base_range * proximity_factor
            else:
                # If the player is hidden behind walls, revert to calm state
                effective_interval = base_interval
                effective_range = base_range

        # --- Spawn rats periodically ---
        now = pygame.time.get_ticks()
        nearby_rats = [
            e for e in enemies_list
            if isinstance(e, RatEnemy)
            and (abs(e.x - self.x) < effective_range and abs(e.y - self.y) < effective_range)
        ]

        if now - self.last_spawn_time > effective_interval and len(nearby_rats) < self.max_spawned_rats:
            self.spawn_enemy(RatEnemy, enemies_list, walls)
            self.last_spawn_time = now
            
        # --- Brood fly spawn ---
        nearby_flies = [
            e for e in enemies_list
            if isinstance(e, BroodFly)
            and (abs(e.x - self.x) < base_range and abs(e.y - self.y) < base_range)
        ]
        if now - self.last_fly_spawn_time > self.fly_spawn_interval and len(nearby_flies) < self.max_spawned_flies:
            if player and can_see_player and random.random() < 0.6:  # only spawn flies when player is near
                self.spawn_enemy(BroodFly, enemies_list, walls)
                self.last_fly_spawn_time = now
                
        # --- Update smoke if angry ---
        if self.is_angry:
            self.smoke_timer += dt
            if self.smoke_timer >= self.smoke_interval:
                self.smoke_timer = 0.0
                self.smoke_particles.append(SmokeParticle(self.x, self.y - 20))

        self.smoke_particles = [p for p in self.smoke_particles if p.update(dt)]

    # ----------------------------------------------------------------
    def spawn_enemy(self, enemy_class, enemies_list, walls=None):
        """Spawn an enemy near the nest without clipping into walls."""
        max_attempts = 10
        for _ in range(max_attempts):
            offset_x = random.randint(-100, 100)
            offset_y = random.randint(-100, 100)
            spawn_x = self.x + offset_x
            spawn_y = self.y + offset_y

            enemy_size = 24
            spawn_rect = pygame.Rect(spawn_x - enemy_size / 2, spawn_y - enemy_size / 2, enemy_size, enemy_size)

            if walls and any(spawn_rect.colliderect(w) for w in walls):
                continue  # retry

            enemies_list.append(enemy_class(spawn_x, spawn_y))
            return  # success

        print(f"⚠️ RatNest at ({self.x:.0f}, {self.y:.0f}) could not find clear spawn spot for {enemy_class.__name__}.")
    def take_damage(self, dmg, health_packs_list=None):
        if not self.active:
            return
        self.health -= dmg
        if self.health <= 0:
            self.destroy(health_packs_list)

    def destroy(self, health_packs_list):
        self.active = False
        if health_packs_list is not None and random.random() < 0.5:
            health_packs_list.append(HealthPack(self.x, self.y))
        self.smoke_particles.clear()
        print("💥 Rat Nest destroyed!")

    # ----------------------------------------------------------------
    # 🔥 Unified burning system (same as Enemy)
    def start_burning(self, dps, duration):
        if not self.is_burning:
            self.is_burning = True
            self.burn_state = "start"
            self.burn_frame = 0
            self.burn_timer = 0.0
            self.burn_dps = dps
            self.burn_duration = duration
            print("🔥 Rat Nest ignited!")

    def stop_burning(self):
        if self.is_burning and self.burn_state != "end":
            self.burn_state = "end"
            self.burn_frame = 0
            self.burn_timer = 0.0
            self.is_burning = True  # stay visible until end sequence done
            print("🔥 Rat Nest extinguished")

    def update_burning(self, dt):
        if not self.is_burning or not self.burn_state:
            return
        frames = enemy.BURN_FRAMES[self.burn_state]
        frame_count = len(frames)
        frame_speed = 10  # frames per second
        self.burn_timer += dt * frame_speed

        if self.burn_timer >= 1:
            self.burn_frame += int(self.burn_timer)
            self.burn_timer %= 1

            if self.burn_state == "start" and self.burn_frame >= frame_count:
                self.burn_state = "loop"
                self.burn_frame = 0
            elif self.burn_state == "end" and self.burn_frame >= frame_count:
                self.is_burning = False
                self.burn_state = None
                self.burn_frame = 0

        if self.burn_state == "loop":
            self.burn_frame %= frame_count
            
    def animate(self, dt):
        """Animate the nest's idle looping animation (faster when angry)."""
        if not self.active:
            return

        # Choose animation speed based on angry state
        speed = self.angry_frame_speed if self.is_angry else self.frame_speed

        self.frame_timer += dt
        if self.frame_timer >= speed:
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.nest_frames)
            self.image = self.nest_frames[self.frame_index]

        # Keep rect centered
        self.rect = self.image.get_rect(center=(self.x, self.y))


    # ----------------------------------------------------------------
    def draw(self, surface, camera_offset=(0, 0)):
        cam_x, cam_y = camera_offset
        rect = self.rect.move(-cam_x, -cam_y)
        if self.active:
            surface.blit(self.image, rect)

        # 🔥 Draw fire overlay if burning
        if self.is_burning and self.burn_state:
            frames = enemy.BURN_FRAMES[self.burn_state]
            frame_index = min(self.burn_frame, len(frames) - 1)
            frame = frames[frame_index]

            # 🔥 Scale fire relative to nest size
            base_flame_size = 30
            scale_factor = self.rect.width / 30.0  # nest is ~80px wide
            scaled_size = int(base_flame_size * scale_factor)
            scaled_frame = pygame.transform.scale(frame, (scaled_size, scaled_size))

            flame_rect = scaled_frame.get_rect(center=rect.center)
            flame_rect.centery -= self.rect.height // 6  # move slightly up
            surface.blit(scaled_frame, flame_rect)
            
        # Smoke draw (only while angry)
        for particle in self.smoke_particles:
            particle.draw(surface, camera_offset)

        # Health bar
        if self.active:
            bar_width, bar_height = 60, 6
            health_ratio = max(0, self.health / self.max_health)
            bar_x = rect.centerx - bar_width // 2
            bar_y = rect.top - 10
            pygame.draw.rect(surface, (60, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(surface, (200, 0, 0), (bar_x, bar_y, bar_width * health_ratio, bar_height))
