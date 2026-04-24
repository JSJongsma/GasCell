import sys
import os

# Voeg de hoofdmap van het project toe aan het pad (één niveau boven Math)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Nu kun je specifiek de CLASSES importeren die je nodig hebt:
from Math.vector import Vector
from Math.matrix import Matrix
from Math.grid import TwoGrid
from Geometry.hole import Hole

class Mirror:
    # has a location, defined by a vector, to define the normal of the twogrid.
    # Has a rotation in the geometry, defined by a matrix, to define the local to world transformation of the twogrid.
    def __init__(self, name, origin: Vector, normal: Vector, grid: TwoGrid, reflection_coef = 1, hole: Hole = None):
        self.reflection_coefficient = reflection_coef # value between 1 and 0
        self.name = name
        self.origin = origin
        self.normal = normal.normalize() # ensure the normal is a unit vector
        self.grid = grid
        self.hole = hole # optional hole in the mirro, defined by a Hole object. If None, there is no hole.
        # Create the world->local transformation matrix based on the normal vector.
        # Rows are the local basis vectors [u, v, n] expressed in world coordinates.
        self.world_to_local = Matrix.from_normal(self.normal)
        self.local_u = Vector(self.world_to_local.m[0][0], self.world_to_local.m[0][1], self.world_to_local.m[0][2])
        self.local_v = Vector(self.world_to_local.m[1][0], self.world_to_local.m[1][1], self.world_to_local.m[1][2])
        self.local_n = Vector(self.world_to_local.m[2][0], self.world_to_local.m[2][1], self.world_to_local.m[2][2])
        self.local_to_world = self.world_to_local.transpose()
        
    def get_local_axes(self):
        """Return de lokale basisas van de spiegel in wereldcoördinaten."""
        return self.local_u, self.local_v, self.local_n

    def get_local_coordinates(self, world_point: Vector):
        """Vertaal een 3D punt naar de coordinaten stelsel (u,v) van de mirror"""
        #world_point is de locatie in de geometry van de mirror
        # 1. Verschuif punt relatief naar de oorsprong van de spiegel
        relative_point = world_point - self.origin #vector
        
        # 2. Roteer naar het lokale stelsel with 
        local_point = self.world_to_local @ relative_point #vector in local coordinates
        
        # local_point.x is 'u', local_point.y is 'v', local_point.z zou ~0 moeten zijn
        return local_point.x, local_point.y
    
    def is_hit(self, world_point: Vector):
        u, v = self.get_local_coordinates(world_point)
        
        # 1. Is het binnen de ronde spiegel?
        mirror_radius = self.grid.u_range / 2
        if (u**2 + v**2) > mirror_radius**2:
            return False
            
        # 2. Is het in het gat? (Dan is het GEEN hit voor de spiegel)
        if self.hole and self.hole.is_hit(u, v):
            return False
            
        return True
        
    def reflect(self, incident_dir: Vector):
        """Berekent de nieuwe richting van de straak"""
        d = incident_dir.normalize()
        n = self.normal
        
        # reflectie formule: r = d - 2(d · n)n
        dot = d.dot(n)
        return (d - n*(2.0*dot)).normalize()
    
    def process_hit(self, ray_position: Vector):
        """
        Checkt of een wereldpositie op de spiegel in het gat valt.
        Retourneert True als het gat geraakt wordt (straal gaat erdoor).
        """
        if not self.hole:
            return False
            
        # Zet wereldpositie om naar lokale u, v coördinaten
        # (Ik neem aan dat je een world_to_local methode hebt die u, v teruggeeft)
        u, v = self.get_local_coordinates(ray_position)
        
        return self.hole.is_hit(u, v)
     
    def __repr__(self):
        # Naam van de 
        return f"Mirror('{self.name}', origin={self.origin}, normal={self.normal})"


if __name__ == "__main__":
      # Maak een klein gat van 0.1 radius in het midden
    my_hole = Hole("EntryHole", origin=Vector(0,0,0), radius=0.1, grid=None)
    
    # Maak de spiegel en geef het gat mee
    mirror1 = Mirror("Spiegel1", 
                     origin=Vector(0,0,0), 
                     normal=Vector(0,0,1), 
                     grid=TwoGrid(2,2,0.5), 
                     hole=my_hole)

    # Test punt in het midden (zou False moeten zijn want het is in het gat)
    center_point = Vector(0, 0, 0)
    print(f"Is midden {center_point} een hit? {mirror1.is_hit(center_point)}") # Verwacht: False
    
    # Test punt net buiten het gat
    edge_point = Vector(0.5, 0, 0)
    print(f"Is rand {edge_point} een hit? {mirror1.is_hit(edge_point)}") # Verwacht: True