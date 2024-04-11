from typing import List, Dict
from infraestructura.models.eolica.parametros import JsonModelEolica
from utils.eolica.distancia import distancia_geodesica

from utils.eolica.dataclasses_eolica import Aerogenerador


class CalculoPcc:
    """
    Clase que contiene los metodos para el calculo de la distancia entre el aerogenerador y el PCC (Punto de conexion comun).
    """

    def calculo_pcc_aerogenerador(
        self, params: JsonModelEolica, aerogeneradores: Dict
    ) -> Dict:
        """
        Calcula la distancia geodésica desde cada aerogenerador hasta el punto de conexión a la red (PCC).
        Params:
            -params: Modelo de objeto eólica generado desde aplicación front.
            -aerogeneradores: Diccionario de datos con los aerogeneradores configurados desde aplicación

        Retorna:
            aerogeneradores: Diccionario de aerogeneradores con la distancia al pcc actualizados.
        """
        grupo_conexiones = self.__agrupar_conexiones_pcc(params)

        for sublist in grupo_conexiones:
            for i, comb in enumerate(sublist):
                aero = aerogeneradores[comb[0]]
                if aero.dist_pcc == None:
                    conexiones = sublist[i:]
                    resultado_grupos = self.__obtener_calculo_conexiones_pcc(
                        conexiones, aerogeneradores
                    )
                    resultado_pcc = self.__obtener_distancia_geodesica_pcc_aero(
                        resultado_grupos
                    )
                    aero.dist_pcc = resultado_pcc
        aerogeneradores.pop("pcc")

        return aerogeneradores

    def __obtener_distancia_geodesica_pcc_aero(
        self, dist_aerogeneradores: List
    ) -> float:
        """
        Calcula la distancia geodésica total desde el punto de conexión a la red (PCC) hasta un aerogenerador, sumando las distancias proporcionadas.

        Parámetros:
        - dist_aerogeneradores (List): Lista de distancias desde el PCC hasta cada aerogenerador.

        Retorna:
        - Float: Resultado de la distancia geodésica total redondeada a 4 decimales.
        """
        resultado = round(sum(dist_aerogeneradores), 4)
        return resultado

    def __obtener_calculo_conexiones_pcc(
        self, conexiones: List, aerogeneradores: Dict
    ) -> List:
        """
        Calcula las distancias geodésicas entre pares de aerogeneradores especificados en las conexiones proporcionadas.

        Parámetros:
        - conexiones (List): Lista de conexiones, donde cada conexión es una tupla que contiene dos identificadores de aerogeneradores.
        - aerogeneradores (Dict): Diccionario que contiene información sobre los aerogeneradores, donde las claves son identificadores únicos y los valores son objetos aerogeneradores.

        Retorna:
        - List: Lista de distancias geodésicas calculadas para cada par de aerogeneradores en las conexiones.
        """
        resultado = []
        cache = {}

        for grupo in conexiones:
            id1, id2 = grupo

            if grupo in cache:
                resultado.append(cache[grupo])
                continue

            aero1 = aerogeneradores[id1]
            aero2 = aerogeneradores[id2]

            x_i_j = self.__calculo_distancia_geodesica(aero1, aero2)

            resultado.append(x_i_j)

            cache[grupo] = x_i_j

        cache.clear()

        return resultado

    def __agrupar_conexiones_pcc(self, params: JsonModelEolica) -> List:
        """
        Agrupa las conexiones de los aerogeneradores según la configuración especificada en los parámetros.

        Parámetros:
        - params (JsonModelEolica): Objeto que contiene los parámetros de configuración de la modelización eólica.

        Retorna:
        - List: Lista de grupos de conexiones, donde cada grupo es una lista de tuplas que representan conexiones entre aerogeneradores y el punto de conexión a la red (PCC).
        """
        conexiones_lista = []

        for data in params.ParametrosConfiguracion.ParametroConexion:
            grupo_conexiones = [
                conexiones.IdentificadorAerogenerador
                for conexiones in data.ConexionAerogenerador
            ]
            grupo_conexiones.append("pcc")
            conexiones_lista.append(grupo_conexiones)

        conexiones_agrupadas = [
            [(sublist[i], sublist[i + 1]) for i in range(len(sublist) - 1)]
            for sublist in conexiones_lista
        ]

        return conexiones_agrupadas

    def __calculo_distancia_geodesica(self, aero_1: Aerogenerador, aero_2: Aerogenerador) -> float:
        """
        Calcula la distancia geodésica entre dos aerogeneradores utilizando una nueva fórmula.

        Parámetros:
        - aero_1 (Aerogenerador): Primer aerogenerador.
        - aero_2 (Aerogenerador): Segundo aerogenerador.

        Retorna:
        - float: Distancia geodésica calculada en kilómetros.
        """
        distancia = distancia_geodesica(
            aero_1.latitud, aero_1.longitud, aero_1.elevacion, aero_2.latitud, aero_2.longitud, aero_2.elevacion
        )
        return distancia
