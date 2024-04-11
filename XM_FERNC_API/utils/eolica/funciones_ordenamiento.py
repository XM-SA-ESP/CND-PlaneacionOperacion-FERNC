import numpy as np
import pandas as pd

from typing import Dict, Tuple
from utils.decoradores import capturar_excepciones

from utils.eolica.distancia import haversine
from utils.manipulador_excepciones import CalculoExcepcion
from utils.mensaje_constantes import MensajesEolica


class Ordenamiento:
    @capturar_excepciones(
            MensajesEolica.Estado.ORDENAMIENTO.value,
            MensajesEolica.Error.ORDENAMIENTO.value,
            CalculoExcepcion
    )
    def ordenamiento_vectorizado(self, aerogeneradores: Dict, n_estampas: int) -> Dict:
        """
        Calculo vectorizado del ordenamiento para las estampas de tiempo. Retorna un diccionario con las estampas como
        key y dataframes como values con la informacion para esa estampa.

        Parámetros:
        - self: Instancia de la clase que contiene el método.
        - aerogeneradores (Dict): Diccionario que mapea identificadores de aerogeneradores a objetos de aerogeneradores.
        - n_estampas (int): Numero de estampas de tiempo.

        Retorno:
        - direcciones_por_estampa (Dict): Diccionario con Pandas DatetimeIndex como keys y Dataframe como values.
        """
        # Configuración del parque en DataFrame
        aux_longitud = np.array([i.longitud for i in aerogeneradores.values()])
        aux_latitud = np.array([i.latitud for i in aerogeneradores.values()])

        lista_aero_df = []

        for aero in aerogeneradores.values():
            lista_aero_df.append(aero.df)

        # Dataframe auxiliar con shape n estampas por n aerogeneradores
        aux_df = pd.concat(lista_aero_df, axis=1)["DireccionViento"]

        direcciones_por_estampa = {}
        dir_promedio = aux_df["DireccionViento"].mean(axis=1)

        def _recorrer_estampas(i: int) -> None:
            """
            Distancia 2D respecto a la primera turbina
            """
            lat_t1 = aux_latitud[0]
            lon_t1 = aux_longitud[0]

            parque_reorganizado = pd.DataFrame({
                "id_turbina": np.array([i.id_aero for i in aerogeneradores.values()]),
                "Elevacion_m": np.array([i.elevacion for i in aerogeneradores.values()])
            })

            parque_reorganizado["longitud_m"], parque_reorganizado["latitud_m"] = self._organizacion(
                lat_t1=lat_t1, lon_t1=lon_t1, tj_longitud=aux_longitud, tj_latitud=aux_latitud
            )

            theta_j = (90 - dir_promedio[i]) * (np.pi / 180)  # Valor en Radianes

            parque_reorganizado["factor_reordenamiento"] = np.sin(theta_j) * parque_reorganizado["longitud_m"] + np.cos(theta_j) * parque_reorganizado["latitud_m"]

            parque_reorganizado = parque_reorganizado.sort_values(by=["factor_reordenamiento"], ascending=False).reset_index(drop=True)
            parque_reorganizado.index = parque_reorganizado.index + 1
            # parque_reorganizado.set_index("id_turbina", inplace=True)

            direcciones_por_estampa[dir_promedio.index[i]] = parque_reorganizado

        np.vectorize(_recorrer_estampas)(np.arange(stop=n_estampas))

        return direcciones_por_estampa

    def _organizacion(
        self, lat_t1: float, lon_t1: float, tj_longitud: np.array, tj_latitud: np.array
    ) -> Tuple:
        """
        Metodo privado para obtener longitud_m y latitud_m que seran usados en para calcular
        el factor de ordenamiento.

        Parámetros:
        - self: Instancia de la clase que contiene el método.
        - lat_t1 (float): Latitud del aerogenerador i.
        - lon_t1 (float): Longitud del aerogenerador i.
        - tj_longitud (np.array): Vector que contiene la longitud de los aerogeneradores.
        - tj_latitud (np.array): Vector que contiene las latitudes de los aerogeneradores.

        Retorno:
        - Tuple: Tupla que contiene:
            - longitud_m.
            - latitud_m.
        """
        # Misma latitud, diferente longitud
        x = haversine(lat1=lat_t1, lon1=lon_t1, lat2=lat_t1, lon2=tj_longitud) # [km]

        # Diferente latitud, misma longitud
        y = haversine(lat1=lat_t1, lon1=lon_t1, lat2=tj_latitud, lon2=lon_t1) # [km]

        # Signo de la resta
        sign_x = np.sign(tj_longitud - lon_t1)
        sign_y = np.sign(tj_latitud - lat_t1)

        return sign_x * x * 1000, sign_y * y * 1000 # (x_m, y_m) [km])