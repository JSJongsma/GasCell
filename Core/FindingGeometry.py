import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import traceback
import sys
import os

# Pad-instellingen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Math.vector import Vector
from Math.matrix import Matrix
from Math.grid import TwoGrid
from Geometry.mirror import Mirror
from Geometry.hole import Hole
from Geometry.cell_geometry import CellGeometry
from Physics.lightray import Lightray
from Physics.Physics import PhysicsUtils
from Core.gas_cell import GasCell
from Results.hitmap import Hitmap
from Core.SearchSpace import SearchSpace
from Core.FitnessEvaluator import FitnessEvaluator

class FindingGeometry:
    def __init__(self, target_reflections=28, iterations=500000, first_reflection_u=None, first_reflection_v=None, hole_diameter=0.4, entry_hole_diameter=0.4):
        self.search_space = SearchSpace()
        self.target_reflections = target_reflections
        self.iterations = iterations

        self.hole_diameter = hole_diameter
        self.hole_radius = hole_diameter / 2.0
        self.hole_u, self.hole_v = 1.2, 0.0

        self.entry_hole_diameter = entry_hole_diameter
        self.entry_hole_radius = entry_hole_diameter / 2.0
        self.entry_hole_u, self.entry_hole_v = -1.2, 0.0

        self.hole_local_pos = Vector(self.hole_u, self.hole_v, 0.0)
        self.entry_hole_local_pos = Vector(self.entry_hole_u, self.entry_hole_v, 0.0)
        self.first_reflection_u = first_reflection_u
        self.first_reflection_v = first_reflection_v

        self.evaluator = FitnessEvaluator(
            target_reflections,
            hole_diameter=self.hole_diameter,
            entry_hole_diameter=self.entry_hole_diameter,
            initial_beam_diameter_cm=self.entry_hole_diameter
        )

        # tracking
        self.best_score = -float("inf")
        self.best_config = None 
        self.best_track_memory = None

        self.current_score = -float("inf")
        self.current_config = None

        self.temperature = 1000
        self.cooling_rate = 0.9999

        self.no_improve_counter = 0  # counter voor stagnatie
        self.dist_no_improve_counter = 0  # extra counter voor afstand stagnatie
        self.last_dist = float("inf")  # laatste afstand tot het gat

        self.edge_lock_counter = 0
        self.pos_m1 = Vector(0, 20, 25.0)
    
    def _check_entry_hole_hit(self, track_memory):
        """
        Controleert of een reflectie op de entry hole op M1 is gevallen.
        Geeft True terug als er een ongeldig gat-contact is gevonden.
        """
        for state in track_memory.memory:
            if state.mirror_name.lower() == "m1":
                # Bereken afstand tot entry hole centrum (-1.2, 0.0)
                du = state.u - self.entry_hole_u
                dv = state.v - self.entry_hole_v
                dist = math.sqrt(du**2 + dv**2)

                if dist < self.entry_hole_radius:
                    return True  # Hit op entry hole gevonden!
        return False
        

    def _setup_cell(self, config):
        try:
            # 1. Posities bepalen
            pos_m1 = Vector(0, 20, 25.0)
            norm_m1 = Vector(1, 0, 0).normalize()
            pos_m2 = Vector(config["m2_x"], config["m2_y"], 25.0)
            pos_m3 = Vector(config["m3_x"], config["m3_y"], 25.0)
                       
            # Afstandscheck
            min_dist = 20.0
            if (pos_m2 - pos_m3).norm() < min_dist or \
               (pos_m1 - pos_m2).norm() < min_dist or \
               (pos_m1 - pos_m3).norm() < min_dist:
                return None, None, None # Geef 3 Nones terug (cell, pos_m2, ray_dir)

            # 2. Richtingen berekenen (Normalen)
            n2_base = PhysicsUtils.calculate_ideal_normal(pos_m1, pos_m2, pos_m3)
            rot_m2 = Matrix.rotation_z(math.radians(config["m2_phi"]))
            n2_final = (rot_m2 @ n2_base).normalize()
            n2_final.z = 0
            
            n3_base = PhysicsUtils.calculate_ideal_normal(pos_m2, pos_m3, pos_m1)
            rot_m3 = Matrix.rotation_z(math.radians(config["m3_theta"]))
            n3_final = (rot_m3 @ n3_base).normalize()
            n3_final.z = 0
                        
            #for name, n_vec in [("M2_base", n2_base), ("M3_base", n3_base)]:
            #    if abs(n_vec.z) > 1e-12:
            # Gebruik het lokale M2-coördinaat om de eerste reflectie te forceren.
            # Dit zorgt ervoor dat de startstraal naar het gewenste (u,v) punt op M2 gaat.
            mirror_target_u = config.get("target_u", self.first_reflection_u)
            mirror_target_v = config.get("target_v", self.first_reflection_v)

            if mirror_target_u is not None and mirror_target_v is not None:
                m2_tmp = Mirror("M2_temp", pos_m2, n2_final, TwoGrid(5.08, 5.08, 0.1), hole=None)
                u_dir, v_dir, _ = m2_tmp.get_local_axes()
                target_point = pos_m2 + (u_dir * mirror_target_u) + (v_dir * mirror_target_v)
            else:
                # Geen specifieke doelpunten opgegeven: fixeer de beam op het midden van M2 (u=0, v=0).
                target_point = pos_m2

            base_dir = (target_point - pos_m1).normalize()

            # Voeg de pitch/yaw variatie uit de config toe
            ray_dir = (
                Matrix.rotation_y(math.radians(config["ray_yaw"])) @ 
                Matrix.rotation_z(math.radians(config["ray_pitch"]))
            ) @ base_dir
            #if abs(ray_dir.z) > 1e-3:
            #    print(f"LEK GEVONDEN: ray_dir heeft Z-component: {ray_dir.z}")
            #    print(f"Config: {config}")
                
            # 4. Cell bouwen
            exit_hole = Hole("Exit", origin=self.hole_local_pos, radius=self.hole_radius, grid=None)
            entry_hole = Hole("Entry", origin=self.entry_hole_local_pos, radius=self.entry_hole_radius, grid=None)
            cell_geo = CellGeometry("Cell", cell_dimensions=(50, 40, 50))
            
            m1 = Mirror("M1", pos_m1, norm_m1, TwoGrid(5.08, 5.08, 0.1), reflection_coef=0.98, hole=entry_hole)
            m2 = Mirror("M2", pos_m2, n2_final, TwoGrid(5.08, 5.08, 0.1), reflection_coef=0.98, hole=exit_hole)
            m3 = Mirror("M3", pos_m3, n3_final, TwoGrid(5.08, 5.08, 0.1), reflection_coef=0.98)
            
            # Harde check op invoer-hoogte
            #if not (pos_m1.z == pos_m2.z == pos_m3.z == 25.0):
            #    print(f"Fout in basis-hoogte: M1={pos_m1.z}, M2={pos_m2.z}, M3={pos_m3.z}")

            for m in [m1, m2, m3]:
                cell_geo.add_mirror(m)
                
            # We geven alleen terug wat we echt nodig hebben voor de simulatie/score
            return GasCell(cell_geo), pos_m2, ray_dir

        except Exception as e:
            print("Fout in _setup_cell:", e)
            traceback.print_exc()
            return None, None, None

    def _compute_eval_state(self, track_mem):
        # Geef eerst een echte hole-exit voorkeur als die er is.
        hole_exit_state = next(
            (state for state in track_mem.memory if getattr(state, 'event_type', None) == 'hole_exit'),
            None
        )
        if hole_exit_state is not None:
            return hole_exit_state

        # Gebruik anders alleen de echte laatste staat van de simulatie.
        return track_mem.memory[-1]
    
    def _calculate_path_length(self, start_pos, states):
        if not states:
            return 0.0
        
        total_length = 0.0
        current_pos = start_pos
        
        for state in states:
            # Bereken afstand tussen vorig punt en huidig raakpunt
            segment_length = (state.position - current_pos).norm()
            total_length += segment_length
            current_pos = state.position # Update voor het volgende segment
            
        return total_length
    
      
    def run_optimization(self):
        self.acceptance = np.zeros(self.iterations)  # Voor het bijhouden van acceptatie ratio
        
        print(f"Start Optimalisatie | Target: {self.target_reflections} bounces op M2(u=1.2, v=0)")

        for i in range(self.iterations):
            config = self.search_space.get_random_config() if self.current_config is None else self.search_space.perturb(self.current_config)

            # Veel schonere aanroep:
            cell, pos_m2, ray_dir = self._setup_cell(config)
            
            if cell is None:
                #print(f"iter {i}: cell None")
                continue

            # Simulatie starten met de kant-en-klare ray_dir
            pos_m1 = Vector(0, 20, 25.0)
            track_mem = cell.run_simulation(
                Lightray(pos_m1 + (ray_dir * 0.01), ray_dir),
                max_reflections=self.target_reflections + 5
            )
            if not track_mem.memory:
                print(f"iter {i}: empty track memory")
                continue

            # Check: geen reflectie mag op de entry hole vallen!
            if self._check_entry_hole_hit(track_mem):
                # print(f"iter {i}: reflectie op entry hole gevonden - skip")
                continue

            for idx, state in enumerate(track_mem.memory):
                z_afwijking = abs(state.position.z - 25.0)
                if z_afwijking > 1e-3:
                   print(f"🚨 DRIFT GEVONDEN: Bounce {idx} op {state.mirror_name} wijkt af! Z={state.position.z}")
                    
            score = self.evaluator.calculate_score(track_mem)
            path_length = self._calculate_path_length(pos_m1, track_mem.memory)
            energy_diff = score - self.current_score
            
            metropolis_accept = math.exp(min(0, energy_diff / self.temperature))

            if (self.current_config is None) or (np.random.rand() < metropolis_accept):
                self.current_score = score
                self.current_config = config
                self.acceptance[i] = 1
                eval_state = self._compute_eval_state(track_mem)
                dist = math.sqrt((eval_state.u - self.hole_u) ** 2 + (eval_state.v - self.hole_v) ** 2)
                bounces = len(track_mem.memory)

                print(f"Iter {i:6d} | Bounces: {bounces:2d} | Dist: {dist:.4f} | Path: {path_length:.1f}cm | Score: {score:12.0f}| acceptence: {self.acceptance[:i+1].mean():.3f}")
                if abs(dist - self.hole_radius) < 0.005:  # Als de afstand dichtbij de radius komt
                    self.edge_lock_counter += 1
                else:
                    self.edge_lock_counter = 0

                improved_score = score > self.best_score + 1e-6
                improved_dist = dist < self.last_dist - 1e-5

                if improved_score or improved_dist:
                    self.best_score = max(self.best_score, score)
                    self.best_config = config
                    self.best_track_memory = track_mem
                    self.no_improve_counter = 0
                    self.dist_no_improve_counter = 0
                    self.last_dist = dist

                    # update search_space voor microscoping
                    self.search_space.m2_base = {"x": config["m2_x"], "y": config["m2_y"]}
                    self.search_space.m3_base = {"x": config["m3_x"], "y": config["m3_y"]}
                    self.search_space.best_m2_phi = config["m2_phi"]
                    self.search_space.best_m3_theta = config["m3_theta"]
                    self.search_space.best_pitch = config["ray_pitch"]
                    self.search_space.best_yaw = 0 # config["ray_yaw"]

                    # Microscope logic
                    if bounces < self.target_reflections:
                        self.search_space.pos_range = 1.0
                        self.search_space.mirror_angle_range = 0.5
                        self.search_space.ray_angle_range = 0.2
                    elif dist >= 1.0:
                        self.search_space.pos_range = 0.3
                        self.search_space.mirror_angle_range = 0.3
                        self.search_space.ray_angle_range = 0.14
                    elif dist >= 0.3:
                        self.search_space.pos_range = 0.01
                        self.search_space.mirror_angle_range = 0.01
                        self.search_space.ray_angle_range = 0.005
                    else:
                        self.search_space.pos_range = 0.01
                        self.search_space.mirror_angle_range = 0.01
                        self.search_space.ray_angle_range = 0.005
                else:
                    # verhoog counters als geen verbetering
                    self.no_improve_counter += 1
                    self.dist_no_improve_counter += 1

                # Early stop bij perfecte oplossing
                if dist < 0.01 and bounces >= self.target_reflections:
                    print("\n🎯 OPTIMALISATIE VOLTOOID: Exacte middelpunt gevonden.")
                    break

                # edge lock reset
                # wanneer we te lang op de rand van het gat blijven hangen, resetten we om uit die situatie te komen
                if self.edge_lock_counter > 10:
                    print("RESET: stuck on hole boundary")
                    self.current_config = None
                    self.temperature = 3.0
                    self.no_improve_counter = 0
                    self.dist_no_improve_counter = 0
                    self.edge_lock_counter = 0
                    self.last_dist = float("inf")
                    print("New initial conditions applied!")
                    print(f"New initial config: {self.current_config}")
                    print(f"New temperature: {self.temperature}")

        return self.best_config, self.best_track_memory
    
    def plot_geometry(self, config, track_memory, cell_dims=(50, 40, 50)):
            fig = plt.figure(figsize=(14, 10))
            ax = fig.add_subplot(111, projection='3d')

            # 1. Cel grenzen
            l, w, h = cell_dims
            for z in [0, h]:
                ax.plot([0, l, l, 0, 0], [0, 0, w, w, 0], [z, z, z, z, z], color='black', alpha=0.2)
            for x, y in [(0,0), (l,0), (l,w), (0,w)]:
                ax.plot([x, x], [y, y], [0, h], color='black', alpha=0.1)

            # 2. Bereken de werkelijke normalen zoals de simulatie dat doet
            pos_m1 = Vector(0, 20, 25.0)
            pos_m2 = Vector(config["m2_x"], config["m2_y"], 25.0)
            pos_m3 = Vector(config["m3_x"], config["m3_y"], 25.0)

            n2_base = PhysicsUtils.calculate_ideal_normal(pos_m1, pos_m2, pos_m3)
            n3_base = PhysicsUtils.calculate_ideal_normal(pos_m2, pos_m3, pos_m1)

            rot_m2 = Matrix.rotation_z(math.radians(config["m2_phi"]))
            rot_m3 = Matrix.rotation_z(math.radians(config["m3_theta"]))

            n1_final = Vector(1, 0, 0) # M1 kijkt altijd naar rechts
            n2_final = (rot_m2 @ n2_base).normalize()
            n3_final = (rot_m3 @ n3_base).normalize()

            # 3. Verbeterde Helper functie voor de spiegel-schijf
            def draw_actual_mirror(pos, normal_vec, color, label, radius=2.5):
                # Maak een cirkel in het YZ-vlak (normaal = X)
                t = np.linspace(0, 2*np.pi, 50)
                y_pts = radius * np.cos(t)
                z_pts = radius * np.sin(t)
                x_pts = np.zeros_like(t)

                # Bereken de rotatie om de X-as cirkel uit te lijnen met de werkelijke normaal vector
                # We gebruiken een eenvoudige quiver voor de pijl die de 'normaal' uit de simulatie volgt
                ax.quiver(pos.x, pos.y, pos.z, 
                        normal_vec.x, normal_vec.y, normal_vec.z, 
                        length=5, color=color, pivot='tail', linewidth=2)
                
                # Voor de schijf zelf plotten we nu een scatter/vlak dat loodrecht staat op de normaal
                ax.scatter(pos.x, pos.y, pos.z, color=color, s=200, label=label, edgecolors='black')
            
            path_length = self._calculate_path_length(self.pos_m1, track_memory)

            # Teken de spiegels met hun ECHTE normalen
            draw_actual_mirror(pos_m1, n1_final, 'red', 'M1 (In)')
            draw_actual_mirror(pos_m2, n2_final, 'green', 'M2 (Exit)')
            draw_actual_mirror(pos_m3, n3_final, 'blue', 'M3')

            # 4. Het pad en het gat (ongewijzigd)
            if track_memory and track_memory.memory:
                points = [(pos_m1.x, pos_m1.y, pos_m1.z)]
                for state in track_memory.memory:
                    points.append((state.position.x, state.position.y, state.position.z))
                path = np.array(points)
                ax.plot(path[:, 0], path[:, 1], path[:, 2], color='orange', alpha=0.7, label='Ray Path')

            hole_x = config["m2_x"] + self.hole_u
            hole_y = config["m2_y"] + self.hole_v
            ax.scatter(hole_x, hole_y, 25.0, color='purple', s=100, label='Target Hole')

            ax.set_box_aspect([l, w, h])
            ax.legend()
            ax.set_title('Path Length: ', path_length, ', Reflections: ', len(track_memory))
            plt.show()
            plt.savefig(f"geometry_{self.target_reflections}_bounces.png", dpi=300)
    
    # save best configuration and track memory for later analysis
    def save_results(self, filename_prefix="best_geometry"):
        if self.best_config is None or self.best_track_memory is None:
            print("No results to save.")
            return
        
        # Save configuration
        config_df = pd.DataFrame([self.best_config])
        config_df.to_csv(f"{filename_prefix}_{self.target_reflections}_config.csv", index=False)
        
        # Save track memory
        track_data = [{
            "mirror_name": state.mirror_name,
            "position_x": state.position.x,
            "position_y": state.position.y,
            "position_z": state.position.z,
            "u": state.u,
            "v": state.v
        } for state in self.best_track_memory.memory]
        
        track_df = pd.DataFrame(track_data)        
        print(f"Results saved: {filename_prefix}_{self.target_reflections}_config.csv and {filename_prefix}_{self.target_reflections}track_memory.csv")

        track_df.to_csv(f"{filename_prefix}_{self.target_reflections}_track_memory.csv", index=False)
