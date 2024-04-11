import unittest

from unittest import mock
from contextlib import suppress

from utils.manejador_service_bus import ManejadorServiceBus


call_count = 0


def mock_consumir_cola(cliente):
    global call_count
    call_count += 1
    if call_count >= 1:
        raise StopIteration  # Detener loop


class TestManejadorServiceBus(unittest.TestCase):
    def setUp(self) -> None:
        self.manejador_sb_instancia = ManejadorServiceBus()

    
    """
    @mock.patch("azure.servicebus.ServiceBusClient.from_connection_string")
    @mock.patch("utils.manejador_service_bus.ManejadorServiceBus._ManejadorServiceBus__obtener_sb_nombre_espacio")
    @mock.patch("utils.manejador_service_bus.ManejadorServiceBus._ManejadorServiceBus__consumir_cola", side_effect=mock_consumir_cola)
    @mock.patch("utils.manejador_service_bus.ManejadorServiceBus._ManejadorServiceBus__obtener_sb_connection_string")
    def test_consumir_service_bus(self, mock_obtener_sb_nombre, mock_connection_string, mock_consumir_cola, mock_from_connection_string):
        mock_from_connection_string.return_value = mock.Mock()

        with suppress(StopIteration):  # Se suprime el error creado para detener el loop
            self.manejador_sb_instancia.consumir_service_bus()

        mock_consumir_cola.assert_called_once()
        mock_connection_string.assert_called_once()
        assert StopIteration
    """
    
    @mock.patch("os.environ.get")
    def test_obtener_sb_connection_string(self, mock_environ):
        mock_environ.return_value = "test_env"

        self.manejador_sb_instancia._ManejadorServiceBus__obtener_sb_connection_string()

        mock_environ.assert_called_once()
