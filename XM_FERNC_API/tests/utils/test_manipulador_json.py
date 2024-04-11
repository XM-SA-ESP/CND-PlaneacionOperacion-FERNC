import json
import unittest
from unittest.mock import MagicMock, Mock, patch

from infraestructura.models.eolica.parametros import JsonModelEolica
from utils.manipulador_modelos import ManipuladorModelos


class TestManipuladorModelos(unittest.TestCase):
    def setUp(self):
        self.manipulador_modelos = ManipuladorModelos()
        with open("./tests/data/test_json_data_actualizar_aerogeneradores.json") as f:
            json_data = json.load(f)
        self.json_esperado = JsonModelEolica(**json_data)

    def test_ajustar_aerogeneradores(self):
        with open("./tests/data/test_json_data_eolica.json") as f:
            json_data = json.load(f)
        params = JsonModelEolica(**json_data)
        coord_aero = (12.28768, -71.22642)
        diccionario_mock = {
            'torre_1': Mock(obtener_distancia=lambda coord: coord_aero),
        }

        resultado = self.manipulador_modelos.ajustar_aerogeneradores(
            params, diccionario_mock)

        for aero_resultado, aero_esperado in zip(
            resultado.ParametrosConfiguracion.Aerogeneradores,
            self.json_esperado.ParametrosConfiguracion.Aerogeneradores,
        ):
            for espec_resultado, espec_esperado in zip(
                aero_resultado.EspecificacionesEspacialesAerogeneradores,
                aero_esperado.EspecificacionesEspacialesAerogeneradores,
            ):
                self.assertEqual(
                    espec_resultado.MedicionAsociada.Value,
                    espec_esperado.MedicionAsociada.Value,
                )

        assert isinstance(resultado, JsonModelEolica)


    def test_ajustar_aerogeneradores_distancia_no_valida(self):
        with open("./tests/data/test_json_data_eolica.json") as f:
            json_data = json.load(f)
        params = JsonModelEolica(**json_data)

        torres = {
            "torre_1": MagicMock(),
            "torre_2": MagicMock(),
        }

        for torre in torres.values():

            torre.obtener_distancia.return_value = 100

            torre.comparar_distancia.return_value = False

        with patch("utils.manipulador_modelos.np.inf", return_value=1000):
            result = self.manipulador_modelos.ajustar_aerogeneradores(
                params, torres)

        for torre in torres.values():
            torre.obtener_distancia.assert_called()

    
