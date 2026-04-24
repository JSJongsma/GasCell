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

def test_herriott_geometry():
    # --- 1. SETUP GEOMETRIE ---
    # We definiëren de box: X=0-40, Y=0-25, Z=0-50
    cell = CellGeometry("Herriott", Vector(0,0,0), Vector(40,25,50), (40, 25, 50))
    
    mid_x = 20.0
    mid_y = 12.5

    # SPIEGEL LINKS (Entry): Op Z=0, X=midden
    hole_links = Hole("Ingang", origin=Vector(mid_x, mid_y, 0), radius=1.0, grid=None)
    # Normaal wijst de cel in (+Z)
    m_links = Mirror("Linker_Spiegel", Vector(mid_x, mid_y, 0), Vector(0,0,1), 
                     TwoGrid(10,10,0.1), hole=hole_links)
    
    # SPIEGEL 1 (Bovenste in diagram): Positie (35, +15)
    # X = 20 + 15 = 35 | Z = 35
    # Normaal wijst schuin terug (of gewoon -Z als versimpeling)
    m_back = Mirror("Spiegel_Boven", Vector(35, mid_y, 35), Vector(0,0,-1), 
                    TwoGrid(10,10,0.1))
    
    # SPIEGEL 2 (Onderste in diagram): Positie (40, -15)
    # X = 20 - 15 = 5 | Z = 40
    m_front_mirror = Mirror("Spiegel_Onder", Vector(5, mid_y, 40), Vector(0,0,-1), 
                            TwoGrid(10,10,0.1))
    
    # Nu vallen ze gegarandeerd binnen de CellGeometry(40, 25, 50)
    cell.add_mirror(m_links)
    cell.add_mirror(m_back)
    cell.add_mirror(m_front_mirror)

    manager = GasCell(cell, alpha=0.0)
    
    # Straal vertrekt vanuit het gat van de Linker_Spiegel richting Spiegel_Boven
    start = Vector(mid_x, mid_y, 0)
    target = Vector(35, mid_y, 35)
    direction = (target - start).normalize()
    
    ray = Lightray(origin=start, direction=direction, intensity=1.0)
    
    print("--- Start Herriott Test ---")
    memory = manager.run_simulation(ray, max_reflections=5)
    memory.print_memory()
    
if __name__ == "__main__":
    test_herriott_geometry()