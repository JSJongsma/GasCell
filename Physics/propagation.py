#propagation.py
# this class will calculate the propagation of the lightrays between reflections.
# this includes distances beteen mirrors in a certain geometry, the intensity of the rays after traveling a distance.
# The Reflection events will be calculated in a seperate class. 

# The class calculates the target mirror, which a ray will hit after it entered the cell, or after a reflection event.
# And it calculates the new position and intensity of the ray after traveling to the target mirror.

import sys
import os

# Voeg de hoofdmap van het project toe aan het pad (één niveau boven Math)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Math.vector import Vector
from Physics.Physics import PhysicsUtils
from Geometry.cell_geometry import CellGeometry
from Geometry.mirror import Mirror
from Physics.lightray import Lightray

class Propagation:
    def __init__(self, cell_geometry: CellGeometry, absorption_alpha: float=0.0):
        self.cell_geometry = cell_geometry
        self.alpha = absorption_alpha
    
    def forward(self, ray):
        """
        Berekent de vrije ruimte stap voor een Lightray object.
        Update de ray positie en intensiteit (gas absorptie).
        """
        # 1. Vind de dichtstbijzijnde spiegel (en de afstand t)
        target_mirror, distance, hole_mirror, hole_distance = self.find_next_intersection(ray)

        # Als er geen object geraakt wordt, 'dooft' de straal in de simulatie
        if target_mirror is None and hole_mirror is None:
            ray.is_extinguished = True
            return None, None

        # Kies de afstand die we daadwerkelijk afleggen.
        travel_distance = distance if target_mirror is not None else hole_distance

        # 2. Bereken nieuwe intensiteit na reizen door gas (Beer-Lambert)
        new_intensity = PhysicsUtils.calculate_beer_lambert(
            ray.intensity, travel_distance, self.alpha
        )

        # 3. Update de Lightray status (vóór de reflectie! / hole exit)
        ray.origin = ray.origin + (ray.direction * travel_distance)
        ray.total_path_length += travel_distance
        ray.intensity = new_intensity

        if target_mirror is not None:
            return target_mirror, "reflection"

        ray.is_extinguished = True
        return hole_mirror, "hole"
    
    def find_next_intersection(self, ray):
        # We zoeken de kleinste positieve afstand
        closest_distance = float('inf') 
        closest_mirror = None
        closest_hole_distance = float('inf')
        closest_hole_mirror = None

        for mirror in self.cell_geometry.get_mirrors():
            d = PhysicsUtils.get_intersection_distance(
                ray.origin, ray.direction, mirror.origin, mirror.normal
            )

            if d <= 0:
                continue

            hit_point = ray.origin + (ray.direction * d)
            hit_check = mirror.is_hit(hit_point)

            if hit_check and d < closest_distance:
                closest_distance = d
                closest_mirror = mirror
                continue

            if mirror.hole:
                u, v = mirror.get_local_coordinates(hit_point)
                if mirror.hole.is_hit(u, v) and d < closest_hole_distance:
                    closest_hole_distance = d
                    closest_hole_mirror = mirror

        return closest_mirror, closest_distance, closest_hole_mirror, closest_hole_distance
        
    
        
        