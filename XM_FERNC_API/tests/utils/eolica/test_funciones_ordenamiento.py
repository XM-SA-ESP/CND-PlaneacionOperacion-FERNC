import unittest

import pandas as pd
from infraestructura.models.eolica.parametros import ConfiguracionAnemometro
from utils.eolica.dataclasses_eolica import Aerogenerador, Pcc, Torre

from utils.eolica.funciones_ordenamiento import Ordenamiento


class TestFuncionesOrdenamiento(unittest.TestCase):

    def setUp(self) -> None:

        self.ordenamiento_instancia = Ordenamiento()

    def test_obtener_ordenamiento_con_torres(self):

        df_aero_mock_1 = pd.DataFrame(
            {
                "DireccionViento": [125.5, 135.0, 140.0, 130.2, ]
            }, index=["2008-01-01", "2008-02-01", "2008-03-01", "2008-04-01"]
        )

        aerogeneradores = {1: Aerogenerador(id_aero=1, id_torre='torre_1', latitud=12.29263, longitud=-71.22642, elevacion=1.0, modelo='Enercon E92/2.3MW', dist_pcc=None, df=df_aero_mock_1, f_ordenamiento=0),
                           2: Aerogenerador(id_aero=1, id_torre='torre_1', latitud=12.29263, longitud=-71.22642, elevacion=1.0, modelo='Enercon E92/2.3MW', dist_pcc=None, df=df_aero_mock_1, f_ordenamiento=0)
                           }

        combinaciones_aero = [(1, 2)]

        fecha = "2008-01-01"

        lista_ordenamiento = self.ordenamiento_instancia.obtener_ordenamiento(
            aerogeneradores, combinaciones_aero, fecha)

        self.assertIsInstance(next(lista_ordenamiento), list)

    def test_crear_combinaciones_aeros(self):

        aerogeneradores = {1: Aerogenerador(id_aero=1, id_torre='torre_1', latitud=12.29263, longitud=-71.22642, elevacion=1.0, modelo='Enercon E92/2.3MW', dist_pcc=None, df=None, f_ordenamiento=0),
                           2: Aerogenerador(id_aero=1, id_torre='torre_1', latitud=12.29263, longitud=-71.22642, elevacion=1.0, modelo='Enercon E92/2.3MW', dist_pcc=None, df=None, f_ordenamiento=0)
                           }
        aerogeneradores["pcc"] = Pcc(
            latitud=12.23987, longitud=-71.25036, elevacion=32.0, voltaje=36.0)

        aerogeneradores, combinaciones_aero = self.ordenamiento_instancia.crear_combinaciones_aeros(
            aerogeneradores)

        self.assertIsInstance(aerogeneradores, dict)
        self.assertIsInstance(combinaciones_aero, list)

    def test_ordenar_lista(self):
        aerogeneradores = {1: Aerogenerador(id_aero=1, id_torre='torre_1', latitud=12.29263, longitud=-71.22642, elevacion=1.0, modelo='Enercon E92/2.3MW', dist_pcc=None, df=None, f_ordenamiento=0),
                           2: Aerogenerador(id_aero=1, id_torre='torre_1', latitud=12.29263, longitud=-71.22642, elevacion=1.0, modelo='Enercon E92/2.3MW', dist_pcc=None, df=None, f_ordenamiento=0)
                           }

        result = self.ordenamiento_instancia._Ordenamiento__ordenar_lista(
            aerogeneradores)

        self.assertIsInstance(result, list)
