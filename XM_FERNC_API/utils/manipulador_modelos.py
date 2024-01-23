import numpy as np

from typing import Dict

from infraestructura.models.eolica.parametros import JsonModelEolica


class ManipuladorModelos:
    def __init__(self) -> None:
        pass

    def ajustar_aerogeneradores(self, params: JsonModelEolica, torres: Dict) -> JsonModelEolica:
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
                coord_aero = (especificaciones_espaciales.Latitud, especificaciones_espaciales.Longitud)
                distancia = torres[id_torre].obtener_distancia(coord_aero)
                
                if not torres[id_torre].comparar_distancia(distancia):
                    dist_min = np.inf
                    for torre in torres.values():
                        distancia_torre_aerogenerador = torre.obtener_distancia(coord_aero)
                        
                        if (
                            torre.comparar_distancia(distancia_torre_aerogenerador)
                            and distancia_torre_aerogenerador < dist_min
                        ):
                            especificaciones_espaciales.MedicionAsociada.Value = torre.Id
                            dist_min = distancia_torre_aerogenerador

        return params