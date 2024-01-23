from datetime import datetime
from fastapi import APIRouter, HTTPException

from dominio.servicio.solar.servicio_solares import ServicioSolar
from infraestructura.models.solar.parametros import JsonModelSolar

router_solar = APIRouter()

@router_solar.post("/realizar_calculo_solares")
async def realizar_calculo_solares(params: JsonModelSolar):
    servicio = ServicioSolar()
    now = datetime.now()
    print('iniciar calculo solar')
    print(now)

    df = servicio.generar_dataframe(params.ArchivoSeries.Nombre)

    if df.is_empty():
        raise HTTPException(
            status_code=404,
            detail="No se pudo procesar el archivo. Verifique que el nombre del archivo es el correcto o que el archivo existe en el blob storage",
        )

    response = servicio.ejecutar_calculos(df, params)

    if response is None:
        raise HTTPException(status_code=404, detail="Sin respuesta de la API")

    return response
