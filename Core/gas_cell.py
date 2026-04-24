#gas_cell.py
# this class is responsible for the main simulation loop. It will take a lightray as input, and it will return a lightray as output.
# it will have a certain geometry, with a certain amount of mirrors and holes. The gas absorption will also be an input of the gas cell.
# There will be looped over all events (propagation and reflection) until the ray is extinguished or it exits the cell through a hole.

import sys
import os

# Pad-instellingen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Math.vector import Vector
from Math.grid import TwoGrid
from Geometry.mirror import Mirror
from Geometry.hole import Hole
from Geometry.cell_geometry import CellGeometry
from Physics.lightray import Lightray
from Results.raystate import Raystate
from Physics.propagation import Propagation
from Physics.reflection_event import ReflectionEvent
from Results.hitmap import Hitmap
from Results.track_memory import TrackMemory

class GasCell:
    def __init__(self, cell_geometry: CellGeometry, alpha: float=0.0):
        self.propagation = Propagation(cell_geometry, alpha)
        self.track_memory = TrackMemory()
        self.hitmaps = {} # Wordt gevuld bij initialisatie
    
    # this function runs the simulation untill the lightray is extinguished/exits the cell.
    # It returns a track memory object, containing all the states of the lightray during the simulation.
    def run_simulation(self, initial_ray: Lightray, max_reflections: int=100):
        ray = initial_ray
        reflection_count = 0
        
        while not ray.is_extinguished:
            # 1. Vliegen
            result = self.propagation.forward(ray)
            if isinstance(result, tuple):
                target_mirror, event_type = result
            else:
                target_mirror = result
                event_type = "reflection"

            if target_mirror is None:
                break

            if event_type == "reflection":
                if reflection_count >= max_reflections:
                    break

                event = ReflectionEvent(ray, target_mirror, self.hitmaps.get(target_mirror.name))
                state = event.process()
                self.track_memory.add_state(state)
                reflection_count += 1
                continue

            if event_type == "hole":
                from Physics.reflection_event import HoleExitEvent
                event = HoleExitEvent(ray, target_mirror, self.hitmaps.get(target_mirror.name))
                state = event.process()
                self.track_memory.add_state(state)
                break
                 
        return self.track_memory
    
# test

