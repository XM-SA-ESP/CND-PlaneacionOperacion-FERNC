import unittest
import pandas as pd
import numpy as np
import polars as pl
import pytest
from infraestructura.models.eolica.parametros import (
    ConfiguracionAnemometro,
    CurvasDelFabricante,
)
from utils.eolica.dataclasses_eolica import Aerogenerador, Modelo, Torre

from utils.eolica.funciones_calculo_temp_presion_densidad import (
    CalculoTempPresionDensidad,
)


class TestCalculoTempPresionDensidad(unittest.TestCase):
    def setUp(self):
        self.calculo_temp_presion_densidad = CalculoTempPresionDensidad()

        data = "./tests/data/test_dataframe.parquet"
        self.df_pl = pl.read_parquet(data)

    def test_obtener_calculo_pvapor_densidad(self):
        # Crear un DataFrame de prueba
        df = pd.DataFrame(
            {"Ta": [20.0, 25.0, 30.0], "PresionAtmosferica": [1013.25, 1010.0, 1005.0]}
        )

        result_df = self.calculo_temp_presion_densidad.obtener_calculo_pvapor_densidad(
            df
        )

        # Asegurarse de que el DataFrame resultante tiene las columnas esperadas
        assert "PVapor" in result_df.columns
        assert "PVaporSaturacion" in result_df.columns
        assert "DenBuje" in result_df.columns

    def test_calculo_temperatura_presion_densidad(self):
        df_torres = pd.DataFrame(
            {
                "DireccionViento": [75.25, 78.42, 76.89],
                "PresionAtmosferica": [990.62, 990.62, 990.62],
                "Ta": [28.11, 27.51, 26.88],
                "VelocidadViento": [8.66, 9.73, 9.62],
            },
            index=[
                "2008-01-01 0:00:00+00:00",
                "2008-01-01 02:00:00+00:00",
                "2008-01-01 03:00:00+00:00",
            ],
        )

        df_torres.index = pd.to_datetime(df_torres.index)

        torres = {
            "torre_1": Torre(
                id="torre_1",
                latitud=12.23587,
                longitud=-7123587,
                elevacion=0.0,
                radio_r=10.0,
                conf_anemometro=[
                    ConfiguracionAnemometro(Anemometro=1, AlturaAnemometro=20.0),
                    ConfiguracionAnemometro(Anemometro=2, AlturaAnemometro=40.0),
                    ConfiguracionAnemometro(Anemometro=3, AlturaAnemometro=60.0),
                ],
                archivo_series="nombre _archivo",
                dataframe=df_torres,
            )
        }

        columnas_expect = [
            "DireccionViento",
            "PresionAtmosferica",
            "Ta",
            "VelocidadViento",
            "PVapor",
            "PVaporSaturacion",
            "DenBuje",
        ]

        result = (
            self.calculo_temp_presion_densidad.calculo_temperatura_presion_densidad(
                torres
            )
        )

        columnas_result = result["torre_1"].dataframe.columns.tolist()

        for col in columnas_expect:
            self.assertIn(col, columnas_result)
