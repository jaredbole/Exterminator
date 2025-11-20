import pygame

class FogOfWar:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        # Full black mask
        self.fog = pygame.Surface((width, height), pygame.SRCALPHA)
        self.fog.fill((0, 0, 0, 255))  # fully opaque

        # Optional blurred reveal brush (soft edges)
        self.reveal_brush = self._make_reveal_brush(220)

    def _make_reveal_brush(self, radius):
        """Create a soft circular brush for smooth fog revealing."""
        brush = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        for r in range(radius, 0, -1):  
            alpha = int(255 * (r / radius))  
            pygame.draw.circle(brush, (0, 0, 0, 255 - alpha), (radius, radius), r)
        return brush

    def reveal_circle(self, x, y, radius=200):
        """Punches a transparent hole around the player."""
        brush = pygame.transform.smoothscale(self.reveal_brush, (radius*2, radius*2))
        self.fog.blit(brush, (x - radius, y - radius), special_flags=pygame.BLEND_RGBA_MIN)

    def reveal_rect(self, rect):
        """Used to instantly reveal full rooms or nest areas."""
        pygame.draw.rect(self.fog, (0, 0, 0, 0), rect)

    def draw(self, screen, camera_offset):
        screen.blit(self.fog, (-camera_offset[0], -camera_offset[1]))

    def reset(self):
        """Restore full fog visibility (reset to completely dark)."""
        self.fog.fill((0, 0, 0, 255))
