from vector import Vector
from matrix import Matrix
from grid import TwoGrid
import math

def test_simulation():
    print("--- 1. Vector & Matrix Basics ---")
    v1 = Vector(1, 0, 0)
    # Rotatie van 90 graden om de Z-as: (1,0,0) moet (0,1,0) worden
    rot_z = Matrix.rotation_z(math.pi / 2) # definieer de rotatie matrix
    v_rot = rot_z.__matmul__(v1) # multipliceer de vector en matrix
    print(f"Rotatie 90deg om Z: {v1} -> {v_rot}") 
    # Check of de lengte behouden blijft (behoud van energie/fysica)
    print(f"Norm behouden? {math.isclose(v_rot.norm(), v1.norm())}") # vergelijk norm voor en na rotatie

    print("\n--- 2. Orthonormale Basis (De Spiegel-test) ---")
    # Stel we hebben een spiegel die onder 45 graden staat
    # De normaalVector wijst dan 'schuin' omhoog/opzij
    n = Vector(1, 1, 0).normalize() #normalize this vector: sides are 1/sqrt(2) then
    local_basis = Matrix.from_normal(n)
    print(f"Basis Matrix voor normaal {n}:\n{local_basis}")
    
    # Test of de rijen loodrecht op elkaar staan (dot product = 0)
    # Matrix.from_normal geeft een wereld->lokaal transformatie, dus de rijen
    # zijn de lokale basisvectoren in wereldcoördinaten.
    u = Vector(local_basis.m[0][0], local_basis.m[0][1], local_basis.m[0][2])
    v = Vector(local_basis.m[1][0], local_basis.m[1][1], local_basis.m[1][2])
    print(f"U loodrecht op V? (dot product): {u.dot(v)}")
    print(f"U loodrecht op N? (dot product): {u.dot(n)}")

    print("\n--- 3. Grid & World Transformations ---")
    # Maak een spiegel-oorsprong op (10, 0, 0) in de wereld
    origin = Vector(10, 0, 0)
    # Gebruik de schuine basis van hierboven
    my_grid = TwoGrid(u_range=2, v_range=2, spacing=1, origin=origin, local_to_world=local_basis)
    
    local_pts = my_grid.generate_points_local()
    world_pts = my_grid.generate_points_world()
    
    print(f"Lokaal punt (0,0,0) wordt in wereld: {world_pts[4]}") # Middelste punt (indien 3x3 grid)
    print(f"Verwacht: Vector(10.0, 0.0, 0.0)")

    print("\n--- 4. Matrix Ketens (Double rotation) ---")
    # Test __matmul__: Twee keer 45 graden moet 90 graden zijn
    rot_45 = Matrix.rotation_z(math.pi / 4)
    rot_90_check = rot_45 @ rot_45
    v_test = rot_90_check.__matmul__(Vector(1,0,0))
    print(f"Dubbele 45deg rotatie op (1,0,0): {v_test}")

if __name__ == "__main__":
    test_simulation()