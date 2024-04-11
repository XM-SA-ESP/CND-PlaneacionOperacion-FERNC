from pydantic import BaseModel
from typing import List, Optional

from infraestructura.models.parametros_base import BaseParametrosTransversales


class Tecnologia(BaseModel):    
    Value: str


class Racking(BaseModel):    
    Value: str


class ParametrosInversor(BaseModel):
    ReferenciaInversor: str
    NInv: int
    PACnominal: int | float
    PDCnominal: int | float
    VDCnominal: int | float
    PDCarranque: int | float
    PACnocturnoW: int | float
    PowerAc:List[int | float]
    PowerDc: List[int | float]


class ParametrosModulo(BaseModel):
    ReferenciaModulo: str
    Tnoct: int | float
    Tecnologia: Tecnologia
    Ns: int | float
    Iscstc: int | float
    Vocstc: int | float
    Impstc: int | float
    Vmpstc: int | float
    AlphaSc: int | float
    BetaOc: int | float
    GammaPmp: int | float
    Pnominalstc: int | float
    Psi: int | float
    Bifacial: bool
    Bifacialidad: Optional[int | float]
    AltoFilaPaneles: Optional[int | float]
    AnchoFilaPaneles: Optional[int | float]


class CantidadPanelConectados(BaseModel):
    Id: int
    CantidadSerie: int
    CantidadParalero: int
    OAzimutal: int | float
    OElevacion: int | float
    Racking: Racking
    OMax: Optional[float]


class EstructuraYConfiguracion(BaseModel):
    NSubarrays: int
    EstructuraPlantaConSeguidores: bool
    CantidadPanelConectados: List[CantidadPanelConectados]


class GrupoInversores(BaseModel):
    ParametrosInversor: ParametrosInversor
    ParametrosModulo: ParametrosModulo
    EstructuraYConfiguracion: EstructuraYConfiguracion


class ParametrosTransversales(BaseParametrosTransversales):
    ZonaHoraria: str
    Altitud: float
    Albedo: float
    L: float


class ArchivoSeries(BaseModel):
    Nombre: str

class ParametrosConfiguracion(BaseModel):
    GrupoInversores: List[GrupoInversores]

class JsonModelSolar(BaseModel):
    IdConexionWs: str
    IdTransaccion: str | None
    IdAplicacion: str | None
    ParametrosTransversales: ParametrosTransversales
    ParametrosConfiguracion: ParametrosConfiguracion
    ArchivoSeries: ArchivoSeries
