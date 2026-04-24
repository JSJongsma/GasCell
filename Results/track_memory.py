#track_memory.py
# track memory will be a 'list' of all raystates in the simulation. Each time a ray is reflected, the reflection event
# returns a raystate object, which will be saved inside a track memory object.

from dataclasses import dataclass
import sys
import os

# Voeg de hoofdmap van het project toe aan het pad (één niveau boven Math)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Results.raystate import Raystate

class TrackMemory:
    def __init__(self):
        self.memory = [] # Een lijst van Raystate objecten

    def add_state(self, raystate: Raystate):
        self.memory.append(raystate)

    def __repr__(self):
        return f"TrackMemory({len(self.memory)} states)"

    def __len__(self):
        return len(self.memory)

    def __iter__(self):
        return iter(self.memory)
    
    def print_memory(self):
        for i, state in enumerate(self.memory):
            print(f"State {i}: {state}")
            
    def get_reflection_count(self):
        """
        Geeft het aantal reflecties terug. 
        Als we ervan uitgaan dat Raystate een attribuut 'event_type' heeft:
        """
        # Pas dit aan naar hoe jouw Raystate bijhoudt of het een spiegel raakte.
        # Bijvoorbeeld:
        return sum(1 for state in self.memory if getattr(state, 'event_type', 'reflection') == 'reflection')
        
        # Of, als elke state (behalve de eerste start-state) een reflectie is:
        # return max(0, len(self.memory) - 1)

    def get_last_point(self):
        """Geeft de positie (Vector) van de allerlaatste state."""
        if not self.memory:
            return None
        return self.memory[-1].position # Ervan uitgaande dat Raystate een .position heeft

    def get_all_mirror_hits(self):
        """Geeft een lijst van posities (Vectors) waar een reflectie plaatsvond."""
        hits = []
        for state in self.memory:
            # Check of het een reflectie is (pas aan naar jouw Raystate logica)
            if getattr(state, 'event_type', 'reflection') == 'reflection':
                hits.append(state.position)
        return hits

    def get_total_path_length(self):
        """Geeft de totale afgelegde weg (handig voor TrajectoryResults)."""
        if not self.memory:
            return 0.0
        return self.memory[-1].path_length