#cell_geometry.py 
# This class will be responsible for defining the geometry of the cell.
# this includes the positions/orientations of the mirrors, size of the cell
# and the inlet and outlet positions. This makes it easier to change the 
# geometry of the cell without having to change the main simulation code. 
# It also makes it easier to visualize the geometry of the cell.

import sys
import os

# Voeg de hoofdmap van het project toe aan het pad (één niveau boven Math)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Math.vector import Vector
from Math.grid import TwoGrid
from Geometry.mirror import Mirror

class CellGeometry:
    def __init__(self, name, cell_dimensions):
        self.name = name # to identify a geometry.
        self.cell_dimensions = cell_dimensions # (length, width, height) of the cell
        self.mirrors = [] # list of mirrors in cell.
        self.inlet_position = None # position of inlet in world coordinates
        self.outlet_position = None # position of outlet in world coordinates

    def __repr__(self):
        return f"CellGeometry(name={self.name}, mirrors={self.mirrors}, inlet_position={self.inlet_position}, outlet_position={self.outlet_position}, cell_dimensions={self.cell_dimensions})"
    
    def add_mirror(self, mirror: Mirror):
            """Voegt een mirror toe die al zijn eigen locatie en normaal heeft."""
            if not isinstance(mirror, Mirror):
                raise TypeError("Mirror must be an instance of the Mirror class.")
            
            if mirror.origin.x < 0 or mirror.origin.x > self.cell_dimensions[0] or \
               mirror.origin.y < 0 or mirror.origin.y > self.cell_dimensions[1] or \
                mirror.origin.z < 0 or mirror.origin.z > self.cell_dimensions[2]:
                 raise ValueError("Mirror origin must be within the cell dimensions.")
            
            self.mirrors.append(mirror)
            
    def get_mirrors(self):
        return self.mirrors
    
    def return_name(self):
        return self.name
    
    def add_inlet(self, position: Vector):
        if not isinstance(position, Vector):
            raise TypeError("position must be a Vector object")
        
        if self.inlet_position is not None:
            raise ValueError("An inlet position is already defined for this cell.")
        
        self.inlet_position = position
    
    def add_outlet(self, position: Vector):
        if not isinstance(position, Vector):
            raise TypeError("position must be a Vector object")
        
        # if an outlet is already defined, raise an error
        if self.outlet_position is not None:
            raise ValueError("An outlet position is already defined for this cell.")
        
        self.outlet_position = position
    
    def get_inlet_position(self):
        return self.inlet_position
    
    def get_outlet_position(self):
        return self.outlet_position
    
    
if __name__ == "__main__":
    cell1 = CellGeometry("Cell1", inlet_position=Vector(0,0,0,), outlet_position=Vector(1,0,0), cell_dimensions=(1,1,1))
    cell1.add_mirror(Mirror(name='mirror1', grid=TwoGrid(2,2,0.5), reflection_coef=1, origin=Vector(0,0,0), normal=Vector(0,0,1)))
    cell1.add_inlet(position=Vector(0,0,0))
