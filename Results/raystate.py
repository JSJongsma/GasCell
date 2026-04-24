#raystate.py
# this class will be responsible for the intermediate states of the ray during the simulation.
# Instead of 5 seperate variables (pos, dir, intensity, wavevector, mirror ref), we put it in a single object, raystate.
# it is a dataclass, purely meant to store a 'snapshot' of the ray at a certain moment in the simulation.
# the datatype will be returned by the reflection event.

# another class, TrackMemory will function as a memory bank for all the raystates during the simulation.

import sys
import os

# Voeg de hoofdmap van het project toe aan het pad (één niveau boven Math)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Math.vector import Vector
from dataclasses import dataclass

@dataclass
class Raystate:
    # Verplichte velden (moet je invullen bij aanmaak)
    position: Vector
    direction: Vector
    intensity: float
    path_length: float
    
    # Optionele velden (hebben een standaardwaarde)
    mirror_name: str = None
    u: float = None
    v: float = None
    event_type: str = "reflection"
    
    def __repr__(self):
        return (f"Raystate(pos={self.position}, dir={self.direction}, "
                f"I={self.intensity:.4f}, L={self.path_length:.2f}, "
                f"mirror='{self.mirror_name}', u={self.u}, v={self.v})")

    