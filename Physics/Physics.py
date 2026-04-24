# Physics utils

import sys
import os

# Voeg de hoofdmap van het project toe aan het pad (één niveau boven Math)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import math
from Math.vector import Vector

class PhysicsUtils:
    """
    Bevat de wiskundige en natuurkundige kernformules voor de simulatie.
    """
    @staticmethod
    def calculate_ideal_normal(source_pos: Vector, mirror_pos: Vector, target_pos: Vector) -> Vector:
        """
        Berekent de normaalvector die een straal van source exact naar target reflecteert.
        acts as an 'auto align' tool. It calculates the normal for which a mirror reflects a ray exactly at the target,
        dependent on the input ray and positions of the mirror and target mirror.
        """
        # 1. Vectoren bepalen en normaliseren
        v_in = (mirror_pos - source_pos).normalize()   # Richting naar de spiegel
        v_out = (target_pos - mirror_pos).normalize()  # Gewenste richting vanaf spiegel
        
        # 2. De bisector (halveringslijn) is de ideale normaal
        # n = (v_out - v_in) / |v_out - v_in|
        ideal_normal = (v_out - v_in).normalize()
        
        return ideal_normal

    @staticmethod
    def get_intersection_distance(ray_origin: Vector, ray_direction: Vector, 
                                 plane_origin: Vector, plane_normal: Vector) -> float:
        """
        Berekent de afstand 't' tot het snijpunt met een vlak. Cruciaal voor de intensiteit.
        Formule: t = ((P_vlak - P_straal) . n) / (d . n)
        """
        dot_product = ray_direction.dot(plane_normal)
        
        # Check of de straal niet (bijna) parallel loopt aan het vlak
        if abs(dot_product) < 1e-10:
            return float('inf')
        
        relative_pos = plane_origin - ray_origin
        t = relative_pos.dot(plane_normal) / dot_product
        
        # We negeren snijpunten in het verleden (t < 0)
        return t if t > 1e-9 else float('inf')

    @staticmethod
    def calculate_beer_lambert(intensity: float, distance: float, alpha: float) -> float:
        """
        Berekent de overgebleven intensiteit na absorptie door gas.
        I = I0 * exp(-alpha * L)
        """
        if alpha == 0: return intensity
        return intensity * math.exp(-alpha * distance)

    @staticmethod
    def reflect_vector(incident_dir: Vector, normal: Vector) -> Vector:
        """
        Berekent de reflectievector: r = d - 2(d . n)n
        Deze methode berekent puur de nieuwe richting van de gereflecteerde straal.
        """
        d = incident_dir.normalize()
        n = normal.normalize()
        dot = d.dot(n)
        return (d - n * (2.0 * dot)).normalize()
    
    @staticmethod
    def calculate_beam_diameter(wavelength = 1654e-6, beam_diameter = 0.2, distance_traveled=9000) -> float:
        """
        This class must calculate the divergence of a beam between reflections.
        We want to calculate the beam width at the mirror reflections, to characterize
        the beam size, for further optimization. This method is calculated in mm. 
        
        The calculation is based on w(z)=w_0*sqrt(1+(\lambda*z/(\pi*w_0^2))^2), where w_0
        is the beam waist (half of the initial diameter) and z is the distance traveled.
        
        There are already methods to calculate the distance traveled, so this can be used
        to calculate the beam width at each reflection point.
        """
        w_0 = beam_diameter / 2.0
        z = distance_traveled
        w = w_0*math.sqrt(1+((wavelength*z)/(math.pi*w_0**2))**2)
        
        return 2*w
    
    @staticmethod
    def compute_beam_diameter_at_reflections(self, start_pos, initial_diameter, states, wavelength = 1654e-6):
        """
        Use the states in track_mem to calculate the beam diameter at each reflection.
        We do this with the static method divergence(wavelength, distance, initial_diameter)
        First, we have to know the distance between the reflection points, from track_mem. 
        Then, we can calculate the diameter at each reflection and return a list of diameters.]
        
        we also want to implement a optimalization eventually, that tries to minimize the intensity 
        loss due to a beam diameter wider than the hole, making this calculation crucial.
        """
        if not states:
            return []
        
        # initial diameter 
        diameter = []
        for state in states:
            # calculate the diameter after a certain distance traveled.
            d = PhysicsUtils.calculate_beam_diameter(wavelength,
                                                     initial_diameter,
                                                     state.path_length)
            diameter.append(d)
    
        return diameter
    
    @staticmethod
    def calculate_final_intensity(I_old, hole_diameter, beam_diameter):
        """
        This method calculates the intensity loss due to a beam diameter wider than the hole.
        We can use the formula: I_loss = 1 - (A_hole / A_beam), where A_hole is the area of the hole and A_beam is the area of the beam.
        This is a crucial method for optimization, as we want to minimize this loss.
        """
        A_hole = math.pi * (hole_diameter / 2)**2
        A_beam = math.pi * (beam_diameter / 2)**2
        
        if A_beam == 0:
            return 1.0  # Total loss if beam diameter is zero
        
        I_final = I_old * (1-math.exp(-2*(hole_diameter/2)**2 / (beam_diameter/2)**2))

        return I_final  # Clamp between 0 and 1
    

