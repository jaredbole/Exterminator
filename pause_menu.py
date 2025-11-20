import pygame

class PauseMenu:
    def __init__(self, screen_width, screen_height):
        self.active = False
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Store channels/sounds that were playing when paused
        self.paused_channels = []

        # Menu options
        self.options = ["RESUME", "EXIT"]
        self.selected = 0

        self.font_big = pygame.font.SysFont("consolas", 72)
        self.font_small = pygame.font.SysFont("consolas", 36)

    def toggle(self):
        """Toggle pause state."""
        if self.active:
            self.resume_sounds()
            self.active = False
        else:
            self.pause_sounds()
            self.active = True

    def pause_sounds(self):
        """Pause all currently playing sounds without losing state."""
        self.paused_channels = []
        for ch_idx in range(pygame.mixer.get_num_channels()):
            ch = pygame.mixer.Channel(ch_idx)
            if ch.get_busy():   # If something is playing on that channel
                ch.pause()
                self.paused_channels.append(ch_idx)

    def resume_sounds(self):
        """Resume only the channels that were playing when paused."""
        for ch_idx in self.paused_channels:
            pygame.mixer.Channel(ch_idx).unpause()
        self.paused_channels.clear()

    def handle_input(self, event):
        """Handle arrow keys + Enter while paused."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                return self.options[self.selected]
        return None

    def draw(self, screen):
        """Draw the pause menu UI."""
        # Darken the screen
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        # Title
        title = self.font_big.render("PAUSED", True, (255, 255, 255))
        screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 150))

        # Draw options
        y = 350
        for i, opt in enumerate(self.options):
            color = (255, 255, 0) if i == self.selected else (255, 255, 255)
            txt = self.font_small.render(opt, True, color)
            screen.blit(txt, (self.screen_width // 2 - txt.get_width() // 2, y))
            y += 60
