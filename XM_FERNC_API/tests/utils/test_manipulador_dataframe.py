import unittest
from unittest import mock
import numpy as np
import pandas as pd
import polars as pl
import pandas.testing as pdt

from unittest.mock import patch
from infraestructura.models.eolica.parametros import ParametrosTransversales

from utils.manipulador_dataframe import ManipuladorDataframe
from infraestructura.models.respuesta import Resultado


class TestManipuladorDataframe(unittest.TestCase):
    def setUp(self) -> None:
        data = "./tests/data/test_dataframe.parquet"
        self.df_pd = pd.read_parquet(data)
        self.manipulador_df_instancia = ManipuladorDataframe()
        self.mock_series = pd.read_excel(
            "./tests/data/test_series_tiempo.xlsx", index_col=0
        )
        self.mock_solpos = pd.read_excel(
            "./tests/data/test_angulo_zenital.xlsx", index_col=0
        )
        self.mock_iext = pd.read_excel(
            "./tests/data/test_iext.xlsx", index_col=0)
        self.mock_dni_dhi = pd.read_excel(
            "./tests/data/test_serie_dni_dhi.xlsx", index_col=0
        )
        self.mock_calculo_df = pd.read_excel(
            "./tests/data/test_data_result_calculo_dni.xlsx", index_col=0
        )
        self.mock_df_combinado = pd.read_csv(
            "./tests/data/test_df_combinado_.csv", index_col=0,
        )

    def test_crear_df_calculo_dni(self):
        """
        Prueba el método 'crear_df_calculo_dni' de la clase ServicioSolar.

        Parámetros:
            self: La instancia de la clase de prueba que contiene el método de prueba.

        Retorna:
            None
        """

        solpos = self.mock_solpos
        iext = self.mock_iext
        resultado_esperado = self.mock_calculo_df
        resultado_esperado.GHI = resultado_esperado.GHI.astype(float)

        # Invocacion del metodo __crear_df_calculo_dni
        resultado = self.manipulador_df_instancia.crear_df_calculo_dni(
            solpos, iext, self.df_pd
        )

        # assert_frame_equal entre el resultado y el df esperado
        pdt.assert_frame_equal(resultado, resultado_esperado)

    def test_combinar_dataframes(self):
        # Create mock input dataframes
        mock_series_dni_dhi = self.mock_dni_dhi
        mock_solpos = self.mock_solpos
        mock_iext = self.mock_iext

        resultado_esperado = self.mock_df_combinado

        # Llamado al metodo
        resultado = self.manipulador_df_instancia.combinar_dataframes(
            mock_series_dni_dhi, mock_solpos, mock_iext
        )

        print(resultado.head(12))
        print(resultado_esperado.head(12))

        # assert_frame_equal entre el resultado y el df esperado
        pdt.assert_frame_equal(resultado, resultado_esperado)

    def test_crear_serie_doy(self):
        """
        Esta función se utiliza para probar el método 'crear_serie_doy' de la clase 'ServicioSolar'.

        Parámetros:
            self: La instancia de la clase de prueba que contiene el método de prueba.

        Retorna:
            None

        Pasos de prueba:
        1. Cargar el archivo parquet con el resultado esperado.
        2. Invocar el método '__crear_serie_doy' de la clase 'ServicioSolar' con el parámetro 'df_pd'.
        3. Convertir el 'resultado' de DatetimeIndex a DataFrame.
        4. Comparar el DataFrame 'resultado' con el DataFrame 'resultado_series' usando la función 'assert_frame_equal' del módulo 'pandas.testing'.
        """

        # Carga archivo parquet con resultado esperado
        resultado_series = self.mock_series

        # Invocacion del metodo __crear_columna_doy
        resultado = self.manipulador_df_instancia.crear_serie_doy(
            self.df_pd, "America/Bogota"
        )

        # Conversion de DatetimeIndex a Dataframe para que pueda ser probado
        resultado = pd.DataFrame(resultado, columns=["series"])
        # Convercion a string para hacer la comparacion
        resultado["series"] = resultado["series"].astype(str)

        # assert_frame_equal entre el resultado y el df esperado
        pdt.assert_frame_equal(resultado, resultado_series)

    def test_filtrar_dataframe(self):
        df = pd.DataFrame(
            {
                "dni": [0, 100, 0, 0],
                "dhi": [0, 0, 50, 0],
            },
            index=pd.to_datetime(
                ["06:00", "09:00", "12:00", "18:00"], format="%H:%M"
            ).tz_localize("America/Bogota"),
        )

        # Expected result
        expected_df = pd.DataFrame(
            {"dni": [100, 0], "dhi": [0, 50]},
            index=pd.to_datetime(["09:00", "12:00"], format="%H:%M").tz_localize(
                "America/Bogota"
            ),
        )

        # Call the method
        result_df = self.manipulador_df_instancia.filtrar_dataframe(df)

        # Assert the result
        pd.testing.assert_frame_equal(result_df, expected_df)

    def test_restaurar_dataframe(self):
        inversores_resultados = {
            "data": {
                "POA": pd.DataFrame(
                    {"poa": [1, 2, 3]},
                    index=pd.to_datetime(
                        ["09:00", "12:00", "18:00"], format="%H:%M"
                    ).tz_localize("America/Bogota"),
                ),
            },
        }
        mock_series_df = pd.DataFrame(
            {"poa": [1, 2, 3], "Ta": [1, 2, 3]},
            index=pd.to_datetime(
                ["09:00", "12:00", "18:00"], format="%H:%M"
            ).tz_localize("America/Bogota"),
        )

        expected_df = pd.DataFrame(
            {"poa": [1.0, 2.0, 3.0], "Ta": [1.0, 2.0, 3.0]},
            index=pd.to_datetime(
                ["09:00", "12:00", "18:00"], format="%H:%M"
            ).tz_localize("America/Bogota"),
        )

        self.manipulador_df_instancia.restaurar_dataframe(
            mock_series_df, inversores_resultados
        )

        pdt.assert_frame_equal(
            inversores_resultados["data"]["POA"], expected_df)

    def test_filtrar_por_mes(self):
        # Datos de prueba
        """
        Enero tiene 31 días, por lo que la suma sería 0 + 1 + 2 + … + 30 0+1+2+…+30
        Febrero tiene 28 días (2023 no es un año bisiesto), por lo que la suma sería 31 + 32 + … + 58 31+32+…+58
        Marzo tiene 31 días, por lo que la suma sería 59 + 60 + … + 89 59+60+…+89

        Las sumas para cada mes son:

        Enero: 465
        Febrero: 1246
        Marzo: 2294
        """
        rng = pd.date_range("2023-01-01", periods=90,
                            freq="D", tz="America/Bogota")
        serie_energia = pd.Series(range(90), index=rng)

        # Invocar el método filtrar_por_mes
        resultado = self.manipulador_df_instancia.filtrar_por_mes(
            serie_energia)

        # Convertir el índice DatetimeIndex de "resultado" en PeriodIndex
        resultado.index = resultado.index.to_period("M")

        # Resultado esperado: La suma de los números del 0 al 30 es 435, del 31 al 59 es 1245, y del 60 al 89 es 3725.
        resultado_esperado = pd.Series(
            [465, 1246, 2294],
            index=pd.PeriodIndex(["2023-01", "2023-02", "2023-03"], freq="M"),
        )

        # Verificar si el resultado coincide con el esperado
        pd.testing.assert_series_equal(resultado, resultado_esperado)

    def test_filtrar_por_dia(self):
        # Datos de prueba
        energia_mensual = pd.Series(
            {
                "2023-01": 1000,
                "2023-02": 900,
                "2023-03": 1200,
            }
        )

        resultado_df = self.manipulador_df_instancia.filtrar_por_dia(
            energia_mensual)
        # Validación del índice
        assert all(
            isinstance(item, pd.Timestamp) for item in resultado_df.index
        ), "El índice no está en formato datetime."

        # Resultados esperados
        energia_diaria_esperada = pd.Series(
            {
                "2023-01": round((1000 / 31), 2),
                "2023-02": round((900 / 28), 2),
                "2023-03": round((1200 / 31), 2),
            }
        )
        energia_diaria_esperada.index = pd.to_datetime(
            energia_diaria_esperada.index, format="%Y-%m"
        )
        df_esperado = pd.DataFrame(
            {"mensual": energia_mensual, "diaria": energia_diaria_esperada}
        )
        # Verificación
        pd.testing.assert_frame_equal(
            resultado_df, df_esperado, check_exact=False)

    # def test_calcular_eda(self):
    #     # Datos de prueba

    #     parametros_tranversales = ParametrosTransversales(
    #         NombrePlanta="TestPlant",
    #         Cen=2,
    #         Ihf=87,
    #         Kpc=1,
    #         Kt=1,
    #         Kin=1,
    #         Latitud=45,
    #         Longitud=45,
    #         InformacionMedida=True,
    #         Offshore=True,
    #         Elevacion=0.3,
    #         Voltaje=0.3,
    #         Ppi=11.0
    #     )

    #     df_em = pd.DataFrame({
    #         'diaria': [15.0, 20.0, 18.0],
    #     }, index=[
    #         "2008-01-01 01:00:00-05:00", 
    #         "2008-01-01 02:00:00-05:00",
    #         "2008-01-01 03:00:00-05:00"
    #     ])
    #     df_em = df_em[~df_em.index.duplicated(keep='first')]

    #     enficc = Resultado(anio=2008, Mes=3, Valor=100)

    #     # Invocar el método calcular_eda
    #     resultados = self.manipulador_df_instancia.calcular_eda(
    #         parametros_tranversales, df_em, enficc)

    #     # Resultados esperados (puedes ajustar estos valores)
    #     esperado = [
    #         Resultado(anio=2022, Mes=12, Valor="N/A"),
    #         Resultado(anio=2023, Mes=1, Valor=900.0),  # 1000 - 100
    #         Resultado(anio=2023, Mes=2, Valor=800.0),  # 900 - 100
    #         Resultado(anio=2023, Mes=3, Valor=1100.0),  # 1200 - 100
    #         Resultado(anio=2023, Mes=4, Valor="N/A"),
    #         Resultado(anio=2023, Mes=5, Valor="N/A"),
    #         Resultado(anio=2023, Mes=6, Valor="N/A"),
    #         Resultado(anio=2023, Mes=7, Valor="N/A"),
    #         Resultado(anio=2023, Mes=8, Valor="N/A"),
    #         Resultado(anio=2023, Mes=9, Valor="N/A"),
    #         Resultado(anio=2023, Mes=10, Valor="N/A"),
    #         Resultado(anio=2023, Mes=11, Valor="N/A"),
    #     ]

    #     # Verificación
    #     self.assertEqual(resultados, esperado)

    @patch('utils.manipulador_dataframe.ManipuladorDataframe.crear_serie_doy')
    def test_ajustar_df_eolica(self, mock_crear_serie_doy):

        data = {
            'DireccionViento': ['45.5', '60.2', '75.7'],
            'PresionAtmosferica': ['1013.2', '1012.7', '1014.0'],
            'Ta': ['25.0', '26.5', '24.8'],
            'VelocidadViento': ['8.2', '7.6', '9.1'],
        }
        df = pl.DataFrame(data)

        mock_crear_serie_doy.return_value = pd.date_range(
            start='2023-01-01', periods=3, freq='H')

        adjusted_df = self.manipulador_df_instancia.ajustar_df_eolica(df)

        expected_data = {
            'DireccionViento': [45.5, 60.2, 75.7],
            'PresionAtmosferica': [1013.2, 1012.7, 1014.0],
            'Ta': [25.0, 26.5, 24.8],
            'VelocidadViento': [8.2, 7.6, 9.1],
        }
        expected_index = pd.date_range(start='2023-01-01', periods=3, freq='H')
        expected_df = pd.DataFrame(expected_data, index=expected_index)

        pd.testing.assert_frame_equal(adjusted_df, expected_df)

    def test_transform_energia_planta(self):
        energia_planta = pd.DataFrame({'Energía [Kwh]': [100, 150, 120]}, index=pd.date_range(
            start='2023-01-01', periods=3, freq='H'))
        transformed_df = self.manipulador_df_instancia.transform_energia_planta(
            energia_planta)
        expected_df = pd.DataFrame({
            'Año': [2023, 2023, 2023],
            'Mes': [1, 1, 1],
            'Día': [1, 1, 1],
            'Hora': [0, 1, 2],
            'Energía [Kwh]': [100, 150, 120],
        }).astype({'Año': int, 'Mes': int, 'Día': int, 'Hora': int})

        pd.testing.assert_frame_equal(transformed_df, expected_df)

    def test_transform_energia_mes(self):
        energia_mes = pd.DataFrame({'Energía [Kwh/mes]': [500, 600, 550]}, index=pd.date_range(
            start='2023-01-01', periods=3, freq='M'))
        transformed_df = self.manipulador_df_instancia.transform_energia_mes(
            energia_mes)
        expected_df = pd.DataFrame({
            'Año': [2023, 2023, 2023],
            'Mes': [1, 2, 3],
            'Energía [Kwh/mes]': [500, 600, 550],
        }).astype({'Año': int, 'Mes': int})

        pd.testing.assert_frame_equal(transformed_df, expected_df)

    def test_transform_energia_diaria(self):
        energia_diaria = pd.DataFrame({
            'diaria': [15.0, 20.0, 18.0],
            'mensual': [1, 1, 1],
        }, index=pd.date_range(start='2023-01-01', periods=3, freq='D'))
        transformed_df = self.manipulador_df_instancia.transform_energia_diaria(
            energia_diaria)
        expected_df = pd.DataFrame({
            'Año': [2023, 2023, 2023],
            'Mes': [1, 1, 1],
            'Em [kWh/día]': [15.0, 20.0, 18.0],
        }).astype({'Año': int, 'Mes': int})

        pd.testing.assert_frame_equal(transformed_df, expected_df)

    def test_transform_enficc(self):
        enficc = Resultado(anio=2023, mes=1, valor=100)
        transformed_df = self.manipulador_df_instancia.transform_enficc(enficc)
        expected_df = pd.DataFrame({
            'Año': [2023],
            'Mes': [1],
            'ENFICC [kWh/día]': [100],
        })

        pd.testing.assert_frame_equal(transformed_df, expected_df)

    def test_transform_eda(self):
        eda_results = [
            Resultado(anio=2023, mes=1, valor=15),
            Resultado(anio=2023, mes=2, valor=10),
            Resultado(anio=2023, mes=3, valor=20),
        ]
        transformed_df = self.manipulador_df_instancia.transform_eda(
            eda_results)
        expected_df = pd.DataFrame({
            'Año': [2023, 2023, 2023],
            'Mes': [1, 2, 3],
            'EDA [kWh/día]': [15, 10, 20],
        }).astype({'Año': int, 'Mes': int})

        pd.testing.assert_frame_equal(transformed_df, expected_df)
