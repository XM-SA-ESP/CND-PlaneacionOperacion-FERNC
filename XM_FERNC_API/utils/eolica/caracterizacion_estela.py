import numpy as np
import pandas as pd

from functools import lru_cache

from utils.eolica.dataclasses_eolica import Aerogenerador, Modelo


class Estela:
    """
    Clase que contiene los metodos para la caracterizacion de la estela
    """
    def __init__(self) -> None:
        """
        Inicializa la clase Estela.
        """
        pass

    def caracterizacion_estela(
        self,
        fecha: pd.DatetimeIndex,
        aero1: Aerogenerador,
        aero2: Aerogenerador,
        modelo_j: Modelo,
        cre: float,
        x_dist: float,
        vel_viento_j: float,
        curva_coef: np.array,
        curva_vcth: np.array,
        theta_j: float,
        x_lon_i_j: float,
        x_lat_i_j: float,
        elevacion_j: float,
        h_buje_j: float,
        influencia_acumulada: float = 0,
    ):
        """
        Caracterizacion de la estela para la fecha y la combinacion de aerogeneradores i, j.

        Args:
            - fecha (pd.DatetimeIndex): Fecha de referencia.
            - aero1 (Aerogenerador): Objeto Aerogenerador que contiene la informacion del aerogenerador i.
            - aero2 (Aerogenerador): Objeto Aerogenerador que contiene la informacion del aerogenerador j.
            - modelo_j (Modelo): Objeto Modelo que contiene informacion del modelo del aerogenerador j.
            - cre (float): Constante que depende de offshore.
            - x_dist (float): Parametro x_dist.
            - vel_viento_j (float): Velocidad del viento corregida del aerogenerador j.
            - curva_coef (np.array): Numpy array de la serie curvas coef.
            - curva_vcth (np.array): Numpy array de la serie curvas vcth.
            - theta_j (float): Parametro theta j.
            - x_lon_i_j (float): Distancia entre longitudes de los aerogeneradores i j.
            - x_lat_i_j (float): Distancia entre latitudes de los aerogeneradores i j.
            - elevacion_j (float): Elevacion del aerogenerador j.
            - h_buje_j (float): Altura del buje deal aerogenerador j.
            - influencia_acumulada (float): Influencia acumulada usada para el calculo 
            de la velocidad influencia estela.
        Retorna:
            - tuple: Tupla que contiene:
                - vel_j_estela (float): Velocidad de viento de j afectada por el efecto estela.
                - vel_influencia_acumulada (float): Velocidad influencia estela acumulada hasta el aerogenerador
                j en la combinacion del ordenamiento.
        """
        diametro_rotor_j = modelo_j.diametro_rotor
        vel_viento_i = aero1.df.loc[fecha, "VelocidadViento"]
        den_buje = aero2.df.loc[fecha, "DenBuje"]
        den_nominal = modelo_j.den_nominal
        r_j_estela = self.__calculo_r_estela(diametro_rotor_j, cre, x_dist)
        c_fabricante = self.__obtener_c_fabricante(vel_viento_i, curva_vcth, curva_coef)
        coef_empuje = self.__calculo_coef_empuje(c_fabricante, den_nominal, den_buje)
        v_estela = self.__obtener_velocidad_estela(
            vel_viento_i, diametro_rotor_j, r_j_estela, coef_empuje
        )

        r_x_dist = self.__obtener_r_x_dist(x_dist)
        centro_estela = self.__obtener_centro_estela(
            x_lon_i_j, x_lat_i_j, x_dist, theta_j, elevacion_j, h_buje_j, r_x_dist
        )

        distancia_estela_j = self.__obtener_distancia_estela_aero(
            x_lon_i_j, x_lat_i_j, centro_estela, elevacion_j, h_buje_j, r_x_dist
        )

        radio_t_j = diametro_rotor_j / 2
        a_rotor = self.__obtener_area_rotor(radio_t_j)
        area_influencia_estela = self.__obtener_area_efecto_estela(
            distancia_estela_j, diametro_rotor_j, radio_t_j, r_j_estela, a_rotor
        )
        bj = self.__obtener_bj(area_influencia_estela, a_rotor)
        vel_influencia_estela = self.__obtener_vel_influencia_estela(
            bj, distancia_estela_j, vel_viento_i, r_x_dist, influencia_acumulada
        )
        vel_j_estela = self.__obtener_vel_j_estela(vel_viento_i, vel_influencia_estela)

        return vel_j_estela, vel_influencia_estela

    @lru_cache(maxsize=None)
    def __calculo_r_estela(
        self, diametro_rotor_j: float, cre: float, x_dist: float
    ) -> float:
        """
        Calculo del radio de la estela.

        Args:
            - diametro_rotor_j (float): Diametro del rotor j.
            - cre (float): Constante que depende de offshore. 
            - x_dist (float): Parametro x_dist.
        Retorna:
            - r_j_estela (float): Radio de la estela.
        """
        r_j_estela = (diametro_rotor_j / 2) + (cre * x_dist)
        return r_j_estela

    def __calculo_coef_empuje(
        self, c_fabricante: float, den_nominal: float, den_buje: float
    ) -> float:
        """
        Ajuste del coeficiente de empuje Cth por la densidad

        Args:
            - c_fabricante (float): Cth interpolada.
            - den_nominal (float): Densidad nominal.
            - den_buje (float): Densidad a la altura del buje para la estampa de tiempo de analisis.
        Retorna:
            - Coeficiente de empuje Cth (float).
        """
        return c_fabricante * (den_nominal / den_buje)

    def __obtener_c_fabricante(
        self, vel_viento: float, cur_vcth: np.array, cur_coef_empuje: np.array
    ) -> float:
        """
        Calculo de la Cth Fabricante usando el metodo interp de Numpy.

        Args:
            - vel_viento (float): Velocidad del viento para el aerogenerador i.
            - cur_vcth (np.array): Curvas de la serie vcth.
            - cur_coef_empuje (np.array): Curvas de la serie coeficiente de empuje.
        Retorna:
            - cth_fabricante (float): Cth fabricante
        """
        cth_fabricante = np.interp(
            vel_viento, cur_vcth, cur_coef_empuje
        )
        return cth_fabricante

    @lru_cache(maxsize=None)
    def __obtener_velocidad_estela(
        self,
        vel_viento_i: float,
        diametro_rotor_j: float,
        r_j_estela: float,
        cth: float,
    ) -> float:
        """
        Calculo de la velocidad estela incidente en el aerogenerador.

        Args:
            - vel_viento_i (float): Velocidad del viento para el aerogenerador i.
            - diametro_rotor_j (float): Diametro del rotor para el aerogenerador j.
            - r_j_estela (float): Radio de la estela.
            - cth (float): Coeficiente de empuje Cth.
        Retorna:
            - vel_estela (float): Velocidad de estela incidente en el aerogenerador.
        """
        vel_estela = vel_viento_i * (
            1 - (1 - np.sqrt(1 - cth)) * ((diametro_rotor_j / (2 * r_j_estela)) ** 2)
        )
        return vel_estela

    def __obtener_r_x_dist(self, x_dist: float) -> int:
        """
        Obtener valor del rectificador Rxdist

        Args:
            - x_dist (float): Parametro x_dist.
        Retorna:
            - 0 si x_dist es menor a cero. 1 si x_dist es mayor a cero.
        """
        if x_dist < 0:
            return 0
        return 1

    def __obtener_centro_estela(
        self,
        x_lon_i_j: float,
        x_lat_i_j: float,
        x_dist: float,
        theta_j: float,
        elevacion_j: float,
        h_buje_j: float,
        r_x_dist: int,
    ) -> np.array:
        """
        Calculo del centro de loa estela.

        Args:
            - x_lon_i_j (float): Distancia entre longitudes de los aerogeneradores i j.
            - x_lat_i_j (float): Distancia entre latitudes de los aerogeneradores i j.
            - x_dist (float): Parametro x_dist.
            - theta_j (float): Parametro theta j. 
            - elevacion_j (float): Elevacion del aerogenerador j.
            - h_buje_j (float): Altura del buje deal aerogenerador j.
            - r_x_dist (int): Parametro Rxdist.
        Retorna:
            - centro_e_ij (np.array): Matriz que representa el centro de la estela [Longitud, Latitud, Altura]
        """
        centro_e_ij = np.array(
            [
                (x_lon_i_j - (x_dist * np.cos(theta_j))) * r_x_dist,
                (x_lat_i_j - (x_dist * np.sin(theta_j))) * r_x_dist,
                (elevacion_j + h_buje_j) * r_x_dist,
            ]
        )
        return centro_e_ij

    def __obtener_distancia_estela_aero(
        self,
        x_lon_i_j: float,
        x_lat_i_j: float,
        c_estela: np.array,
        elevacion_j: float,
        h_buje_j: float,
        r_x_dist: int,
    ) -> float:
        """
        Calculo de la distancia entre la estela y el aerogenerador j.

        Args:
            - x_lon_i_j (float): Distancia entre longitudes de los aerogeneradores i j.
            - x_lat_i_j (float): Distancia entre latitudes de los aerogeneradores i j.
            - c_estela (np.array): Matriz del centro de la estela [Longitud, Latitud, Altura].
            - elevacion_j (float): Elevacion del aerogenerador j.
            - h_buje_j (float): Altura del buje deal aerogenerador j.
            - r_x_dist (int): Parametro Rxdist.
        Retorna:
            - distancia_e_j (float): Distancia entre el centro de la estela y el aerogenerador j.
        """
        distancia_e_j = abs(
            np.linalg.norm(
                [
                    (x_lon_i_j - c_estela[0]) * r_x_dist,
                    (x_lat_i_j - c_estela[1]) * r_x_dist,
                    ((elevacion_j + h_buje_j) - c_estela[2]) * r_x_dist,
                ]
            )
        )

        return distancia_e_j

    def __obtener_area_rotor(self, radio_rotor) -> float:
        """
        Calculo del area del rotor.

        Args:
            - radio_rotor (float): Radio del rotor del aerogenerador j.
        Retorna:
            - a_rotor (float): Area del rotor
        """
        a_rotor = np.pi * (radio_rotor ** 2)
        return a_rotor

    def __obtener_area_efecto_estela(
        self,
        distancia_estela_j: float,
        diametro_rotor_j: float,
        radio_t_j: float,
        r_j_estela: float,
        a_rotor: float,
    ) -> float:
        """
        Calculo del area de influencia de la estela

        -Args:
            - distancia_estela_j (float): Distancia entre el area de la estela y el aerogenerador j.
            - diametro_rotor_j (float): Diametro del rotor del aerogenerador j.
            - radio_t_j (float): Radio del aerogenerador j.
            - r_j_estela (float): Radio de la estela.
            - a_rotor (float): Area del rotor.
        - Retorna:
            - area_influencia_estela (float): Area de influencia de la estela.
        """
        if distancia_estela_j >= (radio_t_j + r_j_estela):
            area_influencia_estela = 0

        elif (radio_t_j + r_j_estela) > distancia_estela_j >= r_j_estela:
            d1 = abs(
                ((radio_t_j**2) - (r_j_estela**2) + (distancia_estela_j**2))
                / (2 * distancia_estela_j)
            )
            z = np.sqrt(abs((radio_t_j**2) - (d1**2)))
            area_influencia_estela = (
                (radio_t_j**2) * np.arccos((2 * d1) / diametro_rotor_j)
                + ((r_j_estela**2)
                * np.arccos((distancia_estela_j - d1) / r_j_estela))
                - (distancia_estela_j * z)
            )

        elif (distancia_estela_j + radio_t_j) >= r_j_estela and (
            distancia_estela_j > (np.sqrt((r_j_estela**2) - (radio_t_j**2)))
        ):
            d1 = abs(
                ((radio_t_j**2) - (r_j_estela**2) + (distancia_estela_j**2))
                / (2 * distancia_estela_j)
            )
            z = np.sqrt(abs(((radio_t_j**2) - (d1**2))))
            area_influencia_estela = (
                (radio_t_j**2) * np.arccos((2 * d1) / diametro_rotor_j)
                + ((r_j_estela**2)
                * np.arccos((distancia_estela_j - d1) / r_j_estela))
                - (distancia_estela_j * z)
            )

        elif (distancia_estela_j + radio_t_j) >= r_j_estela and (
            distancia_estela_j <= (np.sqrt((r_j_estela**2) - (radio_t_j**2)))
        ):
            d1 = abs(
                ((radio_t_j**2) - (r_j_estela**2) + (distancia_estela_j**2))
                / (2 * distancia_estela_j)
            )
            z = np.sqrt(abs(((radio_t_j**2) - (d1**2))))
            area_influencia_estela = (
                a_rotor
                - (radio_t_j**2) * np.arccos((2 * d1) / diametro_rotor_j)
                + (r_j_estela**2) * np.arccos((distancia_estela_j - d1) / r_j_estela)
                - (distancia_estela_j * z)
            )

        else:
            area_influencia_estela = a_rotor

        return area_influencia_estela

    def __obtener_bj(self, area_estela: float, area_rotor: float) -> float:
        """
        Calculo del parametro bj.

        Args:
            - area_estela (float): Area influencia de la estela.
            - area_rotor (float): Area del rotor.
        Retorna:
            - bj (float): Parametro bj.
        """
        bj = area_estela / area_rotor
        return bj

    def __obtener_vel_influencia_estela(
        self,
        bj: float,
        distancia_estela_j: float,
        vel_viento_i: float,
        r_x_dist: int,
        influencia_acumulada: float=0,
    ) -> float:
        """
        Calculo de la magnitud del area de la estela en terminos de la velocidad del viento.

        Args:
            - bj (float): Parametro bj.
            - distancia_estela_j (float): Distancia del centro de la estela al buje del aerogenerador j.
            - vel_viento_i (float): Velocidad del viento del aerogenerador i.
            - r_x_dist (int): Parametro Rxdist.
            - influencia_acumulada (float): Velocidad del viento influenciada por la estela acumulada hasta el generador j.
        Retorna:
            - v_influencia_estela (float): Magnitud del area de la estela.
        """
        v_influencia_estela = bj * (
            (distancia_estela_j - (vel_viento_i * r_x_dist)) ** 2
        )
        v_influencia_estela += influencia_acumulada
        return v_influencia_estela

    def __obtener_vel_j_estela(
            self, vel_viento_i: float, vel_influencia_estela: float
        ) -> float:
        """
        Calculo de la velocidad del viento perturbada por el efecto estela.

        Args:
            - vel_viento_i (float): Velocidad del viento del aerogenerador i.
            - vel_influencia_estela (float): Magnitud del area de la estela.
        Retorna:
            - Velocidad del viento influenciada por el efecto estela para el 
            aerogenerador j (float).
        """
        return vel_viento_i - np.sqrt(vel_influencia_estela)
