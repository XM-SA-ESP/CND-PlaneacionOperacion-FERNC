from pydantic import BaseModel


class BaseParametrosTransversales(BaseModel):
    NombrePlanta: str
    Cen: float
    Ihf: float
    Ppi: float
    Kpc: float
    Kt: float
    Kin: float
    Latitud: float
    Longitud: float
    InformacionMedida: bool
