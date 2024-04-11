import unittest
from unittest.mock import patch
from utils.consumidor import ConsumirApiEstado


class TestConsumirApiEstado(unittest.TestCase):
    
    @patch("requests.post")
    def test_consumir_api_estado(self, mock_post):
        proceso = "TestProceso"
        conexion_id = "TestConexionID"
        pasos_totales = 5

        consumidor_api = ConsumirApiEstado(proceso, conexion_id, pasos_totales)
        mensaje = "TestMensaje"
        consumidor_api.consumir_api_estado(mensaje, exitoso=True)

        mock_post.assert_called_once_with(
            consumidor_api.url,
            json={
                "proceso": proceso,
                "mensaje": f'{{"nombreTarea": "{mensaje}", "total": {pasos_totales}, "progreso": 1}}',
                "conexionId": conexion_id,
                "exitoso": True,
                "tipoMensaje": 1
            },
            verify=False
        )

    def test_validar_progreso_reset(self):
        proceso = "TestProceso"
        conexion_id = "TestConexionID"
        pasos_totales = 3

        consumidor_api = ConsumirApiEstado(proceso, conexion_id, pasos_totales)

        # Se realiza tres llamadas para alcanzar el número total de pasos
        for _ in range(pasos_totales):
            consumidor_api._validar_progreso()

        # En la cuarta llamada, el progreso debería haberse restablecido a cero
        progreso = consumidor_api._validar_progreso()
        self.assertEqual(progreso, 1)