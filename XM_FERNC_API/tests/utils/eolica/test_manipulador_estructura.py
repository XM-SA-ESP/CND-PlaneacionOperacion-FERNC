import json
from unittest import TestCase
from infraestructura.models.eolica.parametros import JsonModelEolica
from utils.eolica.dataclasses_eolica import Aerogenerador

from utils.eolica.manipulador_estructura import ManipuladorEstructura


class TestManipuladorEstructura(TestCase):

    def setUp(self) -> None:
        self.manipulador_instancia = ManipuladorEstructura()

        with open("./tests/data/test_json_data_eolica.json", "r") as file:
            test_json = json.load(file)

        self.params = JsonModelEolica(**test_json)

    def test_crear_dict_modelos_aerogeneradores(self):

        dict_mod, dict_aero = self.manipulador_instancia.crear_dict_modelos_aerogeneradores(
            self.params)

        self.assertIsInstance(dict_aero, dict)
        self.assertIsInstance(dict_mod, dict)

    def test_agregar_pcc(self):

        aerogeneradores = {"1": Aerogenerador(id_aero=1, id_torre='torre_1', latitud=12.29263, longitud=-71.22642, elevacion=1.0, modelo='Enercon E92/2.3MW', dist_pcc=None, df=None, f_ordenamiento=0)
                        }
        result = self.manipulador_instancia.agregar_pcc(self.params, aerogeneradores)

        self.assertIsInstance(result, dict)
        self.assertIn("pcc", result)
