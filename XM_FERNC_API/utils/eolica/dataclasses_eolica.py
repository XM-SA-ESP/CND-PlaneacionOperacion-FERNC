import pandas as pd
from typing import List
from dataclasses import dataclass
from XM_FERNC_API.infraestructura.models.eolica.parametros import (
    ConfiguracionAnemometro,
    CurvasDelFabricante,
)

from XM_FERNC_API.utils.eolica.distancia import distancia_geodesica


@dataclass
class Torre:
    """
    Clase que representa la estructura de las torres de sistemas de medición.
    Métodos:
        -comparar_distancia: Compara una distancia dada versus el radio de representatividad de un torre
        -obtener_distancia: Obtiene la distancia entre 2 torres según su longitud y latitud
    """
    id: str
    latitud: float
    longitud: float
    elevacion: float
    radio_r: float
    conf_anemometro: List[ConfiguracionAnemometro]
    archivo_series: str
    dataframe: pd.DataFrame

    def comparar_distancia(self, distancia: float) -> bool:
        if distancia <= self.radio_r:
            return True

        return False

    def obtener_distancia(self, coord_aerogenerador: tuple) -> float:
        distancia = distancia_geodesica(
            self.latitud, self.longitud, self.elevacion, coord_aerogenerador[0], coord_aerogenerador[1], coord_aerogenerador[2])
        return distancia


@dataclass
class Modelo:
    """
    Clase que representa la estructura de los modelos de aerogeneradores en una planta éolica.
    """
    nombre: str
    altura_buje: float
    diametro_rotor: float
    p_nominal: float
    v_nominal: float
    den_nominal: float
    v_min: float
    v_max: float
    t_min: float
    t_max: float
    curvas_fabricante: List[CurvasDelFabricante]


@dataclass
class Aerogenerador:
    """
    Clase que representa la estructura de un aerogenerador en una planta eólica.
    """
    id_aero: int
    id_torre: str
    latitud: float
    longitud: float
    elevacion: float
    modelo: str
    dist_pcc: float | None = None
    df: pd.DataFrame | None = None
    f_ordenamiento: float | None = 0
    curvas_fabricante: List[CurvasDelFabricante] | None = None

@dataclass
class Pcc:
    """
    Clase que representa la estructura de una serie de potencia.
    """
    latitud: float
    longitud: float
    elevacion: float
    voltaje: float
