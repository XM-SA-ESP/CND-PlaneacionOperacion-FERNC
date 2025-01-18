from typing import List, Optional
from pydantic import BaseModel

from XM_FERNC_API.infraestructura.models.parametros_base import BaseParametrosTransversales


class CurvasDelFabricante(BaseModel):
    SerieVelocidad: float
    SeriePotencia: float
    SerieCoeficiente: float
    SerieVcthCorregida: float = 0


class MedicionAsociada(BaseModel):
    Value: str


class EspecificacionesEspacialesAerogeneradores(BaseModel):
    Aerogenerador: int
    Latitud: float
    Longitud: float
    Elevacion: float
    MedicionAsociada: MedicionAsociada


class Aerogeneradores(BaseModel):
    ModeloAerogenerador: str
    AlturaBuje: float
    DiametroRotor: float
    PotenciaNominal: float
    VelocidadNominal: float
    DensidadNominal: float
    VelocidadCorteInferior: float
    VelocidadCorteSuperior: float
    TemperaturaAmbienteMinima: float
    TemperaturaAmbienteMaxima: float
    CurvasDelFabricante: List[CurvasDelFabricante]
    CantidadAerogeneradores: int
    EspecificacionesEspacialesAerogeneradores: List[
        EspecificacionesEspacialesAerogeneradores
    ]


class ConfiguracionAnemometro(BaseModel):
    Anemometro: int
    AlturaAnemometro: float


class SistemasDeMedicion(BaseModel):
    IdentificadorTorre: str
    Latitud: float
    Longitud: float
    Elevacion: float
    RadioRepresentatividad: float
    CantidadAnemometro: int
    ConfiguracionAnemometro: List[ConfiguracionAnemometro]
    ArchivoSeriesRelacionado: str


class ConexionAerogenerador(BaseModel):
    OrdenConexion: int
    IdentificadorAerogenerador: int


class ParametroConexion(BaseModel):
    Conexion: int
    CantidadAerogeneradoresConexion: int
    Resistencia: float
    ConexionAerogenerador: List[ConexionAerogenerador]


class ParametrosTransversales(BaseParametrosTransversales):
    Offshore: bool
    Elevacion: float
    Voltaje: float


class ParametrosConfiguracion(BaseModel):
    SistemasDeMedicion: Optional[List[SistemasDeMedicion]]
    Aerogeneradores: List[Aerogeneradores]
    ParametroConexion: List[ParametroConexion]


class ArchivoSeries(BaseModel):
    Nombre: str


class JsonModelEolica(BaseModel):
    IdConexionWs: str
    IdTransaccion: str | None
    IdAplicacion: str | None
    ParametrosTransversales: ParametrosTransversales
    ParametrosConfiguracion: ParametrosConfiguracion
    ArchivoSeries: ArchivoSeries
