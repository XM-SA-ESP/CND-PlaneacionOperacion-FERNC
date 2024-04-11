import unittest

from utils.eolica import calculos_estela
from utils.eolica.dataclasses_eolica import Aerogenerador


class TestCalculosEstela(unittest.TestCase):
    def setUp(self):
        self.mock_aero1 = Aerogenerador(
            id_aero=1,
            id_torre="torre_1",
            modelo="enercon",
            latitud=12.29263,
            longitud=-71.226417,
            elevacion=1,
        )
        self.mock_aero2 = Aerogenerador(
            id_aero=2,
            id_torre="torre_1",
            modelo="enercon",
            latitud=12.287679,
            longitud=-71.226417,
            elevacion=2,
        )

    def test_calculo_x_dist(self):
        resultado = calculos_estela.calculo_x_dist(
            0.12, self.mock_aero1, self.mock_aero2, 2
        )
        self.assertAlmostEqual(resultado, 65.9046, places=2)

    def test_obtener_slon_slat(self):
        resultado = calculos_estela.obtener_slon_slat(self.mock_aero1, self.mock_aero2)
        resultado_esperado = (0, -1)
        assert resultado == resultado_esperado
