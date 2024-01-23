import pandas as pd
import polars as pl
import numpy as np

from typing import Dict

from utils.manipulador_dataframe import ManipuladorDataframe


class CalculoTempPresionDensidad:
    def __init__(self) -> None:
        self.manipulador_df = ManipuladorDataframe()

    def calculo_temperatura_presion_densidad(
        self,
        modelos: Dict,
        aerogeneradores: Dict,
        torres: Dict | None = None,
        dataframe: pl.DataFrame | None = None,
    ) -> Dict:
        """
        Calcula la temperatura, presión y densidad del aire ajustadas en función de la altura del buje de los aerogeneradores o las torres asociadas.

        Parámetros:
        - modelos (Dict): Diccionario que contiene información sobre los modelos de aerogeneradores, donde las claves son identificadores únicos y los valores son objetos que representan las características de los modelos.
        - aerogeneradores (Dict): Diccionario que contiene información sobre los aerogeneradores, donde las claves son identificadores únicos y los valores son objetos que representan las características de los aerogeneradores.
        - torres (Dict, opcional): Diccionario que contiene información sobre las torres asociadas a los aerogeneradores, donde las claves son identificadores únicos y los valores son objetos que representan las características de las torres. Si se proporciona, se ajusta la temperatura, presión y densidad del aire específicamente para cada torre.
        - dataframe (pd.DataFrame, opcional): DataFrame que contiene datos meteorológicos, incluyendo temperatura y presión. Si se proporciona, se ajustan los valores en este DataFrame.

        Retorna:
        - Dict: Diccionario que contiene los resultados del cálculo. Si se proporcionan torres, se actualizan los DataFrames asociados a cada torre. Si se proporciona un DataFrame, se retorna un nuevo DataFrame ajustado. En ambos casos, el resultado incluye las columnas calculadas de temperatura, presión y densidad del aire.

        """
        if torres != None:
            for aero in aerogeneradores.values():
                resultado = []
                torre = torres[aero.id_torre]
                caracteristicas = modelos[aero.modelo]
                valores_anemometro = [
                    anemometro.AlturaAnemometro
                    for anemometro in torre.conf_anemometro
                ]
                altura_anemometro = min(
                    valores_anemometro,
                    key=lambda x: abs(x - caracteristicas.altura_buje),
                )
                df = torres[aero.id_torre].dataframe.copy()
                h_buje = caracteristicas.altura_buje
                h_ta = altura_anemometro
                if h_ta != h_buje:
                    df = self.obtener_calculo_pvapor_densidad_con_buje_anemometro(
                        df, h_buje, h_ta
                    )
                    torres[aero.id_torre].dataframe = df
                else:
                    df = self.obtener_calculo_pvapor_densidad(df)
                    torres[aero.id_torre].dataframe = df
            return torres

        resultado = {}
        dataframe = self.manipulador_df.ajustar_df_eolica(dataframe)
        dataframe = self.obtener_calculo_pvapor_densidad(dataframe)
        resultado["dataframe"] = dataframe
        return resultado

    def obtener_calculo_pvapor_densidad(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula la presión de vapor y la densidad del aire en función de la temperatura y la presión atmosférica.

        Parámetros:
        - df (pd.DataFrame): DataFrame que contiene datos meteorológicos, incluyendo temperatura (Ta) y presión atmosférica (PresionAtmosferica).

        Retorna:
        - pd.DataFrame: DataFrame actualizado que incluye las columnas adicionales de presión de vapor (PVapor), presión de vapor de saturación (PVaporSaturacion) y densidad del aire en el buje (DenBuje).

        """
        df["PVapor"] = df["Ta"].apply(
            lambda x: 0.0000205 * np.exp(0.0631846 * (x + 273.15))
        )
        df["PVaporSaturacion"] = df["Ta"].apply(
            lambda x: (6.112 * np.exp((17.62 * x) / (x + 243.5))) * 100
        )
        df["DenBuje"] = (1 / (df["Ta"] + 273.15)) * (
            ((df["PresionAtmosferica"] * 100) / 287.058)
            - (
                ((df["PVapor"] ** 2) / df["PVaporSaturacion"])
                * ((1 / 287.058) - (1 / 461.5))
            )
        )

        return df

    def obtener_calculo_pvapor_densidad_con_buje_anemometro(
        self, df: pd.DataFrame, h_buje: float, h_ta: float
    ) -> pd.DataFrame:
        """
        Calcula la temperatura ajustada en la altura del buje, la presión ajustada en la altura del buje y recalcula la presión de vapor y la densidad del aire en función de la temperatura ajustada.

        Parámetros:
        - df (pd.DataFrame): DataFrame que contiene datos meteorológicos, incluyendo temperatura (Ta) y presión atmosférica (PresionAtmosferica).
        - h_buje (float): Altura del buje del aerogenerador.
        - h_ta (float): Altura de los anemómetros en la torre.

        Retorna:
        - pd.DataFrame: DataFrame actualizado que incluye las columnas adicionales de temperatura ajustada en la altura del buje (TaBuje), presión ajustada en la altura del buje (Pbuje), presión de vapor (PVapor), presión de vapor de saturación (PVaporSaturacion) y densidad del aire en el buje (DenBuje).

        """
        df["TaBuje"] = df["Ta"].apply(
            lambda x: (x + 273.15) - (6.5 * ((h_buje - h_ta) / 1000)) - 273.15
        )
        df["Pbuje"] = (
            df["PresionAtmosferica"]
            * ((df["TaBuje"] + 283.15) / (df["Ta"] + 283.15)) ** 5.26
        )
        df["PVapor"] = df["TaBuje"].apply(
            lambda x: 0.0000205 * np.exp(0.0631846 * (x + 273.15))
        )
        df["PVaporSaturacion"] = df["TaBuje"].apply(
            lambda x: (6.112 * np.exp((17.62 * x) / (x + 243.5))) * 100
        )
        df["DenBuje"] = (1 / (df["TaBuje"] + 273.15)) * (
            ((df["PresionAtmosferica"] * 100) / 287.058)
            - (
                ((df["PVapor"] ** 2) / df["PVaporSaturacion"])
                * ((1 / 287.058) - (1 / 461.5))
            )
        )

        return df
