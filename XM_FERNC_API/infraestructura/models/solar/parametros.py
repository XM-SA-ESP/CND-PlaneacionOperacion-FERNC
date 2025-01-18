from pydantic import BaseModel
from typing import List, Optional

from XM_FERNC_API.infraestructura.models.parametros_base import BaseParametrosTransversales


class Tecnologia(BaseModel):    
    Value: str


class Racking(BaseModel):    
    Value: str


class ParametrosInversor(BaseModel):
    ReferenciaInversor: str
    NInv: int
    PACnominal: float
    PDCnominal: float
    VDCnominal: float
    PDCarranque: float
    PACnocturnoW: float
    PowerAc:List[float]
    PowerDc: List[float]


class ParametrosModulo(BaseModel):
    ReferenciaModulo: str
    Tnoct: float
    Tecnologia: Tecnologia
    Ns: float
    Iscstc: float
    Vocstc: float
    Impstc: float
    Vmpstc: float
    AlphaSc: float
    BetaOc: float
    GammaPmp: float
    Pnominalstc: float
    Psi: float
    Bifacial: bool
    Bifacialidad: Optional[float]
    AltoFilaPaneles: Optional[float]
    AnchoFilaPaneles: Optional[float]


class CantidadPanelConectados(BaseModel):
    Id: int
    CantidadSerie: int
    CantidadParalero: int
    OAzimutal: float
    OElevacion: float
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
