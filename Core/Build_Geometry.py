# Build_Geometry.py
# This class will build a geometry given by a configuration file. This class is supossed to 
# make a more realistic gass cell, with rounded coordinates, since the coordinates given by the 
# configurations (from the optimization) are not rounded, and thus not realistic for allignment.
# This class will round upto a fraction of a mm. 

# the methods this class need are at least one which reads the configuration file, and another one 
# which builds the geometry, after another method rounds the numbers.
# Another method will store the rounded geometry. The GasCell object will then run the simulation.

import csv
import sys
import os
from dataclasses import dataclass, asdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import math
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import traceback

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
from Results.trajectory_result import TrajectoryResult, TrajectoryResultsFromCSV
from Results.Config import Config
from Core.open_csv import CSVLoader
from Core.FindingGeometry import FindingGeometry

class BuildGeometry: 
    def __init__(self, config_file):
        self.config_file = config_file
        
    def read_config(self):
        # Read the config file, and store in a Config data object. 
        # the config file is csv, with the first row the headers, second row the values.
        # we can use open_csv.py for this.
        try:
            csv_loader = CSVLoader()
            config = csv_loader.load_config_from_csv(self.config_file)
            return config
        except Exception as e:
            print("Error reading config file:", e)
            traceback.print_exc()
            raise
        
    def Translate_angles(self, config):
        """
        Vertaalt de hoeken van de optimizer (t.o.v. ideale normaal) naar absolute hoeken,
        waarbij de normaal van spiegel 1 exact 0 graden maakt.
        Ook vertaalt ray_pitch naar absolute fysieke hoek (t.o.v. ideale richting naar target op M2).
        """
        # Posities van de spiegels
        pos_m1 = Vector(0, 20, 25.0)
        pos_m2 = Vector(config.m2_x, config.m2_y, 25.0)
        pos_m3 = Vector(config.m3_x, config.m3_y, 25.0)
        
        # Bereken ideale normalen vanaf het daadwerkelijke entry-hole punt op M1
        entry_hole_world = pos_m1 + Vector(0, -1.2, 0)
        n2_base = PhysicsUtils.calculate_ideal_normal(entry_hole_world, pos_m2, pos_m3)
        n3_base = PhysicsUtils.calculate_ideal_normal(pos_m2, pos_m3, entry_hole_world)
        
        # Bereken de ideale hoeken (in graden) t.o.v. de x-as
        ideal_m2_angle = math.degrees(math.atan2(n2_base.y, n2_base.x))
        ideal_m3_angle = math.degrees(math.atan2(n3_base.y, n3_base.x))
        
        # Absolute hoeken = ideale hoek + offset van optimizer
        absolute_m2_phi = ideal_m2_angle + config.m2_phi
        absolute_m3_theta = ideal_m3_angle + config.m3_theta
        
        # Voor ray_pitch: geen ideale richting, het is offset van base_dir naar target
        absolute_ray_pitch = config.ray_pitch
        absolute_ray_yaw = config.ray_yaw  # Voor consistentie
        
        # Retourneer nieuwe config met absolute hoeken
        translated_config = Config(
            m2_x=config.m2_x,
            m2_y=config.m2_y,
            m3_x=config.m3_x,
            m3_y=config.m3_y,
            m2_phi=absolute_m2_phi,
            m3_theta=absolute_m3_theta,
            ray_pitch=absolute_ray_pitch,
            ray_yaw=absolute_ray_yaw
        )
        
        return translated_config
    def round_config(self, config, dist_precision=2, angle_precision=3):
        """
        Rondt de optimizer-configuratie af.
        Dit werkt op dezelfde parameterruimte als de configuratie uit de optimizer,
        niet op de fysiek-vertalen absolute hoeken van `Translate_angles`.
        dist_precision: aantal decimalen voor cm (2 = 0.01 cm = 0.1 mm)
        angle_precision: aantal decimalen voor hoeken
        """
        
        # Gebruik de ingebouwde round(val, n) om de binair-fout te minimaliseren
        rounded_config = Config(
            # Afstanden (cm)
            m2_x = round(config.m2_x, dist_precision),
            m2_y = round(config.m2_y, dist_precision),
            m3_x = round(config.m3_x, dist_precision),
            m3_y = round(config.m3_y, dist_precision),
            
            # Hoeken (bijv. graden)
            m2_phi = round(config.m2_phi, angle_precision),
            m3_theta = round(config.m3_theta, angle_precision),
            
            # Ray parameters
            ray_pitch = round(config.ray_pitch, angle_precision),
            ray_yaw = round(config.ray_yaw, angle_precision)
        )
        
        return rounded_config
    
    def save_rounded_config(self, config, output_file_path):
        """
        Slaat de Config op als CSV in het standaard format (Headers + 1 datarow).
        """
        try:
            # 1. Definieer de kolomnamen (headers) in de juiste volgorde
            headers = [
                "m2_x", "m2_y", "m3_x", "m3_y", 
                "m2_phi", "m3_theta", "ray_pitch", "ray_yaw"
            ]
            
            # 2. Haal de waarden uit het config object
            data = [
                config.m2_x, config.m2_y, config.m3_x, config.m3_y,
                config.m2_phi, config.m3_theta, config.ray_pitch, config.ray_yaw
            ]
            
            # 3. Zorg dat de directory bestaat
            directory = os.path.dirname(output_file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # 4. Schrijf naar CSV
            with open(output_file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(headers)
                writer.writerow(data)
                
            print(f"Succes: Afgeronde configuratie opgeslagen in: {output_file_path}")
            
        except Exception as e:
            print(f"Error bij het opslaan van de config: {e}")
            traceback.print_exc()
            
    def calculate_normal_from_angles(self, angle):
        # Calculate the normal vector from given angle in degrees. We assume the beam stays in xy plane.
        rad = math.radians(angle)
        normal = Vector(math.cos(rad), math.sin(rad), 0).normalize()
        return normal
            
    def build_gas_cell(self, config, optical_height = 25.0, cell_dimensions = (50,40,50),
                       hole_radius = 0.2, mirror_radius = 5.08, entry_hole_pos = Vector(-1.2,0,0), exit_hole_pos = Vector(1.2,0,0),
                       first_reflection_u=None, first_reflection_v=None): # <-- Voeg deze argumenten toe
        try: 
            cell_geo = CellGeometry(name="RoundedCell", cell_dimensions=cell_dimensions)
        
            pos_m1 = Vector(0, 20, optical_height)  
            pos_m2 = Vector(config.m2_x, config.m2_y, 25.0)
            pos_m3 = Vector(config.m3_x, config.m3_y, 25.0)
            
            norm_m1 = Vector(1, 0, 0).normalize()
            v_ref = Vector(0, 0, 1)
            u_dir_m1 = v_ref.cross(norm_m1).normalize()
            v_dir_m1 = norm_m1.cross(u_dir_m1).normalize()
            entry_hole_world = pos_m1 + (u_dir_m1 * entry_hole_pos.x) + (v_dir_m1 * entry_hole_pos.y)
            
            # Bereken de ideale spiegels zoals FindingGeometry dat doet
            n2_base = PhysicsUtils.calculate_ideal_normal(pos_m1, pos_m2, pos_m3)
            rot_m2 = Matrix.rotation_z(math.radians(config.m2_phi))
            n2_final = (rot_m2 @ n2_base).normalize()
            n2_final.z = 0
            
            n3_base = PhysicsUtils.calculate_ideal_normal(pos_m2, pos_m3, pos_m1)
            rot_m3 = Matrix.rotation_z(math.radians(config.m3_theta))
            n3_final = (rot_m3 @ n3_base).normalize()
            n3_final.z = 0
            
            entry_hole = Hole("Entry", origin=entry_hole_pos, radius=hole_radius, grid=None)
            exit_hole = Hole("Exit", origin=exit_hole_pos, radius=hole_radius, grid=None)
            
            mirror1 = Mirror(name= 'M1', origin=pos_m1, normal=norm_m1, grid = TwoGrid(mirror_radius, mirror_radius, 0.1), hole=entry_hole)
            mirror2 = Mirror(name= 'M2', origin=pos_m2, normal=n2_final, grid = TwoGrid(mirror_radius, mirror_radius, 0.1), hole=exit_hole)
            mirror3 = Mirror(name = 'M3', origin=pos_m3, normal=n3_final, grid=TwoGrid(mirror_radius, mirror_radius, 0.1), hole=None)
            
            cell_geo.add_mirror(mirror1)    
            cell_geo.add_mirror(mirror2)
            cell_geo.add_mirror(mirror3)

            u_dir_m2, v_dir_m2, _ = mirror2.get_local_axes()
            exit_hole_world = pos_m2 + (u_dir_m2 * exit_hole_pos.x) + (v_dir_m2 * exit_hole_pos.y)

            cell_geo.add_inlet(entry_hole_world)
            cell_geo.add_outlet(exit_hole_world)
            
            # Gebruik de gekoppelde eerste reflectie op M2 zoals in FindingGeometry
            if first_reflection_u is not None and first_reflection_v is not None:
                target_point = pos_m2 + (u_dir_m2 * first_reflection_u) + (v_dir_m2 * first_reflection_v)
            else:
                target_point = pos_m2

            # In FindingGeometry wordt de basisrichting vanaf M1 berekend
            base_dir = (target_point - pos_m1).normalize()

            ray_dir = (
                Matrix.rotation_y(math.radians(config.ray_yaw)) @ 
                Matrix.rotation_z(math.radians(config.ray_pitch))
            ) @ base_dir
            ray_dir = ray_dir.normalize()
            
            lightray = Lightray(origin=entry_hole_world + (ray_dir * 0.01), direction=ray_dir)  
            
            gas_cell = GasCell(cell_geometry=cell_geo)
            return gas_cell, lightray, entry_hole_world
        
        except Exception as e:
            print("Error bij het bouwen van de gascel:", e)
            traceback.print_exc()
            raise
        
    def run_simulation(self, lightray: Lightray, gas_cell: GasCell, config: Config,  max_reflections: int=33):
        # first, calculate initial ray direction from config angles
        try:
            TrackMem = gas_cell.run_simulation(initial_ray=lightray, max_reflections=max_reflections)
            return TrackMem            
        except Exception as e:
            print("Error bij het uitvoeren van de simulatie:", e)

def to_format_dict(config_obj: Config) -> dict:
    return asdict(config_obj)

# test
if __name__ == "__main__": 
    config_file_path = "OptimizedGeometries/16Reflections/geometry_16_config.csv"
    builder = BuildGeometry(config_file_path)
    original_config = builder.read_config()
    print('original', original_config)
    translated_config = builder.Translate_angles(original_config)
    print('translated', translated_config)
    # Rond het originele optimizer-configuratieobject af, niet de al voorvertaalde absolute hoeken.
    rounded_config = builder.round_config(original_config)
    print('rounded', rounded_config)
    #output_file_path = "GasCellOptimalizations/best_geometry_22_config_ROUNDED.csv"
    #builder.save_rounded_config(rounded_config, output_file_path)
    
    gas_cell, lightray, entry_hole_world = builder.build_gas_cell(original_config, first_reflection_u=-2, first_reflection_v=0.0)  # <-- Voeg hier de eerste reflectie coördinaten toe
    track_memory = builder.run_simulation(lightray=lightray, gas_cell=gas_cell, config=original_config)
    print(len(track_memory))
    resultbuilder = TrajectoryResult(track_memory=track_memory, config=original_config, grid=TwoGrid(5.08,5.08,0.10))
    resultbuilder.analyze_trajectory()
    
    gas_cell_rounded, lightray_rounded, entry_hole_world = builder.build_gas_cell(rounded_config, first_reflection_u=-2, first_reflection_v=0.0)
    track_memory_rounded = builder.run_simulation(lightray=lightray_rounded, gas_cell=gas_cell_rounded, config=rounded_config)
    print(len(track_memory_rounded))
    resultroundedbuilder = TrajectoryResult(track_memory=track_memory_rounded, config=rounded_config, grid=TwoGrid(5.08,5.08,0.10))
    resultroundedbuilder.analyze_trajectory()
    
    """
    # now try to use the _setup_cell method from finding geometry, to see if we get the same answers.
    Optimized = FindingGeometry(target_reflections=13, iterations=100000, first_reflection_u=-2, first_reflection_v=0.0, hole_diameter=0.4, entry_hole_diameter=0.4)
    # translate the original config to the dict type that is used in the optimizer.
    dict_config = to_format_dict(original_config)
    cell_from_finder, ray_from_finder = Optimized._setup_cell(config=dict_config)
    ray=Lightray(entry_hole_world + (ray_from_finder * 0.01), ray_from_finder)
    track_memory_optimized = cell_from_finder.run_simulation(initial_ray=ray, max_reflections=33)
    print(len(track_memory_optimized))
    
    # now for the rounded config:
    dict_config_rounded = to_format_dict(rounded_config)
    cell_from_finder_rounded, ray_from_finder_rounded = Optimized._setup_cell(config=dict_config_rounded)
    ray_rounded=Lightray(entry_hole_world + (ray_from_finder_rounded * 0.01), ray_from_finder_rounded)
    track_memory_optimized_rounded = cell_from_finder_rounded.run_simulation(initial_ray=ray_rounded, max_reflections=33)
    print(len(track_memory_optimized_rounded))

    # now, we are going to compare the different track memories, using the analysis software.
    #Result1 = TrajectoryResult(track_memory=track_memory_optimized, config=original_config, grid=TwoGrid(5.08, 5.08, 0.1))
    #Result1.analyze_trajectory()
    #Result2 = TrajectoryResult(track_memory=track_memory_optimized_rounded, config=rounded_config, grid=TwoGrid(5.08, 5.08, 0.1))
    #Result2.analyze_trajectory()
    """
