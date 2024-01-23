from typing import List
from dataclasses import dataclass

@dataclass
class Resultado:
    Anio: int
    Mes: int
    Valor: float

@dataclass
class Respuesta:
    ArchivoResultados: str
    DatosEnficc: List[Resultado]
    DatosEda: List[Resultado]
