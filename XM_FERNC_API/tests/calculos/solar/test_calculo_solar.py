import json
import unittest

import pandas as pd

from unittest import mock

from infraestructura.calculos.solar.calculo_solar import (
    realizar_calculo_solares,
    enviar_excepcion_sb_transversal
)
from dominio.servicio.solar.servicio_solares import ServicioSolar
from infraestructura.models.solar.parametros import JsonModelSolar
from utils.manipulador_excepciones import ManipuladorExcepciones


class TestCalculoSolar(unittest.TestCase):
    def setUp(self) -> None:
        with open("./tests/data/test_json_data.json") as f:
            json_data = json.load(f)
        self.params = JsonModelSolar(**json_data)
        self.servicio_solar = ServicioSolar()

    @mock.patch("dominio.servicio.solar.servicio_solares.ServicioSolar.generar_dataframe")
    @mock.patch("dominio.servicio.solar.servicio_solares.ServicioSolar.ejecutar_calculos")
    def test_realizar_calculo_solares_parametros(self, mock_ejecutar_calculos, mock_generar_dataframe):
        """
        Prueba que la funcion fue llamada con exito
        """
        mock_generar_dataframe.return_value = pd.DataFrame({"test": [3, 4, 5]})
        mock_ejecutar_calculos.return_value = pd.DataFrame({"test": [1, 2, 3]})

        resultado = realizar_calculo_solares(self.params)

        mock_ejecutar_calculos.assert_called_once()

    @mock.patch("dominio.servicio.solar.servicio_solares.ServicioSolar.generar_dataframe")
    @mock.patch("dominio.servicio.solar.servicio_solares.ServicioSolar.ejecutar_calculos")
    @mock.patch("infraestructura.calculos.solar.calculo_solar.enviar_excepcion_sb_transversal")
    @mock.patch("utils.consumidor.ConsumirApiEstado.enviar_resultados")
    def test_realizar_calculo_eolicas_retorna_excepcion(
        self,
        mock_enviar_resultados,
        mock_enviar_mensaje_sb,
        mock_ejecutar_calculos,
        mock_generar_dataframe
    ):
        """
        Prueba que la funcion retorna un objeto ManipuladorExcepciones
        """
        mock_generar_dataframe.return_value = pd.DataFrame({"test": [1, 2, 3]})
        mock_ejecutar_calculos.return_value = ManipuladorExcepciones(
            "Ocurrio error", mensaje_tarea="Tarea 1", mensaje_error="Error en calculo"
        )
        mock_enviar_mensaje_sb.return_value = None
        mock_enviar_resultados.return_value = None
        resultado = realizar_calculo_solares(self.params)

        assert resultado == None

    @mock.patch("dominio.servicio.azure.cliente_az_servicebus.ClienteServiceBusTransversal._ClienteServiceBusTransversal__obtener_sb_nombre_espacio")
    @mock.patch("dominio.servicio.azure.cliente_az_servicebus.ClienteServiceBusTransversal._ClienteServiceBusTransversal__obtener_sb_connection_string")
    @mock.patch("dominio.servicio.azure.cliente_az_servicebus.ClienteServiceBusTransversal.enviar_mensaje_excepcion")
    def test_enviar_excepcion_sb_transversal(
        self, mock_enviar_excepcion, mock_obtener_sb_connection_string, mock_obtener_sb_nombre
    ):
        """
        Prueba que la funcion fue llamada con los parametros esperados.
        """
        excepcion = "This is a test exception"
        mock_obtener_sb_connection_string.return_value = "Test"
        mock_obtener_sb_nombre.return_value = ("test1", "test2")

        enviar_excepcion_sb_transversal(self.params, excepcion)

        # Assert that enviar_mensaje_excepcion is called on the mock object
        mock_enviar_excepcion.assert_called_once_with(
            self.params, excepcion
        )