import os

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.servicebus import ServiceBusClient, ServiceBusReceiveMode

from utils import manejador_mensajes


class ManejadorServiceBus:
    def __init__(self):
        self.QUEUE_NAME = "fernc-notificacion-python-queue"
        self.environment = os.environ.get("ENVIRONMENT")

    def consumir_service_bus(self):
        with (ServiceBusClient.from_connection_string(
                self.__obtener_sb_connection_string()
            )
            if self.environment == "dev"
            else ServiceBusClient(
                self.__obtener_sb_nombre_espacio(DefaultAzureCredential()),
                DefaultAzureCredential(),
            )
        ) as cliente:
            while True:
                print("Escuchando...")
                self.__consumir_cola(cliente)

    def __obtener_sb_connection_string(self) -> str:
        return os.environ.get("CONNECTION_STRING_SB_FERNC")

    def __obtener_sb_nombre_espacio(self, credential: DefaultAzureCredential) -> str:
        keyvault_uri = os.environ.get("KEYVAULT_URI")
        secretos = SecretClient(vault_url=keyvault_uri, credential=credential)
        nombre_espacio = secretos.get_secret(
            "xm-fernc-serviceBus-ConectionString"
        ).value
        return nombre_espacio

    def __consumir_cola(self, cliente: ServiceBusClient):
        with cliente.get_queue_receiver(
            self.QUEUE_NAME, receive_mode=ServiceBusReceiveMode.RECEIVE_AND_DELETE
        ) as receptor:
            array_mensajes_recibidos = receptor.receive_messages(max_message_count=1)  # intenta recibir un solo mensaje dentro de 10 segundos
            if array_mensajes_recibidos:
                manejador_mensajes.procesar_mensaje(
                    str(array_mensajes_recibidos[0])
                )
