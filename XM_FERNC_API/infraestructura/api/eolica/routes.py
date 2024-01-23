from fastapi import APIRouter, HTTPException

from dominio.servicio.eolica.servicio_eolicas import ServicioEolicas
from infraestructura.models.eolica.parametros import JsonModelEolica


router_eolica = APIRouter()

@router_eolica.post("/realizar_calculo_eolicas")
async def realizar_calculo_eolicas(params: JsonModelEolica):
    """
    Petición para iniciar el proceso de calculos con todo lo relacionado a plantas eólicas.

    Params:
        -params: Modelo que representa el objeto completo requerido para calculos de las plantas eólicas generado por la aplicación.
        
    Retorna:
        response: Objeto resultando del llamada del método 'ejecutar_calculos' del servicio de eólicas.
    """
    servicio = ServicioEolicas()

    response = servicio.ejecutar_calculos(params)

    if response is None:
        raise HTTPException(status_code=404, detail="Sin respuesta de la API")

    return response
