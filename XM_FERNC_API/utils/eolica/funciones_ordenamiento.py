import numpy as np

from typing import List, Dict


class Ordenamiento:
    def __init__(self) -> None:
        pass

    def obtener_ordenamiento(
        self,
        aerogeneradores: Dict,
        combinaciones_aero: List,
        fecha,
    ) -> List:
        """
        Calcula y asigna factores de ordenamiento a los aerogeneradores en base a la dirección del viento y ubicación relativa.

        Parámetros:
        - self: Instancia de la clase que contiene el método.
        - aerogeneradores: Un diccionario que mapea identificadores de aerogeneradores a objetos de aerogeneradores.
        - combinaciones_aero: Una lista de combinaciones de pares de aerogeneradores para calcular los factores de ordenamiento.
        - fecha: La fecha en la que se calcularán los factores de ordenamiento.
        - torres: (Opcional) Un diccionario que mapea identificadores de torres a objetos de torres. Se utiliza para obtener la dirección del viento si está presente.
        - df: (Opcional) Un DataFrame de pandas que contiene datos relevantes, especialmente la dirección del viento, si no se utiliza torres.

        Retorno:
        - List: Una lista ordenada de identificadores de aerogeneradores basada en los factores de ordenamiento calculados.
        """
        for comb in combinaciones_aero:
            aero1 = aerogeneradores[comb[0]]
            aero2 = aerogeneradores[comb[1]]
            x_lon_i_j = (
                aerogeneradores[comb[1]].longitud - aerogeneradores[comb[0]].longitud
            )
            x_lat_i_j = (
                aerogeneradores[comb[1]].latitud - aerogeneradores[comb[0]].latitud
            )
            slon_i_j = np.sign(x_lon_i_j)
            slat_i_j = np.sign(x_lat_i_j)

            d_viento_i = aero1.df.at[fecha, "DireccionViento"]
            d_viento_j = aero2.df.at[fecha, "DireccionViento"]
            if d_viento_i != d_viento_j:
                promedio_d = np.mean([d_viento_i, d_viento_j])
            else:
                promedio_d = d_viento_i

            thetaj = (90 - promedio_d) * (np.pi / 180) # Valor en Radianes

            factor_ordenamiento = (np.sin(thetaj) * (slon_i_j * x_lon_i_j)) + (np.cos(thetaj) * (slat_i_j * x_lat_i_j))
            aerogeneradores[comb[1]].f_ordenamiento = factor_ordenamiento

        lista_ordenamiento = self.__ordenar_lista(aerogeneradores)
        
        yield lista_ordenamiento

    def crear_combinaciones_aeros(self, aerogeneradores: Dict) -> tuple:
        """
        Crea combinaciones de pares de aerogeneradores para su posterior análisis.

        Parámetros:
        - self: Instancia de la clase que contiene el método.
        - aerogeneradores: Un diccionario que mapea identificadores de aerogeneradores a objetos de aerogeneradores.

        Retorno:
        - Tuple: Una tupla que contiene el diccionario de aerogeneradores modificado (sin el pcc) y la lista de combinaciones de pares de aerogeneradores.
        """

        lista_aeros = list(aerogeneradores.keys())
        combinaciones_aero = [(lista_aeros[0], x) for x in lista_aeros[1:]]

        return aerogeneradores, combinaciones_aero

    def __ordenar_lista(self, aerogeneradores: Dict) -> List:
        """
        Ordena una lista de aerogeneradores basándose en sus factores de ordenamiento.

        Parámetros:
        - self: Instancia de la clase que contiene el método.
        - aerogeneradores: Un diccionario que mapea identificadores de aerogeneradores a objetos de aerogeneradores.

        Retorno:
        - List: Una lista ordenada de identificadores de aerogeneradores basada en los factores de ordenamiento.
        """
        lista_ordenada = sorted(
            aerogeneradores,
            key=lambda x: aerogeneradores[x].f_ordenamiento,
            reverse=True,
        )

        return lista_ordenada
