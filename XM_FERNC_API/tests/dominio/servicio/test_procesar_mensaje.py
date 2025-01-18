import json
import unittest
import pytest

from unittest import mock
from unittest.mock import patch, ANY
from ctypes import ArgumentError

from dominio.servicio.procesar_mensaje import (
    enviar_mensaje_sb_transversal,
    pordefento,
    procesar_mensaje,
    enviar_resultados,
)
from infraestructura.models.solar.parametros import JsonModelSolar
from XM_FERNC_API.infraestructura.models.eolica.parametros import JsonModelEolica
from XM_FERNC_API.infraestructura.models.respuesta import Respuesta

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

    @mock.patch("XM_FERNC_API.dominio.servicio.azure.cliente_az_servicebus.ClienteServiceBusTransversal._ClienteServiceBusTransversal__obtener_sb_nombre_espacio")
    @mock.patch("XM_FERNC_API.dominio.servicio.azure.cliente_az_servicebus.ClienteServiceBusTransversal._ClienteServiceBusTransversal__obtener_sb_connection_string")
    @mock.patch("XM_FERNC_API.dominio.servicio.azure.cliente_az_servicebus.ClienteServiceBusTransversal.enviar_mensaje_a_servicebus")
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

@pytest.fixture
def mensaje_json():
    return {
        "IdConexionWs": "conexion_id",
        "IdTransaccion": "transaccion_id",
        "IdAplicacion": "aplicacion_id",
        # Agrega otros campos requeridos por JsonModelSolar o JsonModelEolica
    }

def test_procesar_mensaje_solar(mensaje_json):
    # Configura el tipo de mensaje para solar
    tipo_mensaje = False  # Representa tipo solar

    # Crea un resultado simulado
    resultado_simulado = Respuesta(
        archivo_resultados="resultados_solar.xlsx",
        datos_enficc=[],
        datos_eda=[]
    )

    # Usa patch para simular las funciones externas
    with patch('dominio.servicio.procesar_mensaje.realizar_calculo_solares', return_value=resultado_simulado) as mock_calculo:
        with patch('dominio.servicio.procesar_mensaje.enviar_resultados') as mock_enviar_resultados:
            # Moquea JsonModelSolar
            with patch('dominio.servicio.procesar_mensaje.JsonModelSolar', autospec=True) as mock_json_model:
                mock_json_model.return_value = mock.MagicMock()
                resultado = procesar_mensaje(mensaje_json, tipo_mensaje)
                
                # Asegúrate de que se llamó a la función correcta
                mock_calculo.assert_called_once()
                mock_enviar_resultados.assert_called_once_with(resultado_simulado, mock_json_model.return_value)

                # Verifica el resultado
                assert resultado == resultado_simulado

def test_procesar_mensaje_eolica(mensaje_json):
    # Configura el tipo de mensaje para eólica
    tipo_mensaje = True  # Representa tipo eólico

    # Crea un resultado simulado
    resultado_simulado = Respuesta(
        archivo_resultados="resultados_eolica.xlsx",
        datos_enficc=[],
        datos_eda=[]
    )

    # Usa patch para simular las funciones externas
    with patch('dominio.servicio.procesar_mensaje.realizar_calculo_eolicas', return_value=resultado_simulado) as mock_calculo:
        with patch('dominio.servicio.procesar_mensaje.enviar_resultados') as mock_enviar_resultados:
            # Moquea JsonModelEolica
            with patch('dominio.servicio.procesar_mensaje.JsonModelEolica', autospec=True) as mock_json_model:
                mock_json_model.return_value = mock.MagicMock()
                resultado = procesar_mensaje(mensaje_json, tipo_mensaje)

                # Asegúrate de que se llamó a la función correcta
                mock_calculo.assert_called_once()
                mock_enviar_resultados.assert_called_once_with(resultado_simulado, mock_json_model.return_value)

                # Verifica el resultado
                assert resultado == resultado_simulado

# def test_enviar_resultados():
#     # Crear un mock para el resultado
#     mock_resultado = mock.MagicMock()
    
#     # Definir los atributos que tu mock debe tener
#     mock_resultado.archivo_resultados = "resultado.xlsx"
#     mock_resultado.DatosEnficc = [
#         {'anio': 2024, 'mes': 1, 'valor': 100},
#         {'anio': 2024, 'mes': 2, 'valor': 200}
#     ]
#     mock_resultado.DatosEda = [
#         {'anio': 2024, 'mes': 1, 'valor': 300},
#         {'anio': 2024, 'mes': 2, 'valor': None}  # Para probar el caso de None
#     ]

#     # Crear un mock para el JsonModelSolar o JsonModelEolica
#     mock_parametros = mock.MagicMock()
#     mock_parametros.IdConexionWs = "12345"
#     mock_parametros.IdTransaccion = "abcde"
#     mock_parametros.IdAplicacion = "mi_aplicacion"

#     # Mock para ConsumirApiEstado
#     with patch('XM_FERNC_API.dominio.servicio.procesar_mensaje.ConsumirApiEstado__enviar_resultados') as mock_api_estado, \
#         patch('XM_FERNC_API.dominio.servicio.procesar_mensaje.enviar_mensaje_sb_transversal') as mock_enviar_mensaje_sb_transversal:
#         mock_api_estado.return_value = mock.MagicMock()
#         mock_enviar_mensaje_sb_transversal = mock.MagicMock()
        
#         # Llamar a la función enviar_resultados
#         enviar_resultados(mock_resultado, mock_parametros)

#         # Verificar que el método se haya llamado correctamente
#         mock_api_estado.assert_called_once_with(proceso="CalculandoproduccionEnergetica", conexion_id=mock_parametros.IdConexionWs, pasos_totales=0)

#         # Verificar que los resultados se envían correctamente
#         expected_json = {
#             "ArchivoResultados": "resultado.xlsx",
#             "ArchivosResultados": ["resultado.xlsx"],
#             "DatosEnficc": [
#                 {"Anio": 2024, "Mes": 1, "Valor": 100},
#                 {"Anio": 2024, "Mes": 2, "Valor": 200}
#             ],
#             "DatosEda": [
#                 {"Anio": 2024, "Mes": 1, "Valor": "300"},
#                 {"Anio": 2024, "Mes": 2, "Valor": "N/A"}
#             ],
#             "IdTransaccion": mock_parametros.IdTransaccion,
#             "CalculoCorrecto": True
#         }

#         # Comprobar el formato del mensaje JSON
#         mock_api_estado.return_value.enviar_resultados.assert_called_once()
#         args, kwargs = mock_api_estado.return_value.enviar_resultados.call_args[0]
#         assert json.loads(args[0]) == expected_json