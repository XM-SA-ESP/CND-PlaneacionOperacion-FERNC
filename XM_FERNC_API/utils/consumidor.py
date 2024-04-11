import os
import requests


class ConsumirApiEstado():
    """
    Clase usada para hacer una request y enviar informacion de un determinado proceso y su progreso
    """
    def __init__(self, proceso: str, conexion_id: str, pasos_totales: int) -> None:
        """
        Contructor de la clase ConsumirApiEstado
        Parametros:
            proceso (str): nombre del proceso del cual se enviara informacion en la request
            conexion_id (str): id de la conexion enviada en el json de la request
            pasos_totales (int): numero de pasos que tiene el proceso del cual se hara notificaion
            url (str): url a la cual se hara la peticion o request/post
            progreso (int): paso actual en el que se encuentra el proceso, se inicia en cero (0)
        """
        self.proceso = proceso
        self.conexion_id = conexion_id
        self.pasos_totales = pasos_totales
        url_net = os.environ.get("URL_NET")
        self.url = f"{url_net}/api/Communication/EnviarMensajePersonalizado"
        self._progreso = 0

    def _validar_progreso(self) -> str:
        """
        Esta funcion se encarga de aumentar en 1 el progreso por cada peticion que se valla hacer.
        en caso de que se alcance el el numero de pasos totales se reestablece en cero _progreso en caso
        de que se siga usando la misma intancia.

        Retorna:
            paso (int): Valor del paso o numero del progreso actual
        """
        self._progreso += 1
        paso = self._progreso
        if self._progreso == self.pasos_totales:
            self._progreso = 0
        return paso
        
    def enviar_resultados(self, mensaje: str, exitoso: bool = False) -> None:
        """
        Esta funcion envia el resultado el FE
        """        
        verificar = False
        if self.conexion_id is not None and self.conexion_id != "":
            requests.post(
                self.url,
                json={
                    "proceso": self.proceso,
                    "mensaje": mensaje,
                    "conexionId": self.conexion_id,
                    "exitoso": exitoso,
                    "tipoMensaje": 1
                },
                verify=verificar
            )

    def consumir_api_estado(self, mensaje: str, exitoso: bool = False) -> None:
        """
        Esta funcion se encarga de hacer una peticion post para enviar informacion del proceso.
        Si self.conexion_id tiene información se consume el endpoint para notificar al FE, que el proceso avanzo.
        """        
        verificar = False
        if self.conexion_id is not None and self.conexion_id != "":
            progreso = self._validar_progreso()            
            requests.post(
                self.url,
                json={
                    "proceso": self.proceso,
                    "mensaje": f'{{"nombreTarea": "{mensaje}", "total": {self.pasos_totales}, "progreso": {progreso}}}',
                    "conexionId": self.conexion_id,
                    "exitoso": exitoso,
                    "tipoMensaje": 1
                },
                verify=verificar
            )
