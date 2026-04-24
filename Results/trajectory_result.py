#trajectory_result.py
# this class will analyze the trajectory given by the TrackMemory. Hitmaps of the mirrors will be generated, a 3D overview 
# of the trajectory will be plotted, and a top view of it, and all positions and angles will be stored in a .csv file. 
# Also, the intensity of the laser will be analyzed here, taking propagation and reflection into account.
# ALso, from csv files, the trajectory can be reconstructed and analyzed. 

# the input is the track_memory of a ray, and a Config object, and of course a 2d grid for the hitmaps.

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
from Results.Config import Config
from Results.track_memory import TrackMemory
from Results.hitmap import Hitmap
from Results.raystate import Raystate


class TrajectoryResult:
    def __init__(self, track_memory: TrackMemory, config: Config, grid: TwoGrid, cell_dimensions=[50,40,30], hole_location=[1.2,0.0,0.2], mirror_reflection_coefficients=None):
        self.track_memory = track_memory
        self.config = Config(**config) if isinstance(config, dict) else config
        self.grid = grid
        self.cell_dimensions = cell_dimensions
        self.hitmaps = {}
        self.intensity_profile = [] # intensity after each reflection, accounting for losses via reflection and propagation (and later absorption)
        self.hole_u = hole_location[0]
        self.hole_v = hole_location[1]
        self.hole_radius = hole_location[2]
        self.target_reflections = len(self.track_memory.memory) if self.track_memory and self.track_memory.memory else 0
        self.mirror_reflection_coefficients = mirror_reflection_coefficients or {
            "M1": 0.98,
            "M2": 0.98,
            "M3": 0.98
        }

    def analyze_trajectory(self):
        # Run all analyses in a sequence
        try:
            self.generate_hitmaps()
            self.plot_3d_trajectory()
            self.plot_top_view()
            self.save_results()
        except Exception as e:
            print("Error during trajectory analysis:")
            traceback.print_exc()
            
    def calculate_beam_diameters(self, beam_diameter=0.4):
        beam_diameters = []
        current_pos = Vector(0, 20 - 1.2, 25)
        cumulative_path_length = 0.0

        if self.track_memory and self.track_memory.memory:
            for state in self.track_memory.memory:
                next_pos = state.position
                segment_length = (next_pos - current_pos).norm()
                cumulative_path_length += segment_length
                current_pos = next_pos

                current_beam_diameter_mm = PhysicsUtils.calculate_beam_diameter(
                    wavelength=1654e-6,  # mm
                    beam_diameter=beam_diameter * 10.0,  # cm -> mm
                    distance_traveled=cumulative_path_length * 10.0  # cm -> mm
                )

                beam_diameters.append(current_beam_diameter_mm / 10.0)  # mm -> cm

        return beam_diameters
    
    def generate_hitmaps(self, beam_diameter=0.4):
        
        """
        Plot de hitmaps inclusief volgnummers van de inslagen en variabele beam diameter.
        beam_diameter geeft de initiele diameter van de bundel op de spiegeloppervlakken.
        """
        grid_info = self.grid
        # 1. Initialiseer Hitmaps
        self.hitmaps = {
            "M1": Hitmap("M1", grid_info),
            "M2": Hitmap("M2", grid_info),
            "M3": Hitmap("M3", grid_info)
        }

        # 2. Plot instellen
    
        fig, axes = plt.subplots(1, 3, figsize=(20, 6))
        mirror_names = ["M1", "M2", "M3"]
        
        # We houden bij hoeveel hits er per spiegel zijn voor de tekst-offset
        # (zodat nummers elkaar niet perfect overlappen)
        mirror_hit_counts = {"M1": 0, "M2": 0, "M3": 0}

        # 3. Vul de hitmaps EN teken de nummers
        if self.track_memory and self.track_memory.memory:
            for idx, state in enumerate(self.track_memory.memory):
                name = state.mirror_name
                if name in self.hitmaps:
                    # Registreer in de data matrix voor de heatmap-kleur
                    self.hitmaps[name].register_hit(state.u, state.v)
                    
                    # Bepaal in welke subplot we moeten tekenen
                    ax_idx = mirror_names.index(name)
                    ax = axes[ax_idx]
                    
                    # Teken het volgnummer (idx + 1 omdat we bij 1 willen beginnen)
                    # We voegen een kleine offset toe zodat het nummer naast de 'hit' staat
                    ax.text(state.u + 0.1, state.v + 0.1, str(idx + 1), 
                            color='white', fontsize=9, fontweight='bold',
                            bbox=dict(facecolor='black', alpha=0.3, edgecolor='none', pad=0.5))
                    
                    # Teken een klein stipje voor de exacte hit
                    marker_style = 'x' if getattr(state, 'event_type', None) == 'hole_exit' else 'o'
                    marker_color = 'cyan' if getattr(state, 'event_type', None) == 'hole_exit' else 'white'
                    ax.plot(state.u, state.v, marker_style, color=marker_color, markersize=5)
                    
                    # Bereken beam diameter met echte Gauss propagatie (PhysicsUtils)
                    # Bereken CUMULATIEVE padlengte tot deze reflectie (optische afstand!)
                    cumulative_path_length = 0.0
                    start_pos = Vector(0, 20, 25.0)  # M1 positie
                    
                    # Tel alle segmenten op tot deze reflectie
                    current_pos = start_pos
                    for prev_idx in range(idx + 1):  # idx + 1 omdat we tot de huidige reflectie willen gaan
                        if prev_idx == 0:
                            # Eerste segment: van M1 naar eerste reflectie
                            next_pos = self.track_memory.memory[0].position
                        else:
                            # Volgende segmenten: van vorige reflectie naar huidige
                            next_pos = self.track_memory.memory[prev_idx].position
                        
                        segment_length = (next_pos - current_pos).norm()
                        cumulative_path_length += segment_length
                        current_pos = next_pos
                    
                    current_beam_diameter_mm = PhysicsUtils.calculate_beam_diameter(
                        wavelength=1654e-6,  # mm
                        beam_diameter=beam_diameter * 10.0,  # cm -> mm
                        distance_traveled=cumulative_path_length * 10.0  # cm -> mm
                    )
                    current_beam_radius = (current_beam_diameter_mm / 2.0) / 10.0  # mm -> cm
                    
                    beam_circle = plt.Circle((state.u, state.v), current_beam_radius, 
                                           edgecolor='yellow', facecolor='none', 
                                           linestyle='--', linewidth=1.5, alpha=0.7)
                    ax.add_artist(beam_circle)
                    
                    # Voeg label toe met beam diameter info
                    ax.text(state.u - 0.3, state.v - 0.5, f"d={current_beam_radius*2:.2f}", 
                           color='yellow', fontsize=7, style='italic', alpha=0.7)

        # 4. Heatmap styling
        for i, name in enumerate(mirror_names):
            hm = self.hitmaps[name]
            img_data = np.array(hm.data).T 
            extent = [-grid_info.u_range/2, grid_info.u_range/2, 
                    -grid_info.v_range/2, grid_info.v_range/2]
            
            im = axes[i].imshow(img_data, extent=extent, origin='lower', 
                                cmap='hot', interpolation='gaussian', alpha=0.8)
            
            # Teken spiegelrand
            circle = plt.Circle((0, 0), grid_info.u_range/2, color='white', fill=False, linestyle='--')
            axes[i].add_artist(circle)
            
            if name == "M1":
                # Teken de entry hole op M1 (u=-1.2, v=0) - Diameter 0.4 cm, radius 0.2
                entry_hole_circle = plt.Circle((-1.2, 0.0), 0.2, color='red', fill=False, linewidth=2)
                axes[i].add_artist(entry_hole_circle)
                axes[i].annotate("ENTRY", xy=(-1.2, -0.5), color='red', ha='center', fontweight='bold')
            
            if name == "M2":
                # Teken het gat op M2 (u=1.2, v=0) - Diameter 0.4 cm, radius 0.2
                hole_circle = plt.Circle((1.2, 0.0), 0.2, color='cyan', fill=False, linewidth=2)
                axes[i].add_artist(hole_circle)
                axes[i].annotate("EXIT", xy=(1.2, -0.7), color='cyan', ha='center', fontweight='bold')

            axes[i].set_title(f"Mirror {name}")
            axes[i].set_xlabel("u (mm)")
            axes[i].set_ylabel("v (mm)")
            axes[i].set_facecolor('#222222') # Donkere achtergrond voor contrast

        total_bounces = len(self.track_memory.memory) if self.track_memory and self.track_memory.memory else 0
        #ax2 = plt.subplot(1,2,1)
        #ax2.plot(self.calculate_beam_diameters(beam_diameter), marker='o', color='yellow')
        #ax2.grid(True)
        #ax2.set_xlabel("Reflection Step")

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
        
    def analyze_intensity(self, final_beam_diameter=0.6):
        if not self.track_memory or not self.track_memory.memory:
            self.intensity_profile = []
            print("No intensity data available.")
            return []

        current_intensity = 1.0
        self.intensity_profile = [current_intensity]

        for state in self.track_memory.memory:
            if state.mirror_name:
                coef = self.mirror_reflection_coefficients.get(state.mirror_name, 1.0)
            else:
                coef = 1.0

            current_intensity *= coef
            self.intensity_profile.append(current_intensity)
            
        # using calculate_intensityloss, we now also account for the loss due to a smaller hole than beam diameter. 
        print(f"Intensity after reflections: {self.intensity_profile[-1]}")
        final_intensity = PhysicsUtils.calculate_final_intensity(self.intensity_profile[-1], self.hole_radius*2, final_beam_diameter)
        self.intensity_profile.append(final_intensity)
        print(f"final intensity detected: {final_intensity}")
        ax2 = plt.subplot(1,2,2)
        ax2.plot(self.intensity_profile, marker='o')
        ax2.grid(True)
        ax2.set_xlabel("Reflection Step")
        ax2.set_ylabel("Relative Intensity")
        return self.intensity_profile
        
    def plot_3d_trajectory(self):
        fig = plt.figure(figsize=(14, 10))
        ax = fig.add_subplot(111, projection='3d')

        # 1. Cel grenzen
        l, w, h = self.cell_dimensions
        for z in [0, h]:
            ax.plot([0, l, l, 0, 0], [0, 0, w, w, 0], [z, z, z, z, z], color='black', alpha=0.2)
        for x, y in [(0,0), (l,0), (l,w), (0,w)]:
            ax.plot([x, x], [y, y], [0, h], color='black', alpha=0.1)

        # 2. Bereken de werkelijke normalen zoals de simulatie dat doet
        pos_m1 = Vector(0, 20, 25.0)
        pos_m2 = Vector(self.config.m2_x, self.config.m2_y, 25.0)
        pos_m3 = Vector(self.config.m3_x, self.config.m3_y, 25.0)

        n2_base = PhysicsUtils.calculate_ideal_normal(pos_m1, pos_m2, pos_m3)
        n3_base = PhysicsUtils.calculate_ideal_normal(pos_m2, pos_m3, pos_m1)

        rot_m2 = Matrix.rotation_z(math.radians(self.config.m2_phi))
        rot_m3 = Matrix.rotation_z(math.radians(self.config.m3_theta))

        n1_final = Vector(1, 0, 0) # M1 kijkt altijd naar rechts

        n2_final = rot_m2 @ n2_base
        n2_final.z = 0.0
        n2_final = n2_final.normalize()

        n3_final = rot_m3 @ n3_base
        n3_final.z = 0.0
        n3_final = n3_final.normalize()

        # 3. Verbeterde Helper functie voor de spiegel-schijf
        def draw_actual_mirror(pos, normal_vec, color, label, radius=2.5, plane='xy'):
            t = np.linspace(0, 2*np.pi, 50)
            if plane == 'xy':
                xs = pos.x + radius * np.cos(t)
                ys = pos.y + radius * np.sin(t)
                zs = np.full_like(xs, pos.z)
            else:
                xs = np.full_like(t, pos.x)
                ys = pos.y + radius * np.cos(t)
                zs = pos.z + radius * np.sin(t)

            ax.plot(xs, ys, zs, color=color, alpha=0.4, linestyle='--')

            ax.quiver(pos.x, pos.y, pos.z, 
                    normal_vec.x, normal_vec.y, normal_vec.z, 
                    length=5, color=color, pivot='tail', linewidth=2)
            ax.scatter(pos.x, pos.y, pos.z, color=color, s=100, label=label, edgecolors='black')

        path_length = self._calculate_path_length(pos_m1, self.track_memory.memory)

        # Teken de spiegels met hun ECHTE normalen
        draw_actual_mirror(pos_m1, n1_final, 'red', 'M1 (In)', plane='yz')
        draw_actual_mirror(pos_m2, n2_final, 'green', 'M2 (Exit)')
        draw_actual_mirror(pos_m3, n3_final, 'blue', 'M3')

        # 4. Het pad en het gat (ongewijzigd)
        if self.track_memory and self.track_memory.memory:
            points = [(pos_m1.x, pos_m1.y, pos_m1.z)]
            for state in self.track_memory.memory:
                points.append((state.position.x, state.position.y, state.position.z))
            path = np.array(points)
            ax.plot(path[:, 0], path[:, 1], path[:, 2], color='orange', alpha=0.7, label='Ray Path')

        hole_x = self.config.m2_x + self.hole_u
        hole_y = self.config.m2_y + self.hole_v
        ax.scatter(hole_x, hole_y, 25.0, color='purple', s=100, label='Target Hole')

        # Draw target hole outline on M2 plane
        t = np.linspace(0, 2*np.pi, 100)
        hole_xs = hole_x + self.hole_radius * np.cos(t)
        hole_ys = hole_y + self.hole_radius * np.sin(t)
        hole_zs = np.full_like(hole_xs, pos_m2.z)
        ax.plot(hole_xs, hole_ys, hole_zs, color='purple', linestyle='--', linewidth=2, alpha=0.8)

        ax.set_box_aspect([l, w, h])
        ax.legend()
        reflection_count = len(self.track_memory.memory) if self.track_memory and self.track_memory.memory else 0
        ax.set_title(f'Path Length: {path_length:.2f}, Reflections: {reflection_count}')
        plt.savefig(f"geometry_{getattr(self, 'target_reflections', 'unknown')}_bounces.png", dpi=300)
        plt.show()
        
    def plot_top_view(self):
        fig, ax = plt.subplots(figsize=(8, 6))
        l, w = self.cell_dimensions[0], self.cell_dimensions[1]
        ax.plot([0, l, l, 0, 0], [0, 0, w, w, 0], color='black', alpha=0.2)

        if self.track_memory and self.track_memory.memory:
            points = [(state.position.x, state.position.y) for state in self.track_memory.memory]
            path = np.array(points)
            ax.plot(path[:, 0], path[:, 1], color='orange', alpha=0.7, label='Ray path')

            for mirror_name, color in zip(["M1", "M2", "M3"], ['red', 'green', 'blue']):
                xs = [s.position.x for s in self.track_memory.memory if s.mirror_name == mirror_name]
                ys = [s.position.y for s in self.track_memory.memory if s.mirror_name == mirror_name]
                if xs and ys:
                    ax.scatter(xs, ys, color=color, s=30, label=f'{mirror_name} hits', alpha=0.7)

            hole_exits = [s for s in self.track_memory.memory if getattr(s, 'event_type', None) == 'hole_exit']
            if hole_exits:
                hx = [s.position.x for s in hole_exits]
                hy = [s.position.y for s in hole_exits]
                ax.scatter(hx, hy, color='purple', marker='x', s=80, label='Hole exits', linewidths=2)

        # Definieer een kleine offset (bijv. 2 mm naast/boven de spiegel)
        offset = 1.5 

        # Locaties van spiegels plotten (scatter punt + tekst met offset)
        # Spiegel M1
        ax.scatter(0, 20, color='red', s=50, marker='s', label='M1 center')
        ax.text(0 + offset, 20 + offset, 'M1', color='red', fontsize=10, fontweight='bold', va='bottom', ha='left')

        mirror_radius = self.grid.u_range / 2 if self.grid is not None else 2.54
        m1_circle = plt.Circle((0, 20), mirror_radius, color='red', fill=False, linestyle='--', alpha=0.5)
        ax.add_patch(m1_circle)

        # Spiegel M2
        ax.scatter(self.config.m2_x, self.config.m2_y, color='green', s=50, marker='s', label='M2 center')
        ax.text(self.config.m2_x + offset, self.config.m2_y + offset, 'M2', color='green', fontsize=10, fontweight='bold', va='bottom', ha='left')
        m2_circle = plt.Circle((self.config.m2_x, self.config.m2_y), mirror_radius, color='green', fill=False, linestyle='--', alpha=0.5)
        ax.add_patch(m2_circle)

        # Spiegel M3
        ax.scatter(self.config.m3_x, self.config.m3_y, color='blue', s=50, marker='s', label='M3 center')
        ax.text(self.config.m3_x + offset, self.config.m3_y + offset, 'M3', color='blue', fontsize=10, fontweight='bold', va='bottom', ha='left')
        m3_circle = plt.Circle((self.config.m3_x, self.config.m3_y), mirror_radius, color='blue', fill=False, linestyle='--', alpha=0.5)
        ax.add_patch(m3_circle)

        # Target Hole
        hole_x = self.config.m2_x + self.hole_u
        hole_y = self.config.m2_y + self.hole_v
        hole_circle = plt.Circle((hole_x, hole_y), self.hole_radius, color='purple', fill=False, linewidth=2, alpha=0.8)
        ax.add_patch(hole_circle)
        ax.scatter(hole_x, hole_y, color='purple', s=100, label='Target Hole', edgecolors='black', zorder=5)
        ax.text(hole_x + offset, hole_y + offset, 'Hole', color='purple', fontsize=9)

        ax.set_title('Top View of Ray Path')
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        ax.set_xlim(-5, l + 10) # Beetje extra ruimte voor tekst aan de randen
        ax.set_ylim(-5, w + 10)
        ax.set_aspect('equal', adjustable='box')
        ax.grid(True, linestyle=':', alpha=0.5)
        ax.legend(loc='best', fontsize='small')
        
        plt.savefig(f"top_view_{getattr(self, 'target_reflections', 'unknown')}_bounces.png", dpi=300)
        plt.show()
                
    def save_results(self, filename_prefix="geometry"):
        if self.config is None or self.track_memory is None:
            print("No results to save.")
            return
        
        # Save configuration
        config_df = pd.DataFrame([self.config.__dict__])
        reflection_count = len(self.track_memory.memory) if self.track_memory and self.track_memory.memory else 0
        config_df.to_csv(f"{filename_prefix}_{reflection_count}_config.csv", index=False)
        
        # Save track memory
        track_data = [{
            "mirror_name": state.mirror_name,
            "position_x": state.position.x,
            "position_y": state.position.y,
            "position_z": state.position.z,
            "u": state.u,
            "v": state.v
        } for state in self.track_memory.memory]
        
        track_df = pd.DataFrame(track_data)
        track_df.to_csv(f"{filename_prefix}_{reflection_count}_track_memory.csv", index=False)
        print(f"Results saved: {filename_prefix}_{reflection_count}_config.csv and {filename_prefix}_{reflection_count}_track_memory.csv")


class TrajectoryResultsFromCSV(TrajectoryResult):
    def from_csv(cls, config_file, track_memory_file):
        try:
            config_df = pd.read_csv(config_file)
            if config_df.empty:
                print("Config CSV is empty.")
                return None
            config_data = config_df.iloc[0].to_dict()
            config_obj = Config(**config_data)

            track_df = pd.read_csv(track_memory_file)
            track_memory = TrackMemory()
            for _, row in track_df.iterrows():
                raystate = Raystate(
                    mirror_name=row['mirror_name'],
                    position=Vector(row['position_x'], row['position_y'], row['position_z']),
                    u=row['u'],
                    v=row['v']
                )
                track_memory.add_state(raystate)

            return cls(track_memory, config_obj, grid=None)  # Grid moet nog worden ingesteld
        except Exception as e:
            print("Error loading from CSV:")
            traceback.print_exc()
            return None
        
    def analyze_csv_trajectory(self, config_file, track_memory_file):
        result = self.from_csv(config_file, track_memory_file)
        if result:
            result.analyze_trajectory()
            result.plot_3d_trajectory()
            result.plot_top_view()
