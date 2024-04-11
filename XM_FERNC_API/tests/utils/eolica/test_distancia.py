import unittest
from utils.eolica.distancia import distancia_geodesica, haversine

class PruebasDistanciaGeodesica(unittest.TestCase):

    def test_distancia_basica(self):
        # Distancia entre dos puntos conocidos
        self.assertAlmostEqual(distancia_geodesica(40.7128, -74.0060, 1, 34.0522, -118.2437, 19), 3944, delta=10)

    def test_misma_ubicacion(self):
        # La distancia entre un punto y él mismo debe ser 0
        self.assertEqual(distancia_geodesica(40.7128, -74.0060, 1, 40.7128, -74.0060, 1), 0)

    def test_distancia_invalida(self):
        # Prueba con coordenadas inválidas (fuera de los límites de latitud y longitud)
        with self.assertRaises(ValueError):
            distancia_geodesica(100, -74.0060, 1, 34.0522, -118.2437, 19)

    def test_harversine(self):
        resultado = haversine(12.29263, -71.226417, 12.287679, -71.226417)
        self.assertAlmostEqual(resultado, 0.55052, places=2)