# barricade.py
import pygame

class Barricade:
    def __init__(self, x, y, width, height, nests_required_to_clear, image_path=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.nests_required_to_clear = nests_required_to_clear
        self.active = True
        self.image = None
        self.has_played_sound = False

        if image_path:
            try:
                self.image = pygame.image.load(image_path).convert_alpha()
            except:
                self.image = pygame.Surface((width, height))
                self.image.fill((120, 70, 30))  # fallback brown barricade
        else:
            self.image = pygame.Surface((width, height))
            self.image.fill((120, 70, 30))

        # Optional crumble sound
        try:
            self.break_sound = pygame.mixer.Sound("assets/audio/barricade_break.wav")
        except:
            self.break_sound = None

    def update(self, active_nests):
        """Deactivate barricade when enough nests are destroyed."""
        if active_nests <= self.nests_required_to_clear and self.active:
            self.active = False
            if self.break_sound and not self.has_played_sound:
                self.break_sound.play()
                self.has_played_sound = True

    def draw(self, screen, camera_offset):
        if not self.active:
            return
        cam_x, cam_y = camera_offset
        screen.blit(self.image, (self.rect.x - cam_x, self.rect.y - cam_y))

    def blocks_movement(self):
        return self.active
