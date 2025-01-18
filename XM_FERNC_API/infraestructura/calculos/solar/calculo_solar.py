from datetime import datetime
import os

from XM_FERNC_API.dominio.servicio.azure.cliente_az_servicebus import ClienteServiceBusTransversal
from XM_FERNC_API.dominio.servicio.solar.servicio_solares import ServicioSolar
from XM_FERNC_API.infraestructura.models.solar.parametros import JsonModelSolar
from XM_FERNC_API.utils.consumidor import ConsumirApiEstado

from XM_FERNC_API.utils.manipulador_excepciones import ManipuladorExcepciones

def realizar_calculo_solares(params: JsonModelSolar):
    servicio = ServicioSolar()
    df = servicio.generar_dataframe(params.ArchivoSeries.Nombre)    
    respuesta = servicio.ejecutar_calculos(df, params)    

    if isinstance(respuesta, ManipuladorExcepciones):
        print(respuesta.obtener_error())
        mensaje_error = respuesta.obtener_mensaje_error()

        ws_estado_fe = ConsumirApiEstado(
            proceso="EstadoCalculo",
            conexion_id=params.IdConexionWs,
            pasos_totales=0
        )
        ws_estado_fe.enviar_resultados(
            mensaje=f'{{"detail": {{"nombreTarea": "{respuesta.obtener_mensaje_tarea()}", "mensajeError": "{mensaje_error}"}}}}',
            exitoso=False)
        
        enviar_excepcion_sb_transversal(params, mensaje_error)

        return None
    
    return respuesta

def enviar_excepcion_sb_transversal(params: JsonModelSolar, excepcion: str):
    '''
    Si llega IdAplicacion se envia mensaje a la integración por medio del service bus transversal   
    Asi como se notifica al FE tambien se debe notifiar a aplicaciones que use este metodo
    '''
    if params.IdAplicacion:
        servicebus_transversal = ClienteServiceBusTransversal(os.environ.get("ENVIRONMENT"))
        servicebus_transversal.enviar_mensaje_excepcion(params, excepcion)