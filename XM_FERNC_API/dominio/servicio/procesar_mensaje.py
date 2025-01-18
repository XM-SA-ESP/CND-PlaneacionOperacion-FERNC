from ctypes import ArgumentError
import gc
import os
from XM_FERNC_API.dominio.servicio.azure.cliente_az_servicebus import ClienteServiceBusTransversal
from XM_FERNC_API.infraestructura.models.eolica.parametros import JsonModelEolica
from XM_FERNC_API.infraestructura.models.solar.parametros import JsonModelSolar
from XM_FERNC_API.infraestructura.calculos.eolica.calculo_eolica import realizar_calculo_eolicas
from XM_FERNC_API.infraestructura.calculos.solar.calculo_solar import realizar_calculo_solares
from XM_FERNC_API.infraestructura.models.mensaje_azure import RecibirMensajeAzure
from XM_FERNC_API.infraestructura.models.respuesta import Respuesta
from XM_FERNC_API.utils.consumidor import ConsumirApiEstado

#De acuerdo al tipo de mensaje se llama un metodo o el otro
switch_dict = {
    0: lambda param: realizar_calculo_solares(param),
    1: lambda param: realizar_calculo_eolicas(param),
}

def procesar_mensaje(mensaje_json, tipo_mensaje):
    mensaje_recibido = mensaje_json#RecibirMensajeAzure.model_validate_json(mensaje_json, strict=False)

    if tipo_mensaje:
        parametros = JsonModelEolica(**mensaje_recibido)
        
    else:
        parametros = JsonModelSolar(**mensaje_recibido)
        

    funcion_seleccionada = switch_dict.get(tipo_mensaje, lambda param: pordefento(param))
    resultado = funcion_seleccionada(parametros)
    enviar_resultados(resultado, parametros) #Enviar información al FE/Integración

    print("Proceso finalizado.")
    return resultado


def enviar_resultados(resultado: Respuesta, parametros: JsonModelSolar| JsonModelEolica):
    '''
    Se envia los resultados al FE de Modelos FERNC y tambien a cualquier otro sistema que este invocando el endpoint de iniciar calculo en este caso SUICC
    '''
    if resultado:
        ws_estado_fe = ConsumirApiEstado(
            proceso="CalculandoproduccionEnergetica", 
            conexion_id=parametros.IdConexionWs,
            pasos_totales=0
        )
        datos_enficc_str = ', '.join([f'{{"Anio": {d.anio}, "Mes": {d.mes}, "Valor": {d.valor}}}' for d in resultado.datos_enficc])
        datos_eda_str = ', '.join([f'{{"Anio": {d.anio}, "Mes": {d.mes}, "Valor": "{d.valor if d.valor is not None else "N/A"}"}}' for d in resultado.datos_eda])

        json_string = f'''
            {{
                "ArchivoResultados": "{resultado.archivo_resultados}", 
                "ArchivosResultados": ["{resultado.archivo_resultados}"],
                "DatosEnficc": [{datos_enficc_str}], 
                "DatosEda": [{datos_eda_str}],
                "IdTransaccion": "{parametros.IdTransaccion}",
                "CalculoCorrecto": true
            }}
        '''
        #Enviar resultados al FE
        ws_estado_fe.enviar_resultados(mensaje=json_string, exitoso=True)
        #Enviar resultados al service bus transversal | SUICC
        enviar_mensaje_sb_transversal(parametros.IdAplicacion, json_string)

def enviar_mensaje_sb_transversal(id_aplicacion: str, json_resultado: str):
   if id_aplicacion:
       servicebus_transversal = ClienteServiceBusTransversal(os.environ.get("ENVIRONMENT"))
       servicebus_transversal.enviar_mensaje_a_servicebus(cuerpo_mensaje=json_resultado, id_aplicacion=id_aplicacion)
    
def pordefento(tipo_mensaje: int):
    """
    Metodo usado para generar un error en caso de que no se reconozca el tipo de mensaje
    Params:
        -tipo_mensaje: el tipo de mensaje recibido     
    """
    raise ArgumentError(f"El valor en 'mensaje_recibido.TipoMensaje' es incorrecto:{tipo_mensaje}, valores permitidos 0: Solar | 1: Eolica")    
