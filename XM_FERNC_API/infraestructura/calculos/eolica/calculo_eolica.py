import os
from XM_FERNC_API.utils.consumidor import ConsumirApiEstado
from XM_FERNC_API.dominio.servicio.eolica.servicio_eolicas import ServicioEolicas
from XM_FERNC_API.dominio.servicio.azure.cliente_az_servicebus import ClienteServiceBusTransversal
from XM_FERNC_API.infraestructura.models.eolica.parametros import JsonModelEolica
from XM_FERNC_API.utils.manipulador_excepciones import ManipuladorExcepciones

def realizar_calculo_eolicas(params: JsonModelEolica):
    """
    Petición para iniciar el proceso de calculos con todo lo relacionado a plantas eólicas.

    Params:
        -params: Modelo que representa el objeto completo requerido para calculos de las plantas eólicas generado por la aplicación.

    Retorna:
        response: Objeto resultando del llamada del método 'ejecutar_calculos' del servicio de eólicas.
    """
    servicio = ServicioEolicas()
    resultado = servicio.ejecutar_calculos(params)

    if isinstance(resultado, ManipuladorExcepciones):
        print(resultado.obtener_error())
        mensaje_error = resultado.obtener_mensaje_error()
        
        ws_estado_fe = ConsumirApiEstado(
            proceso="EstadoCalculo",
            conexion_id=params.IdConexionWs,
            pasos_totales=0
        )
        ws_estado_fe.enviar_resultados(
            mensaje=f'{{"detail": {{"nombreTarea": "{resultado.obtener_mensaje_tarea()}", "mensajeError": "{mensaje_error}"}}}}',
            exitoso=False)
        
        enviar_excepcion_sb_transversal(params, mensaje_error)

        return None

    return resultado

def enviar_excepcion_sb_transversal(params: JsonModelEolica, excepcion: str):
    '''
    Si llega IdAplicacion se envia mensaje a la integración por medio del service bus transversal
    Asi como se notifica al FE tambien se debe notifiar a aplicaciones que use este metodo
    '''
    if params.IdAplicacion:
        servicebus_transversal = ClienteServiceBusTransversal(os.environ.get("ENVIRONMENT"))
        servicebus_transversal.enviar_mensaje_excepcion(params, excepcion)