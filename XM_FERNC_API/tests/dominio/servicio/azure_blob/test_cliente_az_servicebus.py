import unittest
from unittest.mock import patch, MagicMock
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage
import os

from dominio.servicio.azure.cliente_az_servicebus import ClienteServiceBusTransversal  # Reemplaza con la ruta correcta

class TestClienteServiceBusTransversal(unittest.TestCase):
    
    @patch('dominio.servicio.azure.cliente_az_servicebus.DefaultAzureCredential')
    @patch('dominio.servicio.azure.cliente_az_servicebus.ServiceBusClient')
    @patch('dominio.servicio.azure.cliente_az_servicebus.ClienteServiceBusTransversal._ClienteServiceBusTransversal__obtener_sb_connection_string')
    def test_init_dev_environment(self, mock_obtener_connection_string, mock_service_bus_client, mock_default_credential):
        # Mocking el valor de retorno del método privado
        mock_obtener_connection_string.return_value = 'mocked_connection_string'
        
        # Instancia de la clase en ambiente "dev"
        cliente = ClienteServiceBusTransversal(environment='dev')
        
        self.assertEqual(cliente.environment, 'dev')
        self.assertEqual(cliente.cadena_conexion, 'mocked_connection_string')
        self.assertEqual(cliente.nombre_topico, 'cal_modelos_fernc-notificacionresultado-topico')

    """
    @patch('XM_FERNC_API.dominio.servicio.azure.cliente_az_servicebus.ClienteServiceBusTransversal._ClienteServiceBusTransversal__obtener_sb_nombre_espacio')
    @patch('XM_FERNC_API.dominio.servicio.azure.cliente_az_servicebus.SecretClient')
    @patch('XM_FERNC_API.dominio.servicio.azure.cliente_az_servicebus.DefaultAzureCredential')
    @patch('XM_FERNC_API.dominio.servicio.azure.cliente_az_servicebus.ServiceBusClient')
    def test_init_non_dev_environment(self, mock_service_bus_client, mock_default_credential, mock_secret_client, mock_obtener_sb_nombre_espacio):
        # Mock de secretos
        mock_secret_client.return_value.get_secret.side_effect = [
            MagicMock(value='mocked_namespace'),
            MagicMock(value='mocked_topic')
        ]
        
        mock_obtener_sb_nombre_espacio.return_value = ('mocked_namespace', 'mocked_topic')

        # Instancia de la clase en ambiente no "dev"
        cliente = ClienteServiceBusTransversal(environment='prod')
        
        self.assertEqual(cliente.namespace, 'mocked_namespace')
        self.assertEqual(cliente.nombre_topico, 'mocked_topic')
        #self.assertIsInstance(cliente.credencial, DefaultAzureCredential)

    """
    @patch('dominio.servicio.azure.cliente_az_servicebus.ServiceBusClient')
    @patch('dominio.servicio.azure.cliente_az_servicebus.ServiceBusMessage')
    def test_enviar_mensaje_a_servicebus_dev(self, mock_service_bus_message, mock_service_bus_client):
        # Preparación de mocks
        mock_service_bus_client.from_connection_string.return_value = MagicMock()
        cliente = ClienteServiceBusTransversal(environment='dev')
        cliente.cadena_conexion = 'mocked_connection_string'
        
        # Llamada a la función
        cliente.enviar_mensaje_a_servicebus(cuerpo_mensaje='mensaje', id_aplicacion='1234')
        
        # Aserciones
        #mock_service_bus_client.from_connection_string.assert_called_once_with('mocked_connection_string')
        #mock_service_bus_client().get_topic_sender.assert_called_once_with(topic_name=cliente.nombre_topico)
        mock_service_bus_message.assert_called_once_with('mensaje')
    
    @patch('dominio.servicio.azure.cliente_az_servicebus.ServiceBusClient')
    @patch('dominio.servicio.azure.cliente_az_servicebus.ServiceBusMessage')
    def test_enviar_mensaje_a_servicebus_non_dev(self, mock_service_bus_message, mock_service_bus_client):
        # Preparación de mocks
        mock_service_bus_client.return_value = MagicMock()
        cliente = ClienteServiceBusTransversal(environment='dev')
        cliente.namespace = 'mocked_namespace'
        cliente.credencial = MagicMock()
        
        # Llamada a la función
        cliente.enviar_mensaje_a_servicebus(cuerpo_mensaje='mensaje', id_aplicacion='1234')
        
        # Aserciones
        #mock_service_bus_client().get_topic_sender.assert_called_once_with(topic_name=cliente.nombre_topico)
        mock_service_bus_message.assert_called_once_with('mensaje')

    @patch('dominio.servicio.azure.cliente_az_servicebus.os.environ.get')
    @patch('dominio.servicio.azure.cliente_az_servicebus.ServiceBusClient')
    def test_enviar_mensaje_excepcion(self, mock_service_bus_client, mock_os_environ):
        mock_os_environ.return_value = 'dev'
        mock_params = MagicMock(IdTransaccion='tx123', IdAplicacion='app123')
        
        # Instancia la clase en ambiente dev
        cliente = ClienteServiceBusTransversal(environment='dev')
        cliente.cadena_conexion = 'mocked_connection_string'
        
        # Llamada a la función
        cliente.enviar_mensaje_excepcion(params=mock_params, mensaje_excepcion='error_message')
        
        # Aserciones
        #mock_service_bus_client.from_connection_string.assert_called_once_with('mocked_connection_string')
