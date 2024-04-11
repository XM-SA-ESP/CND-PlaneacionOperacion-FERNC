import unittest
from unittest.mock import MagicMock
from XM_FERNC_API.utils.eolica.dataclasses_eolica import Torre

class TestTorre(unittest.TestCase):
    def setUp(self):
        self.config_anemometro = MagicMock()
        self.dataframe = MagicMock()
        self.torre = Torre(
            id="1",
            latitud=40.0,
            longitud=-3.0,
            elevacion=100.0,
            radio_r=5.0,
            conf_anemometro=self.config_anemometro,
            archivo_series="archivo.csv",
            dataframe=self.dataframe,
        )

    def test_comparar_distancia_dentro_del_radio(self):
        coord_aerogenerador = (40.001, -3.001, 19)
        distancia = self.torre.obtener_distancia(coord_aerogenerador)
        result = self.torre.comparar_distancia(distancia)
        self.assertTrue(result)

    def test_comparar_distancia_en_el_borde_del_radio(self):
        coord_aerogenerador = (40.005, -3.005, 19)
        distancia = self.torre.obtener_distancia(coord_aerogenerador)
        result = self.torre.comparar_distancia(distancia)
        self.assertTrue(result)

    def test_comparar_distancia_fuera_del_radio(self):
        coord_aerogenerador = (40.1, -3.01, 19)
        distancia = self.torre.obtener_distancia(coord_aerogenerador)
        result = self.torre.comparar_distancia(distancia)
        self.assertFalse(result)

    def test_obtener_distancia(self):
        coord_aerogenerador = (40.001, -3.001, 19)
        distancia = self.torre.obtener_distancia(coord_aerogenerador)
        self.assertAlmostEqual(distancia, 0.16180507224746996)
