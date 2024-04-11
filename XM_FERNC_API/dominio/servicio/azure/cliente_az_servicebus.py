import os
from azure.servicebus import ServiceBusClient
from azure.servicebus import ServiceBusMessage
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from infraestructura.models.eolica.parametros import JsonModelEolica
from infraestructura.models.solar.parametros import JsonModelSolar


class ClienteServiceBusTransversal:
    def __init__(self, environment):
        self.environment = environment
        NOMBRE_TOPIC = "cal_modelos_fernc-notificacionresultado-topico"  # NOMBRE DEL TOPIC EN AMBIENTE DESARROLLO
        if self.environment == "dev":
            self.cadena_conexion = self.__obtener_sb_connection_string()
            self.nombre_topico = NOMBRE_TOPIC
        else:
            credencial = DefaultAzureCredential()
            self.credencial = credencial
            self.namespace, self.nombre_topico = self.__obtener_sb_nombre_espacio(
                credencial
            )

    def enviar_mensaje_a_servicebus(self, cuerpo_mensaje: str, id_aplicacion: str):
        with (
            ServiceBusClient.from_connection_string(self.cadena_conexion)
            if self.environment == "dev"
            else ServiceBusClient(self.namespace, self.credencial)
        ) as cliente_servicebus:
            self.__enviar_mensaje(cliente_servicebus, cuerpo_mensaje, id_aplicacion)

    def __enviar_mensaje(
        self, cliente_servicebus: ServiceBusClient, cuerpo_mensaje, id_aplicacion
    ) -> None:
        """
        Enviar mensaje: la propiedad message_id llega al service bus y se filtra a la suscripción exacta.
        con este campo se asegura que la aplicación que esta suscrita a una suscripción reciba el mensaje.
        """
        sender = cliente_servicebus.get_topic_sender(topic_name=self.nombre_topico)
        mensaje = ServiceBusMessage(cuerpo_mensaje)
        mensaje.message_id = id_aplicacion
        sender.send_messages(mensaje)

    def enviar_mensaje_excepcion(
        self, params: JsonModelSolar | JsonModelEolica, mensaje_excepcion: str
    ) -> None:
        """
        Si llega IdAplicacion se envia mensaje a la integración por medio del service bus transversal
        Asi como se notifica al FE tambien se debe notifiar a aplicaciones que use este metodo
        """
        servicebus_transversal = ClienteServiceBusTransversal(
            os.environ.get("ENVIRONMENT")
        )
        json_string = f"""
            {{
                "ArchivoResultados": "", 
                "ArchivosResultados": [],
                "DatosEnficc": [], 
                "DatosEda": [],
                "IdTransaccion": "{params.IdTransaccion}",
                "CalculoCorrecto": false,
                "ExcepcionPython": "{mensaje_excepcion}"
            }}
        """
        servicebus_transversal.enviar_mensaje(
            cuerpo_mensaje=json_string, id_aplicacion=params.IdAplicacion
        )

    def __obtener_sb_connection_string(self) -> str:
        """
        Obtiene la cadena de conexión del service bus donde esta el topic para instragraciones
        """
        return os.environ.get("CONNECTION_STRING_SB_TRANSVERSAL")

    def __obtener_sb_nombre_espacio(self, credencial: DefaultAzureCredential) -> tuple:
        """
        Metodo usado para obtener namespace de servicebus transversal a donde se envian mensaje para la integración con otros sistemas (SUICC)
        """
        keyvault_uri = os.environ.get("KEYVAULT_URI")
        secretos = SecretClient(vault_url=keyvault_uri, credential=credencial)
        nombre_espacio = secretos.get_secret(
            "xm-fernc-serviceBus-transversal-url-integracion"
        ).value
        nombre_topico = secretos.get_secret(
            "xm-fernc-serviceBus-transversal-nombretopic-integracion"
        ).value
        return nombre_espacio, nombre_topico
