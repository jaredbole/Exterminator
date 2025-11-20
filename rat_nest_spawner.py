# rat_nest_spawner.py
from rat_nest import RatNest

def create_rat_nests(level_name):
    """Return a list of RatNest objects for the specified level."""
    nests = []
    if level_name == "Infested Apartment Complex":
        nests = [
            RatNest(1000, 1300),		# Kitchen 1
            RatNest(1000, 700),			# Larger APT 1
            RatNest(600, 970),
            RatNest(200, 1100),			# Larger APT 2
            RatNest(100, 700),
            RatNest(200, 300),
            RatNest(1300, 970),			# Storage Closet
            RatNest(1800, 1350),			#room opposite closet
            RatNest(2000, 1350),		#Backtrack Section
            RatNest(2400, 1450),
            RatNest(2050, 900),
            RatNest(2350, 750),
            RatNest(2300, 550),			# Final Boss Annex
            RatNest(2300, 150),
            RatNest(2000, 550),
            RatNest(2000, 150)
        ]
    return nests
