import xm_solarlib


def obtener_solucion_circuito_eq(params_cec_df):
    """
    Crea diccionarios de modelos y aerogeneradores a partir de los parámetros de configuración proporcionados y 
    se deberá estimar la curva de voltaje con respecto a la corriente (curva I-V) para cada estampa temporal.

    Parámetros:
    - self: Instancia de la clase que contiene el método.
    - params: Un objeto JsonModelEolica que contiene parámetros de configuración para la modelización eólica.

    Retorno:
    - Tuple: Una tupla que contiene un diccionario de modelos de aerogeneradores y un diccionario de objetos de aerogeneradores.
    """
    resultado = xm_solarlib.pvsystem.singlediode(
        photocurrent=params_cec_df["photocurrent"],
        saturation_current=params_cec_df["saturation_current"],
        resistance_series=params_cec_df["resistance_series"],
        resistance_shunt=params_cec_df["resistance_shunt"],
        nnsvth=params_cec_df["nNsVth"],
        method="lambertw",
    )
    return resultado
