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
from Core.gas_cell import GasCell

def test_full_automation():
    # SETUP: Een cel met 3 spiegels
    cell = CellGeometry("AutoTest", Vector(0,0,0), Vector(10,0,0), (10,10,10))
    
    # Spiegel op Z=0 (geen gat)
    m0 = Mirror("Front", Vector(0,0,0), Vector(0,0,1), TwoGrid(10,10,0.1), reflection_coef=0.99)
    # Spiegel op Z=10 (geen gat)
    m2 = Mirror("Back", Vector(0,0,10), Vector(0,0,-1), TwoGrid(10,10,0.1), reflection_coef=0.99)
    
    # We voegen ze toe
    cell.add_mirror(m0)
    cell.add_mirror(m2)

    # INITIALISEER MANAGER
    # We zetten alpha op 0.05 voor een beetje gas-absorptie
    manager = GasCell(cell, alpha=0.01)
    
    # SCHIET DE STRAAL
    # Start op Z=2, kijkend naar de achterwand (Z=10)
    ray = Lightray(origin=Vector(0,0,2), direction=Vector(0,0,1), intensity=1.0)
    
    print("--- Start Automatische Simulatie ---")
    # We laten hem maximaal 5 keer stuiteren
    memory = manager.run_simulation(ray, max_reflections=50)
    
    # RESULTATEN
    print("\n--- Resultaten uit TrackMemory ---")
    memory.print_memory()
    
    # Check intensiteit verloop
    last_state = memory.memory[-1]
    print(f"\nEindintensiteit na {len(memory.memory)} klappen: {last_state.intensity:.4f}")

if __name__ == "__main__":
    test_full_automation()