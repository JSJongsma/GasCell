
class Vector:
    def __init__(self, x: float, y: float, z: float):
        # define the components of the Vector
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    # Representation of the Vector
    def __repr__(self):
        return f"Vector({self.x}, {self.y}, {self.z})"

    # Basic operations
    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float): # mult with a scalr
        return Vector(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float):
        return self.__mul__(scalar)

    # Length and normalization
    def norm(self):
        return (self.x**2 + self.y**2 + self.z**2)**0.5

    def normalize(self):
        n = self.norm()
        if n == 0:
            raise ValueError("Cannot normalize zero Vector")
        return Vector(self.x/n, self.y/n, self.z/n)

    # Dot and cross
    def dot(self, other):
        return self.x*other.x + self.y*other.y + self.z*other.z

    def cross(self, other):
        return Vector(
            self.y*other.z - self.z*other.y,
            self.z*other.x - self.x*other.z,
            self.x*other.y - self.y*other.x
        )

    # Afstand
    def distance_to(self, other):
        return (self - other).norm()

