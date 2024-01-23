import math
from typing import List


def calculo_dhi(struct: List) -> int:
    """
    Calcula la Irradiancia Difusa Horizontal (DHI).

    Parámetros:
    - struct (List): Una lista que contiene los siguientes elementos:
        - [0]: GHI (Irradiancia Global Horizontal)
        - [1]: DNI (Irradiancia Directa Normal)
        - [2]: zenith (Ángulo zenital en grados).

    Retorno:
    - int: Valor calculado de la Irradiancia Difusa Horizontal (DHI).
    """
    # math.cos retorna el coseno de x radians.
    # Conversion de zenith de grados a radians para el calculo.
    dni = struct[0] - struct[1] * math.cos(math.radians(struct[2]))
    return dni


def calculo_temp_panel(struct: List) -> float:
    """
    Calcula la temperatura del panel solar.

    Parámetros:
    - struct (List): Una lista que contiene los siguientes elementos:
        - [0]: irradiancia (Nivel de irradiancia incidente en el panel solar).
        - [1]: temp_ambiente (Temperatura ambiente en grados Celsius).
        - [2]: Otros parámetros si es necesario para el cálculo.

    Retorno:
    - float: Temperatura calculada del panel solar.
    """
    temp_panel = struct[1] + ((struct[2] - 20) / 800) * struct[0]
    return temp_panel
