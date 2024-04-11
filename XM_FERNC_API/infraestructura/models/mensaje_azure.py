from pydantic import BaseModel

from infraestructura.models.solar.parametros import JsonModelSolar
from infraestructura.models.eolica.parametros import JsonModelEolica


class RecibirMensajeAzure(BaseModel):
    TipoMensaje: int
    CuerpoMensaje: JsonModelSolar | JsonModelEolica
