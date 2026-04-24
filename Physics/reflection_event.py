#reflection_event.py
# this class will be responsible for calculating the reflection of a lighray with a certain angle to the 
# normal of the mirror. It will calculate the new direction of the ray after the event.

import sys
import os

# Voeg de hoofdmap van het project toe aan het pad (één niveau boven Math)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Math.vector import Vector
from Physics.Physics import PhysicsUtils
from Geometry.cell_geometry import CellGeometry
from Geometry.mirror import Mirror
from Physics.lightray import Lightray
from Results.hitmap import Hitmap
from Results.raystate import Raystate

class ReflectionEvent:
    def __init__(self, ray: Lightray, mirror: Mirror, hitmap: Hitmap = None):
        self.ray = ray
        self.mirror = mirror
        self.hitmap = hitmap

    def process(self) -> Raystate:
        """
        Voert de reflectie uit en geeft een snapshot (Raystate) terug.
        """
        # 1. BEREKEN ALTIJD de lokale coördinaten (u, v)
        # Dit moet buiten de 'if hitmap' staan, anders kent Raystate 'u' niet!
        u, v = self.mirror.get_local_coordinates(self.ray.origin)
        
        # 2. Registreer op de hitmap (als die er is)
        if self.hitmap:
            self.hitmap.register_hit(u, v, self.ray.intensity)

        # 3. SPIEGEL VERLIES
        self.ray.intensity *= self.mirror.reflection_coefficient

        # 4. REFLECTIE
        new_direction = PhysicsUtils.reflect_vector(self.ray.direction, self.mirror.normal)
        self.ray.direction = new_direction

        # 5. SNAPSHOT (u en v zijn nu gegarandeerd bekend)
        return Raystate(
            position=Vector(self.ray.origin.x, self.ray.origin.y, self.ray.origin.z),
            direction=Vector(self.ray.direction.x, self.ray.direction.y, self.ray.direction.z),
            intensity=self.ray.intensity,
            path_length=self.ray.total_path_length,
            mirror_name=self.mirror.name,
            u=u,
            v=v,
            event_type="reflection"
        )


class HoleExitEvent:
    def __init__(self, ray: Lightray, mirror: Mirror, hitmap: Hitmap = None):
        self.ray = ray
        self.mirror = mirror
        self.hitmap = hitmap

    def process(self) -> Raystate:
        u, v = self.mirror.get_local_coordinates(self.ray.origin)

        if self.hitmap:
            self.hitmap.register_hit(u, v, self.ray.intensity)

        return Raystate(
            position=Vector(self.ray.origin.x, self.ray.origin.y, self.ray.origin.z),
            direction=Vector(self.ray.direction.x, self.ray.direction.y, self.ray.direction.z),
            intensity=self.ray.intensity,
            path_length=self.ray.total_path_length,
            mirror_name=self.mirror.name,
            u=u,
            v=v,
            event_type="hole_exit"
        )