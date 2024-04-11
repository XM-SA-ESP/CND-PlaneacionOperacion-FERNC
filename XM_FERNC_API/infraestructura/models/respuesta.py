from typing import List
from dataclasses import dataclass, field

@dataclass
class Resultado:
    anio: int = field(metadata={"alias": "Anio"})
    mes: int = field(metadata={"alias": "Mes"})
    valor: float = field(metadata={"alias": "Valor"})
    """
    Anio: int
    Mes: int
    Valor: float
    """

@dataclass
class Respuesta:
    archivo_resultados: str
    datos_enficc: List[Resultado]
    datos_eda: List[Resultado]
