import unittest
from unittest.mock import Mock, patch
from infraestructura.models.eolica.parametros import JsonModelEolica
from utils.eolica.dataclasses_eolica import Aerogenerador
from utils.eolica.funciones_calculo_pcc import CalculoPcc

class TestCalculoPcc(unittest.TestCase):
    def setUp(self) -> None:
        self.calculo_pcc_instancia = CalculoPcc()

    def test_calculo_pcc_aerogenerador(self):
        params = Mock()
        params.ParametrosConfiguracion.ParametroConexion = [
            Mock(ConexionAerogenerador=[
                Mock(IdentificadorAerogenerador=1), 
                Mock(IdentificadorAerogenerador=2)
            ]),
            Mock(ConexionAerogenerador=[
                Mock(IdentificadorAerogenerador=2), 
                Mock(IdentificadorAerogenerador='pcc')
            ]),
        ]
        aerogeneradores = {
            1: Mock(id_aero='Aero1', latitud=0, longitud=0, elevacion=0, dist_pcc=None),
            2: Mock(id_aero='Aero2', latitud=1, longitud=1, elevacion=1, dist_pcc=None),
            'pcc': Mock(id_aero='Aero3', latitud=2, longitud=2, elevacion=2, dist_pcc=None),
        }

        resultado = self.calculo_pcc_instancia.calculo_pcc_aerogenerador(params, aerogeneradores)

        self.assertAlmostEqual(resultado[1].dist_pcc, 313.7821, places=4)
        self.assertAlmostEqual(resultado[2].dist_pcc, 156.8793, places=4)

    def test_obtener_distancia_geodesica_pcc_aero(self):
        dist_aerogeneradores = [100, 150, 200]

        resultado = self.calculo_pcc_instancia._CalculoPcc__obtener_distancia_geodesica_pcc_aero(dist_aerogeneradores)

        self.assertAlmostEqual(resultado, 450, places=4)

    def test_obtener_calculo_conexiones_pcc(self):
        conexiones = [(1, 2), (2, 3)]
        aerogeneradores = {
            1: Aerogenerador(id_aero='Aero1', id_torre='Torre1', modelo='Modelo1', latitud=0, longitud=0, elevacion=0, dist_pcc=None),
            2: Aerogenerador(id_aero='Aero2', id_torre='Torre2', modelo='Modelo2', latitud=1, longitud=1, elevacion=1, dist_pcc=None),
            3: Aerogenerador(id_aero='Aero3', id_torre='Torre3', modelo='Modelo3', latitud=2, longitud=2, elevacion=2, dist_pcc=None),
        }

        resultado = self.calculo_pcc_instancia._CalculoPcc__obtener_calculo_conexiones_pcc(conexiones, aerogeneradores)

        self.assertAlmostEqual(resultado[0], 156.9028, places=4)
        self.assertAlmostEqual(resultado[1], 156.8793, places=4)

    def test_agrupar_conexiones_pcc(self):
        params = Mock()
        params.ParametrosConfiguracion.ParametroConexion = [
            Mock(ConexionAerogenerador=[Mock(IdentificadorAerogenerador=1), Mock(IdentificadorAerogenerador=2)]),
            Mock(ConexionAerogenerador=[Mock(IdentificadorAerogenerador=2), Mock(IdentificadorAerogenerador=3)]),
        ]

        resultado = self.calculo_pcc_instancia._CalculoPcc__agrupar_conexiones_pcc(params)

        self.assertEqual(resultado, [[(1, 2), (2, 'pcc')], [(2, 3), (3, 'pcc')]])

    def test_calculo_distancia_geodesica(self):
        aero_1 = Aerogenerador(id_aero='Aero1', id_torre='Torre1', modelo='Modelo1', latitud=0, longitud=0, elevacion=0, dist_pcc=None)
        aero_2 = Aerogenerador(id_aero='Aero2', id_torre='Torre2', modelo='Modelo2', latitud=1, longitud=1, elevacion=1, dist_pcc=None)

        resultado = self.calculo_pcc_instancia._CalculoPcc__calculo_distancia_geodesica(aero_1, aero_2)

        self.assertAlmostEqual(resultado, 156.9028, places=4)