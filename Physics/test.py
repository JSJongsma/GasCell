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

def test_propagation():
    # --- 1. SETUP GEOMETRIE ---
    cell = CellGeometry("TestCell", Vector(0,0,0), Vector(10,0,0), (10,10,10))
    
    # Spiegel 0: De 'voorwand' op Z=0
    m0 = Mirror("Voorste_Spiegel", origin=Vector(0,0,0), normal=Vector(0,0,1), 
                grid=TwoGrid(10,10,0.1))
    
    # Spiegel 1: In het midden met gat op Z=5
    hole1 = Hole("Gat1", origin=Vector(0,0,5), radius=1.0, grid=None)
    m1 = Mirror("Spiegel_Met_Gat", origin=Vector(0,0,5), normal=Vector(0,0,-1), 
                grid=TwoGrid(10,10,0.1), hole=hole1)
    
    # Spiegel 2: De achterwand op Z=10
    m2 = Mirror("Achterste_Spiegel", origin=Vector(0,0,10), normal=Vector(0,0,-1), 
                grid=TwoGrid(10,10,0.1))
    
    cell.add_mirror(m0)
    cell.add_mirror(m1)
    cell.add_mirror(m2)

    # --- 2. SETUP RESULTAAT-OBJECTEN ---
    # We maken hitmaps voor de spiegels die we willen monitoren
    hitmaps = {
        "Achterste_Spiegel": Hitmap(m2, grid=TwoGrid(10,10,0.1)),
        "Voorste_Spiegel": Hitmap(m0, grid=TwoGrid(10,10,0.1))
    }
    
    # Een lijst om onze Raystates (TrackMemory) in op te slaan
    track_memory = TrackMemory()

    # --- 3. DE SIMULATIE ---
    prop = Propagation(cell, absorption_alpha=0.1)
    ray = Lightray(origin=Vector(0,0,0), direction=Vector(0,0,1), intensity=1.0)

    print("--- Start Simulatie: Heenreis ---")
    # STAP 1: Propagatie naar achteren
    target = prop.forward(ray)
    if target:
        # Registreer de reflectie en sla de staat op
        event = ReflectionEvent(ray, target, hitmap=hitmaps.get(target.name))
        state = event.process() # ReflectionEvent geeft nu een Raystate terug
        track_memory.add_state(state)
        
        print(f"Geraakt: {target.name} op {ray.origin}")
        print(f"Intensiteit na gas: {ray.intensity:.4f}")

    print("\n--- Terugreis ---")
    # STAP 2: Propagatie terug naar voren (door het gat van m1 naar m0)
    target2 = prop.forward(ray)
    if target2:
        event2 = ReflectionEvent(ray, target2, hitmap=hitmaps.get(target2.name)) # make a reflection event for the second hit
        state2 = event2.process() # process the reflection event and get the new ray state: Ray state is returned by reflection event.
        track_memory.add_state(state2) # save the new returned ray state to the track memory.
        
        print(f"Geraakt: {target2.name} op {ray.origin}")
        print(f"Totale weglengte: {ray.total_path_length}m")
    
    track_memory.print_memory()

if __name__ == "__main__":
    test_propagation()