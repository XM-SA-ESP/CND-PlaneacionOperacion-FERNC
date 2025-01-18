from pydantic import BaseModel

from XM_FERNC_API.infraestructura.models.solar.parametros import JsonModelSolar
from XM_FERNC_API.infraestructura.models.eolica.parametros import JsonModelEolica


class RecibirMensajeAzure(BaseModel):
    TipoMensaje: int
    CuerpoMensaje: JsonModelSolar | JsonModelEolica
