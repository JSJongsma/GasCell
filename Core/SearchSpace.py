# SearchSpace.py
# this class will generate the test geometries for the optimization process, based on the parameters of the problem.
# We have certain constraints in this problem, which can be varied in this class.

import sys
import os

# Pad-instellingen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import random
import numpy as np
from Math.vector import Vector


class SearchSpace:
    def __init__(self):
        # Basis posities (startpunt voor Hill-Climbing)
        self.m2_base = {"x": 42.5, "y": 7}
        self.m3_base = {"x": 37.5, "y": 32.0}

        # Basis hoeken (wordt geüpdatet bij elke nieuwe topscore)
        self.best_pitch = 0.0
        self.best_yaw = 0.0
        self.best_m2_phi = 0.0
        self.best_m2_theta = 0.0
        self.best_m3_phi = 0.0
        self.best_m3_theta = 0.0

        # Zoekbereik (wordt kleiner naarmate we dichterbij komen)
        self.pos_range = 2.5
        self.mirror_angle_range = 2
        self.ray_angle_range = 0.1

    def get_random_config(self):
        return {
            "m2_x": self.m2_base["x"] + random.uniform(-self.pos_range, self.pos_range),
            "m2_y": self.m2_base["y"] + random.uniform(-self.pos_range, self.pos_range),
            "m3_x": self.m3_base["x"] + random.uniform(-self.pos_range, self.pos_range),
            "m3_y": self.m3_base["y"] + random.uniform(-self.pos_range, self.pos_range),
            # Spiegel hoek offsets (phi = hor, theta = vert)
            "m2_phi": self.best_m2_phi + random.uniform(-self.mirror_angle_range, self.mirror_angle_range),
            "m3_theta": self.best_m3_theta + random.uniform(-self.mirror_angle_range, self.mirror_angle_range),
            # Laser start hoeken
            "ray_pitch": self.best_pitch + random.uniform(-self.ray_angle_range, self.ray_angle_range),
            "ray_yaw":  0 #+ random.uniform(-self.ray_angle_range, self.ray_angle_range),
        }
        

    def perturb(self, current_config):
        # Maak een nieuwe configuratie op basis van de huidige, met kleine willekeurige stappen
        new_cfg = current_config.copy()
        
        pos_limits = {
            "m2_x": (40, 45), 
            "m2_y": (5, 11),
            "m3_x": (35, 40), 
            "m3_y": (31, 35)
        }

        # Perturb positions
        for key, (low, high) in pos_limits.items():
                step = random.uniform(-self.pos_range, self.pos_range)
                if random.random() < 0.05: step *= 10
                new_cfg[key] = np.clip(new_cfg[key] + step, low, high)

        max_mirror_angle = 6
        for key in ["m2_phi", "m3_theta"]:
            step = random.uniform(-self.mirror_angle_range, self.mirror_angle_range)
            if random.random() < 0.05: step *= 10
            new_cfg[key] = np.clip(new_cfg[key] + step, -max_mirror_angle, max_mirror_angle)

        # Perturb laser angles MET harde grens
        max_ray_angle = 3
        for key in ["ray_pitch"]: #, "ray_yaw"]:
            step = random.uniform(-self.ray_angle_range, self.ray_angle_range)
            if random.random() < 0.05: step *= 10
            new_cfg[key] = np.clip(new_cfg[key] + step, -max_ray_angle, max_ray_angle)      

        # In perturb:
        new_cfg["ray_yaw"] = 0.0 # Forceer altijd 0
        return new_cfg

    def get_description(self, config):
        return (
            f"M2: ({config['m2_x']:.2f}, {config['m2_y']:.2f}) | "
            f"M3: ({config['m3_x']:.2f}, {config['m3_y']:.2f}) | "
            f"Ray: P:{config['ray_pitch']:.3f}°, Y:{config['ray_yaw']:.3f}°"
        )

