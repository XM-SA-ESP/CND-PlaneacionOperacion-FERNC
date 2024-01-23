import numpy as np
import pandas as pd
import scipy.optimize as scipy_optimize

from typing import List, Dict
from functools import lru_cache

from utils.eolica.caracterizacion_estela import Estela
from utils.eolica.dataclasses_eolica import Modelo

class CorreccionVelocidadParque:
    def __init__(self) -> None:
        self.estela = Estela()

    def correccion_velocidad_parque_eolico(
        self,
        fecha: pd.DatetimeIndex,
        ordenamiento: List,
        aerogeneradores: Dict,
        modelos: Dict,
        h_buje_promedio: List,
        offshore: bool,
        z_o1: float,
        z_o2: float,
        cre: float
    ) -> tuple:
        """
        Correccion de la velocidad del viento por efectos de grandes parques. En base al ordenamiento y la fecha
        se toma un aerogenerador de referencia y se calcula la velocidad corregida sin recuperacion y con recuperacion.
        En este mismo proceso se calcula la velocidad del viento afectada por la estela.

        Args:
            - fecha (pd.DatetimeIndex): Fecha referencia para el calculo.
            - ordenamiento (List): Lista que contiene tuples con los ids de los generadores.
            - aerogeneradores (Dict): Diccionario con objetos Aerogenerador.
            - modelos (Dict): Diccionario con objetos Modelo.
            - h_buje_promedio (float): Altura buje promedio.
            - offshore (bool): Parametro offshore
            - z_o1: Rugosidad del terreno
            - z_o2: Rugosidad aumentada por el parque
            - cre: Constante que depende de offshore
        yield:
            - tuple: Una tupla que contiene:
                - vel_estela | None: Velocidad de la estela si las condiciones se cumplen o None si hay correccion.
                - id_aero | None:  Id del aerogenerador cuya velocidad se ve afectada o None si no hay correccion.

        """
        combinaciones_ordenamiento = [(ordenamiento[0], x) for x in ordenamiento[1:]]
        influencia_acumulada = 0

        for comb in combinaciones_ordenamiento:
            aero1, aero2 = aerogeneradores[comb[0]], aerogeneradores[comb[1]]
            modelo_i, modelo_j = modelos[aero1.modelo], modelos[aero2.modelo]

            x_lon_i_j = aero2.longitud - aero1.longitud
            x_lat_i_j = aero2.latitud - aero1.latitud
            elevacion_i, elevacion_j = (
                aero1.elevacion,
                aero2.elevacion,
            )
            h_buje_i, h_buje_j = (
                modelo_i.altura_buje,
                modelo_j.altura_buje,
            )
            diametro_rotor_j = modelo_j.diametro_rotor

            dir_viento = aero2.df.loc[fecha, "DireccionViento"]
            vel_viento = aero2.df.loc[fecha, "VelocidadViento"]
            theta_j = dir_viento * np.pi / 180
            x_dist = self.__calculo_x_dist(
                theta_j,
                x_lon_i_j,
                x_lat_i_j,
                elevacion_j,
                h_buje_j,
                elevacion_i,
                h_buje_i
            )
            curva_vel, curva_coef, curva_vcth = self.__obtener_curvas(modelo_j)

            if offshore and x_dist > 0:
                h_prima, z_prima = self.__calculo_h_z_prima(diametro_rotor_j, x_dist, h_buje_j, h_buje_promedio, z_o2)
                vel_corregida = self.__velocidad_corregida_sin_recuperacion(h_prima, z_prima, vel_viento, z_o1, z_o2)
                
                if x_dist / diametro_rotor_j >= 60:
                    x_inicio = 60 * diametro_rotor_j
                    x_50 = 40 * diametro_rotor_j
                    vel_corregida = self.__velocidad_corregida_con_recuperacion(
                        vel_viento,
                        vel_corregida,
                        x_dist,
                        x_inicio,
                        x_50
                    )

                vel_estela, vel_influencia = self.estela.caracterizacion_estela(
                    fecha,
                    aero1,
                    aero2,
                    modelo_j,
                    cre,
                    x_dist,
                    vel_corregida,
                    curva_coef,
                    curva_vcth,
                    theta_j,
                    x_lon_i_j,
                    x_lat_i_j,
                    elevacion_j,
                    h_buje_j,
                    influencia_acumulada
                )
                influencia_acumulada += vel_influencia
                if vel_estela != vel_viento:
                    yield vel_estela, aero2.id_aero
                else:
                    yield None, None
            
            else:
                vel_estela, vel_influencia = self.estela.caracterizacion_estela(
                    fecha,
                    aero1,
                    aero2,
                    modelo_j,
                    cre,
                    x_dist,
                    vel_viento,
                    curva_coef,
                    curva_vcth,
                    theta_j,
                    x_lon_i_j,
                    x_lat_i_j,
                    elevacion_j,
                    h_buje_j,
                    influencia_acumulada
                )
                influencia_acumulada += vel_influencia
                if vel_estela != vel_viento:
                    yield vel_estela, aero2.id_aero
                else:
                    yield None, None

    @lru_cache(maxsize=None)
    def __velocidad_corregida_sin_recuperacion(
        self,
        h_prima: float,
        z_prima: float,
        vel_viento: float,
        z_o1: float,
        z_o2: float
    ) -> np.float64 | float:
        """
        Calculo para obtener la velocidad corregida sin recuperacion.
        
        Args:
            - h_prima (float): Parametro h prima (h').
            - z_prima (float): Parametro z prima (z').
            - vel_viento (float): Velocidad del viento del aerogenerador j.
            - z_o1: Rugosidad del terreno.
            - z_o2: Rugosidad aumentada por el parque.
        Retorna:
            - v_gf_j (np.float64): Velocidad corregida sin recuperacion si se cumplen las condiciones
            o la velocidad del viento de j si no se ve afectada.
        """
        if z_prima > (0.09 * h_prima) and z_prima < (0.3 * h_prima):
            v_gf_j = self.__z_prima_mayor(vel_viento, z_prima, h_prima, z_o1, z_o2)
            return v_gf_j
        elif z_prima < (0.09 * h_prima):
            v_gf_j = self.__z_prima_menor(vel_viento, z_prima, h_prima, z_o1, z_o2)
            return v_gf_j
        else:
            return vel_viento
        
    @lru_cache(maxsize=None)
    def __velocidad_corregida_con_recuperacion(
        self,
        vel_viento: float,
        vel_corregida: float,
        x_dist: np.float64,
        x_inicio: float,
        x_50: float
    ) -> np.float64:
        """
        Calculo para obtener la velocidad corregida con recuperacion.

        Args:
            - vel_viento (float): Velocidad del viento del aerogenerador j.
            - vel_corregida (float): Velocidad del viento corregida del aerogenerador j.
            - x_dist (np.float64): Parametro x dist.
            - x_inicio (float)
            - x_50 (float)
        Retorna:
            - vel_corregida_con_recuperacion (np.float64): Velocidad delo viento corregida con recuperacion.
        """
        vel_corregida_con_recuperacion = vel_viento * (1 - (1 - (vel_corregida/vel_viento)) * (0.5 ** ((x_dist - x_inicio)/x_50)))
        return vel_corregida_con_recuperacion

    def calcular_h_buje_promedio(self, modelos: Dict, aerogeneradores: Dict) -> np.float64:
        """
        Calculo de la temperatura buje promedio de todos los aerogeneradores.

        Args:
            - modelos (Dict): Diccionario con dataclasses Modelo.
            - aerogeneradores (Dict): Diccionario con dataclasses Aerogenerador.
        
        Retorna:
            - h_buje_promedio (float): Altura buje promedio.
        """
        altura_buje_lista = []
        for aero in aerogeneradores.values():
            altura_buje_lista.append(modelos[aero.modelo].altura_buje)

        h_buje_promedio = np.mean(altura_buje_lista)

        return h_buje_promedio
    
    @lru_cache(maxsize=None)
    def __z_prima_mayor(
        self, vel_viento: float, z_prima: float, h_prima: float, z_o1: float, z_o2: float
    ) -> np.float64:
        """
        Calculo de z_prima para la condicion z_prima > (0.09 * h_prima) and z_prima < (0.3 * h_prima)

        Args:
            - vel_viento (float): Velocidad del viento del aerogenerador j.
            - z_prima (float): Parametro z prima (z')
            - h_prima (float): Parametro h_prima (h')
            - z_o1: Rugosidad del terreno.
            - z_o2: Rugosidad aumentada por el parque.
        Retorna:
            Float con el calculo para la condicion.
        """
        return (vel_viento / np.log(z_prima / z_o1)) * (((np.log(h_prima / z_o1) / np.log(h_prima / z_o2)) * (np.log(0.09 * h_prima / z_o2)) * (1 - (np.log(z_prima / (0.09 * h_prima)) / np.log(0.3 / 0.09)))) + ((np.log(0.3 * h_prima / z_o1)) * (np.log(z_prima/ (0.09 * h_prima)) / np.log(0.3 / 0.09))))

    @lru_cache(maxsize=None)
    def __z_prima_menor(
        self, vel_viento: float, z_prima: float, h_prima: float, z_o1: float, z_o2: float
    ) -> np.float64:
        """
        Calculo de z_prima para la condicion z_prima < (0.09 * h_prima)

        Args:
            - vel_viento (float): Velocidad del viento del aerogenerador j.
            - z_prima (float): Parametro z prima (z')
            - h_prima (float): Parametro h_prima (h')
            - z_o1: Rugosidad del terreno.
            - z_o2: Rugosidad aumentada por el parque.
        Retorna:
            Float con el calculo para la condicion.
        """
        return vel_viento * (((np.log(h_prima / z_o1) * np.log(z_prima / z_o2))) / ((np.log(h_prima / z_o2) * np.log(z_prima / z_o1))))
    
    def __altura_capa_limite_interna(self, h: float, x: float, z_02: float) -> float:
        """
        x: Distancia a sotavento
        z_02: Rugosidad aumentada por el parque
        """
        return (h * (np.log(h / z_02) - 1)) - (0.9 * x)

    @lru_cache(maxsize=None)
    def __calculo_x_dist(
        self,
        theta: float,
        x_lon_i_j: float,
        x_lat_i_j: float,
        elevacion_j: float,
        h_buje_j: float,
        elevacion_i: float,
        h_buje_i: float,
    ) -> np.float64:
        """
        Calculo de x_dist construyendo dos vectores en numpy y calculando el producto
        punto entre los dos.

        Args:
            - theta (float): Parametro Theta j.
            - x_lon_i_j (float): Distancia entre longitudes de los aerogeneradores i j.
            - x_lat_i_j (float): Distancia entre latitudes de los aerogeneradores i j.
            - elevacion_j (float): Elevacion del aerogenerador j.
            - h_buje_j (float): Altura del buje del aerogenerador j.
            - elevacion_i (float): Elevacion del aerogenerador i.
            - h_buje_i (float): Altura del buje del aerogenerador i.
        Retorna:
            - x_dist(np.float64): Resultado del producto punto entre los dos vectores.
        """
        vector_1 = np.array([-np.cos(theta), -np.sin(theta), 0])
        vector_2 = np.array(
            [
                x_lon_i_j,
                x_lat_i_j,
                (elevacion_j + h_buje_j) - (elevacion_i + h_buje_i),
            ]
        )

        x_dist = np.dot(vector_1, vector_2)

        return x_dist

    @lru_cache(maxsize=None)
    def __calculo_h_z_prima(
        self,
        diametro: float,
        x_dist: np.float64,
        h_buje: float,
        h_buje_promedio: np.float64,
        z_o2: float,
    ) -> tuple:
        """
        Calculo de los parametros h prima (h') y z prima (z')

        Args:
            - diamero (float): Diametro del rotor del aerogenerador j.
            - x_dist (np.float64): Parametro x dist.
            - h_buje (float): Altura del buje del aerogenerador j.
            - h_buje_promedio (np.float64): Altura buje promedio.
            - z_o2 (float): Rugosidad aumentada por el parque.
        """
        h_cli = scipy_optimize.root_scalar(
            f=self.__altura_capa_limite_interna,
            args=(x_dist, z_o2),
            bracket=[0.0001, 10000],
            method="bisect",
        ).root # Altura capa limite (hcli) calculada con el metodo biseccion.
        h_prima = h_cli + ((2 / 3) * h_buje_promedio)
        z_prima = h_buje - diametro

        return h_prima, z_prima

    def __obtener_curvas(self, modelo: Modelo):
        """
        Metodo privado para la obtencion de las curvas del fabricante
        
        Args:
            - modelo (Modelo): Objeto Modelo con la informacion relacionada al modelo.
        Retorna:
            - tuple: Tupla que contiene:
                - curva_vel (np.array): Numpy array con curva para la serie de velocidad.
                - curva_coef (np.array): Numpy array con curva para la serie de Coeficiente.
                - curva_vcth (np.array): Numpy array con curva para la serie vcth.
        """
        curva_vel = np.array([data.SerieVelocidad for data in modelo.curvas_fabricante])
        curva_coef = np.array([data.SerieCoeficiente for data in modelo.curvas_fabricante])
        curva_vcth = np.array([data.SerieVcthCorregida for data in modelo.curvas_fabricante])

        return curva_vel, curva_coef, curva_vcth
    
    @staticmethod
    def obtener_curvas_potencia_velocidad(modelo: Modelo):
        curva_vel = np.array([data.SerieVelocidad for data in modelo.curvas_fabricante])
        curva_potencia = np.array([data.SeriePotencia for data in modelo.curvas_fabricante])
        return curva_vel, curva_potencia
