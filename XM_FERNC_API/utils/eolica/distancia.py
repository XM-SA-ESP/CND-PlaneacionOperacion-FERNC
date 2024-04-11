import math
import numpy as np


def distancia_geodesica(lat1, lon1, ele1, lat2, lon2, ele2) -> float:
    """
    Calcula la distancia geodésica entre dos puntos en la superficie de la Tierra.

    Parámetros:
    - lat1 (float): Latitud del primer punto.
    - lon1 (float): Longitud del primer punto.
    - ele1 (float): Elevacion del primer punto.
    - lat2 (float): Latitud del segundo punto.
    - lon2 (float): Longitud del segundo punto.
    - ele2 (float): Elevacion del segundo punto

    Retorna:
    - float: Distancia geodésica calculada en kilómetros.
    """
    # Validar las coordenadas
    for coord in [lat1, lat2]:
        if not -90 <= coord <= 90:
            raise ValueError("La latitud debe estar entre -90 y 90 grados.")
    for coord in [lon1, lon2]:
        if not -180 <= coord <= 180:
            raise ValueError("La longitud debe estar entre -180 y 180 grados.")

    # Convertir latitud y longitud de grados a radianes
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Fórmula de Haversine
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    # Radio de la Tierra en kilómetros. Usa 3956 para millas
    r = 6371

    x_geodesica = c * r

    x_j = np.sqrt((x_geodesica ** 2) + (((ele2 / 1000) - (ele1 / 1000)) ** 2))

    # Calcular el resultado
    return x_j

def haversine(lat1:float, lon1:float, lat2:float, lon2:float) -> float:
    lat1, lon1, lat2, lon2 = map(np.deg2rad, [lat1, lon1, lat2, lon2])

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = np.sin(delta_lat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(delta_lon/2)**2

    c = 2 * np.arcsin(np.sqrt(a))

    r = 6371

    x_geodesica = c * r

    x_j = np.sqrt(x_geodesica ** 2)

    return x_j