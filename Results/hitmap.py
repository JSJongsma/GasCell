# hitmap.py
# This class will be responsible for defining the hitmap of a mirror, or even a hole. 
# The hitmap is made up of the grid points of the respective mirror (or hole). Each time a 
# ray hits the mirror, the respective coordinate in the hitmap will be updated.

import sys
import os

# Voeg de hoofdmap van het project toe aan het pad (één niveau boven Math)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Math.vector import Vector
from Math.grid import TwoGrid
from Geometry.mirror import Mirror

class Hitmap:
    def __init__(self, mirror_name, grid: TwoGrid):
        self.mirror_name = mirror_name
        self.grid = grid # We lenen de u_range, v_range en spacing
        
        # Maak een 2D matrix (data grid)
        self.u_bins = int(grid.u_range / grid.spacing)
        self.v_bins = int(grid.v_range / grid.spacing)
        self.data = [[0.0 for _ in range(self.v_bins + 1)] for _ in range(self.u_bins + 1)]  
 
        
    def register_hit(self, u, v, intensity=1.0):
        """Vertaal lokale u,v naar matrix-indices en sla op."""
        
        # EXTRA CHECK: Is het punt wel binnen de ronde spiegel?
        mirror_radius = self.grid.u_range / 2
        if (u**2 + v**2) > mirror_radius**2:
            return False # Hit wordt genegeerd want valt buiten de ronde schijf
        
        i = int((u + self.grid.u_range / 2) / self.grid.spacing)
        j = int((v + self.grid.v_range / 2) / self.grid.spacing)

        if 0 <= i <= self.u_bins and 0 <= j <= self.v_bins:
            self.data[i][j] += intensity # keep track of intensity of hits
            return True
        return False

# To use this class, make a dictionary of each mirror/(exit)hole name, coupled to their own hitmap