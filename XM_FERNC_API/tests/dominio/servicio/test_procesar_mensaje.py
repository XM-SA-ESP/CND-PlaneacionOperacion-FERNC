import json
import unittest

from unittest import mock
from ctypes import ArgumentError
from infraestructura.models.respuesta import Respuesta, Resultado

from dominio.servicio.procesar_mensaje import (
    procesar_mensaje,
    enviar_resultados,
    enviar_mensaje_sb_transversal,
    pordefento,
)
from infraestructura.models.solar.parametros import JsonModelSolar
from infraestructura.models.mensaje_azure import RecibirMensajeAzure


class TestProcesarMensaje(unittest.TestCase):
    def setUp(self) -> None:
        self.json_string = f'''
            {{
                "ArchivoResultados": "1234",
                "ArchivosResultados": ["3, 4"],
                "DatosEnficc": [1, 2],
                "DatosEda": [1, 2],
                "IdTransaccion": "8912u3j",
                "CalculoCorrecto": true
            }}
        '''
        with open("./tests/data/test_json_data.json") as f:
            json_data = json.load(f)
        self.params = JsonModelSolar(**json_data)

    @mock.patch("dominio.servicio.procesar_mensaje.enviar_resultados")
    @mock.patch("dominio.servicio.procesar_mensaje.switch_dict")
    @mock.patch("infraestructura.calculos.solar.calculo_solar.realizar_calculo_solares")
    @mock.patch("infraestructura.models.mensaje_azure.RecibirMensajeAzure.model_validate_json")
    def test_procesar_mensaje(
        self, mock_validate_json, mock_realizar_calculo_solar, mock_switch_get, mock_enviar_resultados
    ):
        mensaje_json = RecibirMensajeAzure(TipoMensaje=0, CuerpoMensaje=self.params)
        mock_validate_json.return_value = mensaje_json
        mock_realizar_calculo_solar.return_value = "test"
        mock_switch_get.return_value = mock.Mock()
        mock_enviar_resultados.return_value = None

        procesar_mensaje(mensaje_json)

        mock_validate_json.assert_called_once()
        mock_enviar_resultados.assert_called_once()

    @mock.patch("utils.consumidor.ConsumirApiEstado.enviar_resultados")
    @mock.patch("dominio.servicio.procesar_mensaje.enviar_mensaje_sb_transversal")
    def test_enviar_resultados(self, mock_enviar_mensaje_sb, mock_enviar_resultados):
        mock_resultado1 = Resultado(
            anio=2000,
            mes=1,
            valor=32,
        )
        mock_resultado2 = Resultado(
            anio=2000,
            mes=2,
            valor=42,
        )
        mock_respuesta = Respuesta(
            archivo_resultados="test",
            datos_enficc=[mock_resultado1, mock_resultado2],
            datos_eda=[mock_resultado1, mock_resultado2]
        )

        enviar_resultados(mock_respuesta, self.params)

        mock_enviar_resultados.assert_called_once()
        mock_enviar_mensaje_sb.assert_called_once()

    @mock.patch("dominio.servicio.azure.cliente_az_servicebus.ClienteServiceBusTransversal._ClienteServiceBusTransversal__obtener_sb_nombre_espacio")
    @mock.patch("dominio.servicio.azure.cliente_az_servicebus.ClienteServiceBusTransversal._ClienteServiceBusTransversal__obtener_sb_connection_string")
    @mock.patch("dominio.servicio.azure.cliente_az_servicebus.ClienteServiceBusTransversal.enviar_mensaje_a_servicebus")
    def test_enviar_excepcion_sb_transversal(
        self, mock_enviar_mensaje, mock_obtener_sb_connection_string, mock_obtener_sb_nombre
    ):
        """
        Prueba que la funcion fue llamada con los parametros esperados.
        """
        mock_obtener_sb_connection_string.return_value = "Test"
        mock_obtener_sb_nombre.return_value = ("test1", "test2")

        enviar_mensaje_sb_transversal(
            id_aplicacion=self.params.IdAplicacion, json_resultado=self.json_string
        )

        mock_enviar_mensaje.assert_called_once_with(
            id_aplicacion=self.params.IdAplicacion, cuerpo_mensaje=self.json_string
        )

    def test_tipo_mensaje_invalido(self):
        """
        Prueba si la función genera un error cuando se recibe un tipo de mensaje no válido.
        """
        tipo_mensaje = 2

        with self.assertRaises(ArgumentError) as error:
            pordefento(tipo_mensaje)

        self.assertEqual(
            str(error.exception),
            f"El valor en 'mensaje_recibido.TipoMensaje' es incorrecto:{tipo_mensaje}, valores permitidos 0: Solar | 1: Eolica"
        )
