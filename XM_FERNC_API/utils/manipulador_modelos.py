import numpy as np

from typing import Dict, Tuple

from infraestructura.models.eolica.parametros import (
    JsonModelEolica,
    EspecificacionesEspacialesAerogeneradores,
)
from utils.decoradores import capturar_excepciones
from utils.mensaje_constantes import MensajesEolica


class ManipuladorModelos:
    @capturar_excepciones(
            "No es posible ajustar los aerogeneradores.",
            "Ajustando Aerogeneradores.",
            MensajesEolica.Error.ASIGNAR_TORRES_A_EROGENERADOR.value
    )
    def ajustar_aerogeneradores(
        self, params: JsonModelEolica, torres: Dict
    ) -> JsonModelEolica:
        """
        Metodo para la actualizacion de los aerogeneradores a la torre mas cercana
        tomando en cuenta su radio de representatividad.

        Args:
            - params (JsonModelEolica): Objeto que contiene la informacion del JSON
            - torres (Dict): Diccionario que contiene objetos Torre.

        Retorna:
            - params: Objeto JSON con los aerogeneradores actualizados a la torre mas cercana.
        """
        for aerogeneradores in params.ParametrosConfiguracion.Aerogeneradores:
            for especificaciones_espaciales in aerogeneradores.EspecificacionesEspacialesAerogeneradores:
                id_torre = especificaciones_espaciales.MedicionAsociada.Value
                coord_aero = (
                    especificaciones_espaciales.Latitud,
                    especificaciones_espaciales.Longitud,
                    especificaciones_espaciales.Elevacion,
                )
                distancia = torres[id_torre].obtener_distancia(coord_aero)

                if not torres[id_torre].comparar_distancia(distancia):
                    self._buscar_torre_mas_cercana(
                        torres, coord_aero, especificaciones_espaciales
                    )
        return params

    def _buscar_torre_mas_cercana(
        self,
        torres: Dict,
        coord_aero: Tuple,
        especificaciones_espaciales: EspecificacionesEspacialesAerogeneradores,
    ) -> None:
        """
        Metodo para ajustar la id de la torre asignada al aerogenerador.

        Args:
            - torres (Dist): Diccionario que contiene objetos Torre.
            - coord_aero (Tuple): Tupla que contiene las coordenadas del aerogenerador.
            - especificaciones_espaciales (EspecificacionesEspacialesAerogeneradores): Especificaciones espaciales
            de la torre asignada al aerogenerador.
        Retorna:
            - None
        """
        dist_min = np.inf
        for torre in torres.values():
            distancia_torre_aerogenerador = torre.obtener_distancia(coord_aero)

            if (
                torre.comparar_distancia(distancia_torre_aerogenerador)
                and distancia_torre_aerogenerador < dist_min
            ):
                especificaciones_espaciales.MedicionAsociada.Value = torre.id
                dist_min = distancia_torre_aerogenerador
