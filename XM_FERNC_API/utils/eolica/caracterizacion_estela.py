import scipy
import numpy as np
import pandas as pd
import xarray as xr

from utils.decoradores import capturar_excepciones
from utils.manipulador_excepciones import BaseExcepcion, CalculoExcepcion
from utils.mensaje_constantes import MensajesEolica


class Estela:

    def __init__(
        self,
        offshore: bool,
        cre: float,
        caracteristicas_tij: pd.DataFrame,
        densidad: pd.DataFrame,
        dataset: xr.Dataset,
        n_turbinas: int,
        curvas_xarray: xr.Dataset,
        n_estampa_df: tuple,
    ) -> None:

        self.offshore = offshore
        self.cre = cre
        self.caracteristicas_tij = caracteristicas_tij
        self.densidad = densidad
        self.dataset = dataset
        self.n_turbinas = n_turbinas
        self.curvas_xarray = curvas_xarray
        self.n_estampa_df = n_estampa_df

        self.vecdirtur = [
            self._vector_tij(t_i)
            for t_i in np.arange(start=1, stop=self.n_turbinas + 1)
        ]

        self.vecdir_tj = self._vecdir_tj()

        self.proyec = np.sum(np.multiply(self.vecdirtur, self.vecdir_tj), axis=1)
        self.proyec[self.proyec < 0] = 0

        self.rectificador = self.proyec.copy()
        self.rectificador[self.rectificador <= 0] = 0
        self.rectificador[self.rectificador > 0] = 1

        if self.offshore:
            txt_vel_dataset = 'velocidad_grandes_parques'
        else:
            txt_vel_dataset = 'velocidad_viento'


        # Velocidad del viento de las turbinas para la estampa n
        self.temp_vel_ti = self.dataset[txt_vel_dataset].T.values[self.n_estampa_df[0]]
    
    def _vecdir_tj(self):
        vecdir_tj = np.array(
            [
                -np.cos(
                    np.deg2rad(
                        self.dataset["direccion_viento"].values.T[self.n_estampa_df[0]]
                    )
                ),  # [rad]
                -np.sin(
                    np.deg2rad(
                        self.dataset["direccion_viento"].values.T[self.n_estampa_df[0]]
                    )
                ),  # [rad]
                np.zeros(self.n_turbinas),
            ]
        )  # [rad]

        return vecdir_tj

    def _vector_tij(self, t_i):
        return np.array(
            [
                self.n_estampa_df[1]["longitud_m"][t_i]
                - self.n_estampa_df[1]["longitud_m"].values,
                self.n_estampa_df[1]["latitud_m"][t_i]
                - self.n_estampa_df[1]["latitud_m"].values,
                (
                    self.n_estampa_df[1]["Elevacion_m"][t_i]
                    + self.caracteristicas_tij["altura_buje"][
                        self.n_estampa_df[1]["id_turbina"]
                    ][t_i]
                )
                - (
                    self.n_estampa_df[1]["Elevacion_m"].values
                    + self.caracteristicas_tij["altura_buje"][
                        self.n_estampa_df[1]["id_turbina"]
                    ].values
                ),
            ]
        )

    def _spline_cubico(self, i):
        cur_vel, cur_coef = (
            self.curvas_xarray.sel(turbina=i + 1)["cur_vel"].values,
            self.curvas_xarray.sel(turbina=i + 1)["cur_coef"].values,
        )
        return float(
            scipy.interpolate.splev(
                x=self.temp_vel_ti[i], tck=scipy.interpolate.splrep(cur_vel, cur_coef, k=3)
            )
        )

    def _norma_distancia_estela_rotor(self, i):

        centro_ji = self._centro_ij()

        resultado = np.linalg.norm(
            np.array(
                [
                    (self.n_estampa_df[1]["longitud_m"][i + 1] - centro_ji[i].T[0])
                    * self.rectificador[i],
                    (self.n_estampa_df[1]["latitud_m"][i + 1] - centro_ji[i].T[1])
                    * self.rectificador[i],
                    (
                        self.n_estampa_df[1]["Elevacion_m"][i + 1]
                        + self.caracteristicas_tij["altura_buje"][
                            self.n_estampa_df[1]["id_turbina"]
                        ].values
                        - centro_ji[i].T[2]
                    )
                    * self.rectificador[i],
                ]
            ).T,
            axis=1,
        )

        if np.isnan(resultado).any():
            raise BaseExcepcion(
                "se han encontrado valores NaN.",
                "Calculando Estela.",
                MensajesEolica.Error.DISTANCIA_ESTELA_ROTOR.value,
            )
        return resultado

    def _koch(self, radio_turbina, area_rotor, radio_estela, d):
        def area_influencia_estela_caso1():
            d1 = abs(((radio_turbina**2) - (radio_estela**2) + (d**2)) / (2 * d))
            z = abs((radio_turbina**2) - (d1**2)) ** 0.5

            return (
                (radio_turbina**2) * np.arccos(d1 / radio_turbina)
                + (radio_estela**2) * np.arccos((d - d1) / radio_estela)
                - (d * z)
            )

        def area_influencia_estela_caso2():
            d1 = abs(((radio_turbina**2) - (radio_estela**2) + (d**2)) / (2 * d))
            z = abs((radio_turbina**2) - (d1**2)) ** 0.5

            return (
                area_rotor
                - (radio_turbina**2) * np.arccos(d1 / radio_turbina)
                + (radio_estela**2) * np.arccos((d - d1) / radio_estela)
                - (d * z)
            )

        NUMPY_CONDITIONS = [
            d >= (radio_turbina + radio_estela),
            (d >= radio_estela) & (d < (radio_turbina + radio_estela)),
            (d + radio_turbina >= radio_estela)
            & (d > (((radio_estela**2) - (radio_turbina**2)) ** 0.5)),
            (d + radio_turbina >= radio_estela)
            & (d <= (((radio_estela**2) - (radio_turbina**2)) ** 0.5)),
        ]

        NUMPY_CHOICES = [
            0,
            area_influencia_estela_caso1(),
            area_influencia_estela_caso1(),
            area_influencia_estela_caso2(),
        ]

        resultado = np.select(
            condlist=NUMPY_CONDITIONS, choicelist=NUMPY_CHOICES, default=area_rotor
        )
        return resultado

    def _centro_ij(self):
        centro_ji = np.stack(
            [
                (
                    self.n_estampa_df[1]["longitud_m"].values
                    + self.proyec * self.vecdir_tj[0]
                )
                * self.rectificador,
                (
                    self.n_estampa_df[1]["latitud_m"].values
                    + self.proyec * self.vecdir_tj[1]
                )
                * self.rectificador,
                (
                    self.n_estampa_df[1]["Elevacion_m"].values
                    + self.caracteristicas_tij["altura_buje"][
                        self.n_estampa_df[1]["id_turbina"]
                    ].values
                )
                * self.rectificador,
            ],
            axis=-1,
        )

        return centro_ji

    @capturar_excepciones(
        MensajesEolica.Estado.ESTELA.value,
        MensajesEolica.Error.ESTELA.value,
        CalculoExcepcion,
    )
    def efecto_estela_vectorizado(
        self,
    ) -> xr.Dataset:
        '''
        Estimación de velocidades perturbadas por efecto de estela
        ''' 
    
        # Cálculo del radio de la estela Tj a la altura de t_i
        radio_estela = np.where(
            self.proyec > 0,
            self.caracteristicas_tij["radio"].values + self.cre * self.proyec,
            0,
        )

        if np.isnan(radio_estela).any():
            raise BaseExcepcion(
                "Radio estela con valores NaN.",
                "Calculando Radio estela.",
                MensajesEolica.Error.RADIO_ESTELA.value,
            )

        try:
            aux_ct = np.array(
                list(map(self._spline_cubico, np.arange(stop=self.n_turbinas)))
            )
        except Exception:
            raise BaseExcepcion(
                MensajesEolica.Error.ESTELA.value,
                MensajesEolica.Estado.ESTELA.value,
                MensajesEolica.Error.ESTELA.value,
            )

        if np.isnan(aux_ct).any():
            raise BaseExcepcion(
                "aux_ct con valores NaN.",
                "Calculando Efecto estela.",
                MensajesEolica.Error.SPLINE_CUBICO.value,
            )

        cth = (
            aux_ct
            * self.caracteristicas_tij["densidad"].values
            / self.densidad.iloc[self.n_estampa_df[0]].values
        )

        estela_ji = self.temp_vel_ti * (
            1
            - (1 - np.sqrt(1 - cth))
            * (
                self.caracteristicas_tij["radio"][
                    self.n_estampa_df[1]["id_turbina"]
                ].values
                / radio_estela
            )
            ** 2
        )
        estela_ji[(estela_ji == -np.inf) | (estela_ji == np.inf)] = 0

        d = np.array(
            list(
                map(self._norma_distancia_estela_rotor, np.arange(stop=self.n_turbinas))
            )
        )

        radio_turbina = np.repeat(
            self.caracteristicas_tij["radio"].values[None, :],
            repeats=self.n_turbinas,
            axis=0,
        )
        area_rotor = np.repeat(
            self.caracteristicas_tij["area_rotor"].values[None, :],
            repeats=self.n_turbinas,
            axis=0,
        )

        ashad = np.array(
            list(
                map(
                    lambda x, y, z, w: self._koch(x, y, z, w),
                    radio_turbina.flatten(),
                    area_rotor.flatten(),
                    radio_estela.flatten(),
                    d.flatten(),
                )
            )
        ).reshape(self.n_turbinas, self.n_turbinas)
        ashad[np.isnan(ashad)] = 0

        beta = ashad / area_rotor
        suma = np.sum(
            beta * ((estela_ji - self.temp_vel_ti) ** 2) * self.rectificador, axis=1
        )
        suma = np.sum(beta * ((estela_ji - self.temp_vel_ti)**2) * self.rectificador, axis=1)

        vel_perturbada = self.temp_vel_ti - suma**0.5

        vel_perturbada = np.where(
            np.isnan(vel_perturbada) == True, self.temp_vel_ti, vel_perturbada
        )

        # Filtro por NaN
        vel_perturbada = np.where(np.isnan(vel_perturbada) == True, self.temp_vel_ti, vel_perturbada)
        vel_perturbada = np.where(
            np.isnan(vel_perturbada) == True, self.temp_vel_ti, vel_perturbada
        )

        vel_perturbada = np.where(vel_perturbada < 0, 0, vel_perturbada)

        return (
            pd.Series(vel_perturbada, index=self.n_estampa_df[1]["id_turbina"])
            .sort_index()
            .values
        )
