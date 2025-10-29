from dataclasses import dataclass

@dataclass
class BulletStats:
    speed: float
    damage: int
    lifetime: float = 2.0
    def __init__(self, speed=500, damage=10):
        self.speed = speed
        self.damage = damage