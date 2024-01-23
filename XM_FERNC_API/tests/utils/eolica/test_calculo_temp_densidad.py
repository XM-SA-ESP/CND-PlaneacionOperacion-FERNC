import unittest
import pandas as pd
import numpy as np
import polars as pl
import pytest
from infraestructura.models.eolica.parametros import ConfiguracionAnemometro, CurvasDelFabricante
from utils.eolica.dataclasses_eolica import Aerogenerador, Modelo, Torre

from utils.eolica.funciones_calculo_temp_presion_densidad import CalculoTempPresionDensidad


class TestCalculoTempPresionDensidad(unittest.TestCase):

    def setUp(self):
        self.calculo_temp_presion_densidad = CalculoTempPresionDensidad()

        data = "./tests/data/test_dataframe.parquet"
        self.df_pl = pl.read_parquet(data)

    def test_obtener_calculo_pvapor_densidad(self):
        # Crear un DataFrame de prueba
        df = pd.DataFrame({
            "Ta": [20.0, 25.0, 30.0],
            "PresionAtmosferica": [1013.25, 1010.0, 1005.0]
        })

        result_df = self.calculo_temp_presion_densidad.obtener_calculo_pvapor_densidad(
            df)

        # Asegurarse de que el DataFrame resultante tiene las columnas esperadas
        assert "PVapor" in result_df.columns
        assert "PVaporSaturacion" in result_df.columns
        assert "DenBuje" in result_df.columns

    def test_calculo_temperatura_presion_densidad_with_torres(self):
        modelos = {
            "Enercon E92/2.3MW": Modelo(
                nombre="Enercon E92/2.3MW0", altura_buje=98.0, diametro_rotor=92.8, p_nominal=2350.0, v_nominal=14.0, den_nominal=1.23, v_min=2.0, v_max=25.0, t_min=-10.0, t_max=45.0, curvas_fabricante=[
                    CurvasDelFabricante(
                        SerieVelocidad=1.0, SeriePotencia=0.0, SerieCoeficiente=0.0, SerieVcthCorregida=0),
                    CurvasDelFabricante(
                        SerieVelocidad=2.0, SeriePotencia=3.6, SerieCoeficiente=1.0, SerieVcthCorregida=0)
                ])
        }
        aerogeneradores = {1: Aerogenerador(id_aero=1, id_torre='torre_1', latitud=12.29263, longitud=-71.22642, elevacion=1.0, modelo='Enercon E92/2.3MW', dist_pcc=None, df=None, f_ordenamiento=0),
                        2: Aerogenerador(id_aero=1, id_torre='torre_1', latitud=12.29263, longitud=-71.22642, elevacion=1.0, modelo='Enercon E92/2.3MW', dist_pcc=None, df=None, f_ordenamiento=0)
                        }

        df_torres = pd.DataFrame({
            "DireccionViento": [
                75.25, 78.42, 76.89
            ], "PresionAtmosferica": [
                990.62, 990.62, 990.62
            ], "Ta": [
                28.11, 27.51, 26.88
            ], "VelocidadViento": [
                8.66, 9.73, 9.62
            ]
        }, index=["2008-01-01 0:00:00+00:00", "2008-01-01 02:00:00+00:00", "2008-01-01 03:00:00+00:00"], )

        df_torres.index = pd.to_datetime(df_torres.index)

        torres = {"torre_1": Torre(
            id="torre_1", latitud=12.23587, longitud=-7123587, elevacion=0.0, radio_r=10.0, conf_anemometro=[ConfiguracionAnemometro(
                Anemometro=1, AlturaAnemometro=20.0),
                ConfiguracionAnemometro(
                Anemometro=2, AlturaAnemometro=40.0),
                ConfiguracionAnemometro(
                Anemometro=3, AlturaAnemometro=60.0)], archivo_series="nombre _archivo", dataframe=df_torres
        )}

        columnas_expect = ["DireccionViento", "PresionAtmosferica", "Ta", "VelocidadViento",
                           "TaBuje", "Pbuje", "PVapor", "PVaporSaturacion", "DenBuje"]

        result = self.calculo_temp_presion_densidad.calculo_temperatura_presion_densidad(
            modelos, aerogeneradores, torres)

        columnas_result = result['torre_1'].dataframe.columns.tolist()

        for col in columnas_expect:
            self.assertIn(col, columnas_result)

    def test_obtener_calculo_pvapor_densidad_con_buje_anemometro(self):

        df_torres = pd.DataFrame({
            "DireccionViento": [
                75.25, 78.42, 76.89
            ], "PresionAtmosferica": [
                990.62, 990.62, 990.62
            ], "Ta": [
                28.11, 27.51, 26.88
            ], "VelocidadViento": [
                8.66, 9.73, 9.62
            ]
        }, index=["2008-01-01 0:00:00+00:00", "2008-01-01 02:00:00+00:00", "2008-01-01 03:00:00+00:00"], )

        df_torres.index = pd.to_datetime(df_torres.index)

        result_df = self.calculo_temp_presion_densidad.obtener_calculo_pvapor_densidad_con_buje_anemometro(
            df_torres, 100.0, 80.0)

        expected_df = pd.DataFrame({
            "DireccionViento": [75.25, 78.42, 76.89],
            "PresionAtmosferica": [990.62, 990.62, 990.62],
            "Ta": [28.11, 27.51, 26.88],
            "VelocidadViento": [8.66, 9.73, 9.62],
            "TaBuje": [27.98, 27.38, 26.75],
            "Pbuje": [988.4456646529, 988.4414689457, 988.4370459906],
            "PVapor": [3758.1907090835, 3618.3817199489, 3477.1764141461],
            "PVaporSaturacion": [3757.1799555829, 3627.931883521, 3496.4188680899],
            "DenBuje": [1.1295587332, 1.1324726019, 1.135513778],

        }, index=["2008-01-01 0:00:00+00:00", "2008-01-01 02:00:00+00:00", "2008-01-01 03:00:00+00:00"], )

        expected_df.index = pd.to_datetime(expected_df.index)

        pd.testing.assert_frame_equal(result_df, expected_df)
