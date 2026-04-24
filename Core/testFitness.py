import sys
import os

# Zorg dat Python de modules kan vinden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Math.vector import Vector
from Results.raystate import Raystate
from Results.track_memory import TrackMemory
from Core.FitnessEvaluator import FitnessEvaluator

def test_fitness_logic():
    # 1. SETUP: Definieer het doel (exit hole)
    # Stel: we willen dat de straal eindigt op Vector(40, 12.5, 5)
    exit_goal = Vector(40.0, 12.5, 5.0)
    target_bounces = 10
    evaluator = FitnessEvaluator(target_reflections=target_bounces, exit_hole_pos=exit_goal)
    
    print(f"--- Start Fitness Test (Target: {target_bounces} bounces) ---")

    # --- SCENARIO A: De 'Perfecte' kandidaat ---
    # Haalt precies 10 bounces en eindigt exact op het exit-gat.
    mem_perfect = TrackMemory()
    # Voeg 10 bounces toe (we simuleren de snapshots van ReflectionEvent)
    for i in range(target_bounces):
        mem_perfect.add_state(Raystate(
            position=Vector(i, 0, 0), 
            direction=Vector(1, 0, 0), 
            intensity=0.9**i, 
            path_length=float(i*10),
            mirror_name=f"Mirror_{i%2}"
        ))
    # De allerlaatste state is een 'hit' op het exit gat
    mem_perfect.add_state(Raystate(exit_goal, Vector(1,0,0), 0.5, 100.0, mirror_name="ExitMirror")) # definieer een laatste hit die exact positie van gat heeft
    
    score_perfect = evaluator.calculate_score(mem_perfect)

    # --- SCENARIO B: De 'Net Niet' kandidaat ---
    # Haalt ook 10 bounces, maar eindigt 5 cm naast het gat.
    mem_near = TrackMemory()
    for i in range(target_bounces):
        mem_near.add_state(Raystate(Vector(i,0,0), Vector(1,0,0), 0.9**i, float(i*10), mirror_name="M"))
    
    off_target = exit_goal + Vector(0, 5, 0) # 5 cm afwijking op de Y-as
    mem_near.add_state(Raystate(off_target, Vector(1,0,0), 0.5, 100.0, mirror_name="ExitMirror"))
    
    score_near = evaluator.calculate_score(mem_near)

    # --- SCENARIO C: De 'Mislukte' kandidaat ---
    # Haalt maar 2 bounces en vliegt dan uit de cel.
    mem_fail = TrackMemory()
    for i in range(2):
        mem_fail.add_state(Raystate(Vector(i,0,0), Vector(1,0,0), 0.9**i, float(i*10), mirror_name="M"))
    
    score_fail = evaluator.calculate_score(mem_fail)

    # --- RESULTATEN PRINTEN ---
    print(f"Score Perfect (0cm offset): {score_perfect:>10.2f}")
    print(f"Score Near    (5cm offset): {score_near:>10.2f}")
    print(f"Score Fail    (Te weinig hits): {score_fail:>10.2f}")

    # --- ASSERTIONS (De logische check) ---
    assert score_perfect > score_near, "Fout: Perfecte hit moet hoger scoren dan 5cm offset!"
    assert score_near > score_fail, "Fout: 10 hits moet hoger scoren dan 2 hits!"
    
    print("\n✅ TEST GESLAAGD: De evaluator rangschikt de resultaten correct volgens jouw Raystate data.")

if __name__ == "__main__":
    test_fitness_logic()