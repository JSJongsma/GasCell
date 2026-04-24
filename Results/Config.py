#Config.py
# this dataclass will store configurations of 3 mirrors their positions and angles. 

from dataclasses import dataclass

@dataclass(frozen=True) # Frozen maakt het onveranderbaar, wat veilig is voor optimalisatie
class Config:
    m2_x: float
    m2_y: float
    m3_x: float
    m3_y: float
    m2_phi: float
    m3_theta: float
    ray_pitch: float
    ray_yaw: float = 0.0

    def to_dict(self):
        return self.__dict__
    
    def __str__(self):
        return (f"Config(m2_x={self.m2_x}, m2_y={self.m2_y}, m3_x={self.m3_x}, m3_y={self.m3_y}, "
                f"m2_phi={self.m2_phi}, m3_theta={self.m3_theta}, ray_pitch={self.ray_pitch}, ray_yaw={self.ray_yaw})")
    
"""
best_dict = {
    'm2_x': 37.518, 
    'm2_y': 8.141, 
    'm3_x': 37.293, 
    'm3_y': 32.496, 
    'm2_phi': -5.0, 
    'm3_theta': -4.842, 
    'ray_pitch': 0.213, 
    'ray_yaw': 0.0
}

config_obj = Config(**best_dict) # unpacking dict to create config object
print(config_obj.__str__())

"""