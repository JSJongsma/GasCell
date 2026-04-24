# grid.py
from Math.vector import Vector
from Math.matrix import Matrix

class TwoGrid:
    """2D grid in lokaal spiegelvlak (u,v)"""

    def __init__(self, u_range, v_range, spacing, origin=None, local_to_world=None):
        # define the parameters of the grid itself.
        self.u_range = u_range 
        self.v_range = v_range
        self.spacing = spacing
        
        # define the parameters of the grid in the world. The origin is the center of the grid in world coordinates,
        # and local_to_world is a Matrix that transforms from local (u,v) to world coordinates.
        self.origin = origin if origin else Vector(0, 0, 0)
        self.local_to_world = local_to_world if local_to_world else Matrix.identity()

        # Handig voor de hitmap later: bereken vast het aantal vakjes
        self.u_bins = int(self.u_range / self.spacing)
        self.v_bins = int(self.v_range / self.spacing)

    def generate_points_local(self):
        """Genereer punten in lokaal (u,v) vlak, gecentreerd rond (0,0)"""
        points = []
        u_start = -self.u_range / 2
        v_start = -self.v_range / 2

        for i in range(self.u_bins + 1):
            for j in range(self.v_bins + 1):
                u = u_start + i * self.spacing
                v = v_start + j * self.spacing
                # We gebruiken hier je Vector class
                points.append(Vector(u, v, 0)) 
        return points

    def generate_points_world(self):
        """Zet lokaal grid om naar wereldcoördinaten met de Matrix en origin"""
        local_points = self.generate_points_local()
        world_points = []

        for p in local_points:
            # Hier gebruiken we de nieuwe @ operator of apply_to_Vector
            pw = (self.local_to_world @ p) + self.origin
            world_points.append(pw)

        return world_points