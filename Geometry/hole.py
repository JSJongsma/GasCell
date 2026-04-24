#hole.py
# this class will be responsible for defining the geometry of the holes in the cell (entry and exit)
# it will define the position and size of the holes, as well as the shape (circular, rectangular, etc.)


import sys
import os

# Voeg de hoofdmap van het project toe aan het pad (één niveau boven Math)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Math.vector import Vector
from Math.grid import TwoGrid

class Hole:
    def __init__(self, name, origin: Vector, radius: float, grid: TwoGrid):
        self.name = name 
            # 'origin' is hier een Vector(u, v, 0) -> de plek OP de spiegel
        self.origin = origin 
        self.radius = radius 
        self.grid = grid
        
    def __repr__(self):
        return f"Hole('{self.name}', origin={self.origin}, radius={self.size})"
    
    def is_hit(self, u: float, v: float):
        """
        u, v zijn de lokale coördinaten op de spiegel waar de straal inslaat.
        We kijken of die inslag binnen de straal van het gat (self.origin) valt.
        """
        # Bereken afstand tussen inslagpunt (u,v) en het midden van het gat (self.origin.x, self.origin.y)
        du = u - self.origin.x
        dv = v - self.origin.y
        
        distance_sq = du**2 + dv**2
        return distance_sq <= self.radius**2

