import json
import unittest

import pandas as pd

from unittest import mock

from infraestructura.calculos.eolica.calculo_eolica import (
    realizar_calculo_eolicas,
    enviar_excepcion_sb_transversal
)
from dominio.servicio.eolica.servicio_eolicas import ServicioEolicas
from infraestructura.models.eolica.parametros import JsonModelEolica
from utils.manipulador_excepciones import ManipuladorExcepciones


class TestCalculoEolica(unittest.TestCase):
    def setUp(self) -> None:
        with open("./tests/data/test_json_data_eolica.json") as f:
            json_data = json.load(f)
        self.params = JsonModelEolica(**json_data)
        self.servicio_eolica = ServicioEolicas()

    @mock.patch("XM_FERNC_API.dominio.servicio.eolica.servicio_eolicas.ServicioEolicas.ejecutar_calculos")
    def test_realizar_calculo_eolicas_parametros(self, mock_ejecutar_calculos):
        """
        Prueba que la funcion fue llamada con exito
        """
        mock_ejecutar_calculos.return_value = pd.DataFrame({"test": [1, 2, 3]})

        resultado = realizar_calculo_eolicas(self.params)

        mock_ejecutar_calculos.assert_called_once_with(self.params)

    @mock.patch("XM_FERNC_API.dominio.servicio.eolica.servicio_eolicas.ServicioEolicas.ejecutar_calculos")
    @mock.patch("XM_FERNC_API.infraestructura.calculos.eolica.calculo_eolica.enviar_excepcion_sb_transversal")
    @mock.patch("XM_FERNC_API.utils.consumidor.ConsumirApiEstado.enviar_resultados")
    def test_realizar_calculo_eolicas_retorna_excepcion(
        self, mock_enviar_resultados, mock_enviar_mensaje_sb, mock_ejecutar_calculos
    ):
        """
        Prueba que la funcion retorna un objeto ManipuladorExcepciones
        """
        mock_ejecutar_calculos.return_value = ManipuladorExcepciones(
            "Ocurrio error", mensaje_tarea="Tarea 1", mensaje_error="Error en calculo"
        )
        mock_enviar_mensaje_sb.return_value = None
        mock_enviar_resultados.return_value = None
        resultado = realizar_calculo_eolicas(self.params)

        assert isinstance(resultado, ManipuladorExcepciones) == True

    @mock.patch("XM_FERNC_API.dominio.servicio.azure.cliente_az_servicebus.ClienteServiceBusTransversal._ClienteServiceBusTransversal__obtener_sb_nombre_espacio")
    @mock.patch("XM_FERNC_API.dominio.servicio.azure.cliente_az_servicebus.ClienteServiceBusTransversal._ClienteServiceBusTransversal__obtener_sb_connection_string")
    @mock.patch("XM_FERNC_API.dominio.servicio.azure.cliente_az_servicebus.ClienteServiceBusTransversal.enviar_mensaje_excepcion")
    def test_enviar_excepcion_sb_transversal(self, mock_enviar_excepcion, mock_obtener_sb_connection_string, mock_obtener_sb_nombre):
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
