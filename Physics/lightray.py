# lightray
# this class defines the input (and output) of the simulation. The lightray has a certain intensity and a certain direction.
# It is meant as the pure in and output of the simulation. We will give the gas_cell a lightray as input,
# And the gas_cell will return a lightray as output.

import sys
import os

# Voeg de hoofdmap van het project toe aan het pad (één niveau boven Math)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Math.vector import Vector

class Lightray:
    def __init__(self, origin: Vector, direction: Vector, intensity: float=1):
        self.origin = origin          # Startpunt (meestal de inlet)
        self.direction = direction.normalize() # De wavevector k
        self.intensity = intensity    # Start intensiteit (bijv. 1.0 of 100%)
        
        # De uiteindelijke output karakteristieken
        self.total_path_length = 0.0
        self.is_extinguished = False # Voor als de intensiteit 0 wordt of de straal 'verdwaalt'

    def __repr__(self):
        return (f"Lightray(pos={self.origin}, dir={self.direction}, "
                f"I={self.intensity:.4f}, L={self.total_path_length:.2f})")