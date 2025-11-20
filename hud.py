import pygame

class HUD:
    def __init__(self, player, screen_width, screen_height):
        self.player = player
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Fonts
        self.font_small = pygame.font.Font(None, 28)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_large = pygame.font.Font(None, 48)
        
        # Health bar setup
        self.health_bar_width = 200
        self.health_bar_height = 20
        self.health_bar_pos = (30, 30)

        # Objective info
        self.objective_text = "Destroy all nests"
        self.total_nests = 0
        self.active_nests = 0

        # Ammo display position
        self.ammo_pos = (30, 65)
        
    def update_objective_progress(self, active_nests, total_nests):
        """Update objective info dynamically based on nest count."""
        self.active_nests = active_nests
        self.total_nests = total_nests

        if active_nests > 0:
            self.objective_text = f"Destroy all nests: {total_nests - active_nests}/{total_nests} cleared"
        else:
            self.objective_text = "All nests destroyed! Find the exit."

    def set_objective(self, text):
        """Update the objective text dynamically."""
        self.objective_text = text

    def draw_health_bar(self, surface):
        """Draw a simple health bar."""
        x, y = self.health_bar_pos
        ratio = max(self.player.health / self.player.max_health, 0)
        
        # Outline
        pygame.draw.rect(surface, (255, 255, 255), (x - 2, y - 2, self.health_bar_width + 4, self.health_bar_height + 4), 2)
        
        # Background
        pygame.draw.rect(surface, (60, 60, 60), (x, y, self.health_bar_width, self.health_bar_height))
        
        # Health fill
        fill_width = int(self.health_bar_width * ratio)
        color = (220 - int(120 * ratio), int(200 * ratio), 50)  # shifts from red to green
        pygame.draw.rect(surface, color, (x, y, fill_width, self.health_bar_height))

        # Text overlay
        text = self.font_small.render(f"HP: {self.player.health}/{self.player.max_health}", True, (255, 255, 255))
        surface.blit(text, (x + self.health_bar_width + 10, y - 2))

    def draw_ammo(self, surface):
        """Draw ammo or fuel info depending on weapon type."""
        weapon = self.player.current_weapon
        x, y = self.ammo_pos

        # --- Flamethrower: show fuel percentage + horizontal bar ---
        if weapon.__class__.__name__ == "Flamethrower":
            fuel_ratio = weapon.get_fuel_ratio() if hasattr(weapon, "get_fuel_ratio") else 1.0
            fuel_percent = int(fuel_ratio * 100)
            text_surface = self.font_medium.render(f"Fuel: {fuel_percent}%", True, (255, 200, 100))
            surface.blit(text_surface, (x, y))

            # Fuel bar dimensions
            bar_width = 180
            bar_height = 14
            bar_y = y + 32  # slightly below the text

            # Outline
            pygame.draw.rect(surface, (255, 255, 255), (x - 2, bar_y - 2, bar_width + 4, bar_height + 4), 2)
            # Background
            pygame.draw.rect(surface, (40, 40, 40), (x, bar_y, bar_width, bar_height))

            # Fill color shifts from red (empty) to orange to yellow
            fill_color = (
                int(255 - 155 * fuel_ratio),
                int(150 + 80 * fuel_ratio),
                60
            )
            fill_width = int(bar_width * fuel_ratio)
            pygame.draw.rect(surface, fill_color, (x, bar_y, fill_width, bar_height))

        # --- Other weapons: show ammo count ---
        elif hasattr(weapon, "ammo") and hasattr(weapon, "max_ammo"):
            ammo_text = f"Ammo: {weapon.ammo}/{weapon.max_ammo}"
            text_surface = self.font_medium.render(ammo_text, True, (255, 255, 255))
            surface.blit(text_surface, (x, y))

        # --- Infinite weapons ---
        else:
            text_surface = self.font_medium.render("Ammo: ∞", True, (255, 255, 255))
            surface.blit(text_surface, (x, y))


    def draw_objective(self, surface):
        """Draw the current objective centered near the top of the screen."""
        text_surface = self.font_large.render(self.objective_text, True, (255, 220, 80))
        text_rect = text_surface.get_rect(center=(self.screen_width // 2, 40))
        surface.blit(text_surface, text_rect)

    def draw(self, surface):
        """Master draw function."""
        self.draw_health_bar(surface)
        self.draw_ammo(surface)
        self.draw_objective(surface)
