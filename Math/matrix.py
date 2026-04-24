from Math.vector import Vector
import math

class Matrix:
    """Basis operaties voor 3x3 matrices en transformaties."""
    
    def __init__(self, rows):
        # rows is een lijst van 3 lijsten, elk met 3 floats
        self.m = rows

    def __repr__(self):
        return f"Matrix({self.m})"

    def __matmul__(self, other):
        """
        Ondersteunt de @ operator voor:
        1. Matrix @ Vector -> geeft een nieuwe Vector
        2. Matrix @ Matrix -> geeft een nieuwe Matrix
        """
        # Geval 1: Matrix @ Vector
        if isinstance(other, Vector): # check if other is vector object
            x = self.m[0][0] * other.x + self.m[0][1] * other.y + self.m[0][2] * other.z
            y = self.m[1][0] * other.x + self.m[1][1] * other.y + self.m[1][2] * other.z
            z = self.m[2][0] * other.x + self.m[2][1] * other.y + self.m[2][2] * other.z
            return Vector(x, y, z)

        # Geval 2: Matrix @ Matrix
        elif isinstance(other, Matrix): # check if other is matrix object
            result = [[0.0] * 3 for _ in range(3)]
            for i in range(3): # loop through rows of self
                for j in range(3): # loop through columns of other
                    result[i][j] = (
                        self.m[i][0] * other.m[0][j] +
                        self.m[i][1] * other.m[1][j] +
                        self.m[i][2] * other.m[2][j]
                    ) # inproduct of row i of self and column j of other
            return Matrix(result)
        
        else:
            raise TypeError(f"Vermenigvuldiging met type {type(other)} niet ondersteund.")

    def transpose(self):
        """Geeft de getransponeerde matrix terug."""
        return Matrix([
            [self.m[0][0], self.m[1][0], self.m[2][0]],
            [self.m[0][1], self.m[1][1], self.m[2][1]],
            [self.m[0][2], self.m[1][2], self.m[2][2]]
        ])

    # these static methods do not require an instance. When these methods are called, they make a new instance of the matrix 
    # defined in the method.
    @staticmethod
    def identity():
        """Geeft de 3x3 eenheidsmatrix terug."""
        return Matrix([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ])

    @staticmethod
    def rotation_x(theta):
        """Maakt een rotatiematrix om de X-as (theta in radialen)."""
        c, s = math.cos(theta), math.sin(theta)
        return Matrix([
            [1, 0,  0],
            [0, c, -s],
            [0, s,  c]
        ])

    @staticmethod
    def rotation_y(theta):
        """Maakt een rotatiematrix om de Y-as (theta in radialen)."""
        c, s = math.cos(theta), math.sin(theta)
        return Matrix([
            [ c, 0, s],
            [ 0, 1, 0],
            [-s, 0, c]
        ])

    @staticmethod
    def rotation_z(theta):
        """Maakt een rotatiematrix om de Z-as (theta in radialen)."""
        c, s = math.cos(theta), math.sin(theta)
        return Matrix([
            [c, -s, 0],
            [s,  c, 0],
            [0,  0, 1]
        ])

    # Form a orthonormal basis from a normal vector n. This is useful for transforming between world and local mirror coordinates.
    @staticmethod
    def from_normal(n):
        """
        Creëert een orthonormale basis (Matrix) waarbij de Z-as 
        overeenkomt met de gegeven normaalvector n.
        Handig voor transformaties van Wereld naar Lokaal vlak.
        """
        # Zorg dat n genormaliseerd is
        n = n.normalize()

        # Kies een referentie-as voor v zodat lokale v zoveel mogelijk overeenkomt
        # met de wereld-z-as wanneer de spiegel verticaal staat.
        if abs(n.z) < 0.999:
            v = Vector(0, 0, 1)
        else:
            # Als de spiegel bijna horizontaal is, gebruiken we een andere referentie
            v = Vector(0, 1, 0)

        # u = vector loodrecht op v en n
        u = v.cross(n).normalize()

        # v = vector loodrecht op n en u (zodat de basis orthonormaal blijft)
        v = n.cross(u).normalize()

        # De matrix wordt hier opgebouwd met de lokale basisvectoren als rijen:
        # [u, v, n]. Dat betekent dat deze matrix punten uit wereldcoördinaten
        # naar lokale mirrorcoördinaten (u,v,z) transformeert.
        return Matrix([
            [u.x, u.y, u.z],
            [v.x, v.y, v.z],
            [n.x, n.y, n.z]
        ])

if __name__ == "__main__":
    # Test: Rotatie van 90 graden om Z (ongeveer 1.57 radialen)
    test_m = Matrix.rotation_z(math.pi / 2)
    print("Rotatiematrix Z (90 graden):")
    print(test_m)
    
    # Test Matrix @ Vector
    v = Vector(1, 0, 0)
    v_transformed = test_m @ v
    print(f"\nVector {v} na rotatie: {v_transformed}")