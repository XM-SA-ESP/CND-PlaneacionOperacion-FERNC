import pandas as pd
import polars as pl
import numpy as np
from typing import Dict
from XM_FERNC_API.utils.manipulador_dataframe import ManipuladorDataframe
from pyspark.sql.functions import col, exp, lit
from pyspark.sql import DataFrame

class CalculoTempPresionDensidad:
    def __init__(self) -> None:
        self.manipulador_df = ManipuladorDataframe()

    def calculo_temperatura_presion_densidad(
        self,
        torres: Dict | None = None,
        dataframe: DataFrame | None = None,
    ) -> Dict:
        """
        Calcula la temperatura, presión y densidad del aire ajustadas en función de la altura del buje de los aerogeneradores o las torres asociadas.

        Parámetros:
        - aerogeneradores (Dict): Diccionario que contiene información sobre los aerogeneradores, donde las claves son identificadores únicos y los valores son objetos que representan las características de los aerogeneradores.
        - torres (Dict, opcional): Diccionario que contiene información sobre las torres asociadas a los aerogeneradores, donde las claves son identificadores únicos y los valores son objetos que representan las características de las torres. Si se proporciona, se ajusta la temperatura, presión y densidad del aire específicamente para cada torre.
        - dataframe (pd.DataFrame, opcional): DataFrame que contiene datos meteorológicos, incluyendo temperatura y presión. Si se proporciona, se ajustan los valores en este DataFrame.

        Retorna:
        - Dict: Diccionario que contiene los resultados del cálculo. Si se proporcionan torres, se actualizan los DataFrames asociados a cada torre. Si se proporciona un DataFrame, se retorna un nuevo DataFrame ajustado. En ambos casos, el resultado incluye las columnas calculadas de temperatura, presión y densidad del aire.

        """
        if torres != None:
            for torre in torres.values():
                torre.dataframe = self.obtener_calculo_pvapor_densidad(torre.dataframe)
            return torres

        resultado = {}
        dataframe = self.manipulador_df.ajustar_df_eolica(dataframe)
        dataframe = self.obtener_calculo_pvapor_densidad(dataframe)
        resultado["dataframe"] = dataframe
        return resultado

    def obtener_calculo_pvapor_densidad(self, df: DataFrame) -> pd.DataFrame:
        """
        Calcula la presión de vapor y la densidad del aire en función de la temperatura y la presión atmosférica.

        Parámetros:
        - df (pd.DataFrame): DataFrame que contiene datos meteorológicos, incluyendo temperatura (Ta) y presión atmosférica (PresionAtmosferica).

        Retorna:
        - pd.DataFrame: DataFrame actualizado que incluye las columnas adicionales de presión de vapor (PVapor), presión de vapor de saturación (PVaporSaturacion) y densidad del aire en el buje (DenBuje).

        """
        if isinstance(df, pd.DataFrame):
            df["PVapor"] = df["Ta"].apply(lambda x: 0.0000205 * np.exp(0.0631846 * (x + 273.15))
            )
            df["PVaporSaturacion"] = df["Ta"].apply(lambda x: (6.112 * np.exp((17.62 * x) / (x + 243.5))) * 100)
            df["DenBuje"] = (1 / (df["Ta"] + 273.15)) * (
                ((df["PresionAtmosferica"] * 100) / 287.058)
                - (
                    ((df["PVapor"] ** 2) / df["PVaporSaturacion"])
                    * ((1 / 287.058) - (1 / 461.5))
                )
            )
        else:            
            df = df.withColumn("PVapor", lit(0.0000205) * exp(lit(0.0631846) * (col("Ta") + lit(273.15))))                        
            df = df.withColumn("PVaporSaturacion", (lit(6.112) * exp((lit(17.62) * col("Ta")) / (col("Ta") + lit(243.5)))) * lit(100))                        

            df = df.withColumn("DenBuje", 
                            (lit(1) / (col("Ta") + lit(273.15))) * (
                                ((col("PresionAtmosferica") * lit(100)) / lit(287.058)) 
                                - (
                                    ((col("PVapor") ** lit(2)) / col("PVaporSaturacion"))
                                    * ((lit(1) / lit(287.058)) - (lit(1) / lit(461.5)))
                                )
                            )
            )

        return df
