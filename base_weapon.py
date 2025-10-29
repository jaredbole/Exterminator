import math

class Weapon:
    def __init__(self, fire_rate: float):
        self.fire_rate = fire_rate               # shots per second
        self.cooldown = 1.0 / fire_rate
        self.timer = 0.0

    def update(self, dt: float):
        if self.timer > 0:
            self.timer -= dt

    def can_fire(self) -> bool:
        return self.timer <= 0

    def fire(self, x, y, mouse_pos, bullet_list):
        """Override in subclasses to spawn bullets"""
        pass
