import numpy as np

from typing import Tuple

from XM_FERNC_API.utils.eolica.distancia import distancia_geodesica
from XM_FERNC_API.utils.eolica.dataclasses_eolica import Aerogenerador


def calculo_x_dist(
    theta: float,
    aero1,
    aero2,
    x_elevacion: float,
) -> np.float64:
    """
    Calculo de x_dist construyendo dos vectores en numpy y calculando el producto
    punto entre los dos.

    Args:
        - theta (float): Parametro Theta j.
        - aero1 (Aerogenerador): Aerogenerador i.
        - aero2 (Aerogenerador): Aerogenerador j.
        - x_elevacion (float): Diferencia de elevacion entre los aerogeneradores i j.
    Retorna:
        - x_dist(np.float64): Resultado del producto punto entre los dos vectores.
    """
    vector_1 = np.array([-np.cos(theta), -np.sin(theta), 0])

    x = distancia_geodesica(
        aero1["latitud"],
        aero1["longitud"],
        aero1["elevacion"],
        aero1["latitud"],
        aero2["longitud"],
        aero1["elevacion"],
    )
    y = distancia_geodesica(
        aero1["latitud"],
        aero1["longitud"],
        aero1["elevacion"],
        aero2["latitud"],
        aero1["longitud"],
        aero1["elevacion"],
    )
    slon_i_j, slat_i_j = obtener_slon_slat(aero1, aero2)

    vector_2 = np.array(
        [
            (slon_i_j * x * 1000),
            (slat_i_j * y * 1000),
            x_elevacion,
        ]
    )

    x_dist = np.dot(vector_1, vector_2)

    return x_dist


def obtener_slon_slat(
    aero1, aero2
) -> Tuple[float, float]:
    """
    Calculo para la obtencion de las distancias slon y slat en metros para cada
    combinacion entre areogeneradores i, j.

    Args:
        - aero1 (Aerogenerador): Aerogenerador i de la combinacion.
        - aero2 (Aerogenerador): Aerogenerador j de la combinacion.
    Retorna:
        - Tuple: Una tupla que contiene:
            - slon_i_j (float): Longitud en metros entre i, j.
            - slat_i_j (float): Latitud en metros entre i, j.
    """
    x_lon_i_j = aero2["longitud"] - aero1["longitud"]
    x_lat_i_j = aero2["latitud"] - aero1["latitud"]
    slon_i_j = np.sign(x_lon_i_j)
    slat_i_j = np.sign(x_lat_i_j)

    return slon_i_j, slat_i_j
