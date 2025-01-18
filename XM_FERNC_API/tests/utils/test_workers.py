import unittest
import pytest
from unittest.mock import MagicMock, patch
from XM_FERNC_API.utils.workers import wrapper_efecto_estela_vectorizado, new_correcction
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType, DoubleType, ArrayType

from XM_FERNC_API.utils.eolica.caracterizacion_estela import Estela

from pyspark.sql import SparkSession
import pandas as pd

class TestCorreccionesWorker(unittest.TestCase):

    def mock_pandas_udf(arg1):

        keys = pd.Series([
            100.0,  # Altura promedio del buje en metros
            120.0,
        ])

        turbine_info = pd.Series([
            True,  # Indica si es un parque eólico offshore
            False,
        ])

        estructura_info = pd.Series([
            10.0,  # Altura de referencia o algún otro parámetro
            15.0,
        ])

        densidades = pd.Series([
            5.0,  # Otro parámetro de referencia
            7.0,

        ])
        # Mock que imita pandas_udf pero no hace la conversión
        def wrapper(func):
            def inner(*args, **kwargs):
                # Convertir pandas.Series a listas
                args = [pd.Series(arg) if isinstance(arg, list) else arg for arg in args]
                result = func(keys, turbine_info, estructura_info, densidades)
                # Convertir el resultado a listas, similar a pandas.Series
                return result
            return inner
        return wrapper
        
    @patch('XM_FERNC_API.utils.workers.pandas_udf', side_effect=mock_pandas_udf)
    @patch('XM_FERNC_API.utils.workers.efecto_estela_vectorizado_refactor')
    def test_wrapper_efecto_estela_vectorizado(self, mock_estela_vectorizado, mock_pandas_udf):
        
        offshore = True
        cre = 0.02
        caracteristicas_tij = MagicMock()
        densidad = MagicMock()
        dataset = MagicMock()
        n_turbinas = 3
        curvas_xarray = MagicMock()
        df_data = MagicMock()
        curvas_info = MagicMock()

        mock_result1 = MagicMock()
        mock_result1.result = ('2023-01-01', 'aero_1', 8.5)
        mock_result2 = MagicMock()
        mock_result2.result = ('2023-01-02', 'aero_2', 7.2)

        df_data.withColumn.return_value.select.return_value.collect.return_value = [
            mock_result1,
            mock_result2,
        ]

        resultado = wrapper_efecto_estela_vectorizado(
            offshore,
            cre,
            caracteristicas_tij,
            n_turbinas,
            df_data,
            curvas_info,
        )
        mock_estela_vectorizado.call_count == 2
        assert resultado[0][0] == '2023-01-01'
        
def mock_pandas_udf(arg1):
    fecha = pd.Series([
        pd.Timestamp('2023-01-01'),
        pd.Timestamp('2023-01-02'),
        pd.Timestamp('2023-01-03')
    ])

    ordenamiento = pd.Series([
        1,  # ID del aerogenerador o alguna otra representación
        2,
        3
    ])

    h_buje_promedio = pd.Series([
        100.0,  # Altura promedio del buje en metros
        120.0,
        110.0
    ])

    offshore = pd.Series([
        True,  # Indica si es un parque eólico offshore
        False,
        True
    ])

    z_o1 = pd.Series([
        10.0,  # Altura de referencia o algún otro parámetro
        15.0,
        12.0
    ])

    z_o2 = pd.Series([
        5.0,  # Otro parámetro de referencia
        7.0,
        6.0
    ])
    # Mock que imita pandas_udf pero no hace la conversión
    def wrapper(func):
        def inner(*args, **kwargs):
            # Convertir pandas.Series a listas
            args = [pd.Series(arg) if isinstance(arg, list) else arg for arg in args]
            result = func(fecha, ordenamiento, h_buje_promedio, z_o1, z_o2)
            # Convertir el resultado a listas, similar a pandas.Series
            return result
        return inner
    return wrapper

# Test principal

@patch('XM_FERNC_API.utils.workers.correccion_velocidad_parque_eolico_solo')
@patch('XM_FERNC_API.utils.workers.pandas_udf', side_effect=mock_pandas_udf)
def test_new_correction(mock_pandas_udf, mock_correccion):

    args_list_df_mock = MagicMock()
    aerogeneradores_broadcast_mock = MagicMock()
    modelos_broadcast_mock = MagicMock()

    mock_correccion.return_value = [(8.5, 'aero_1')]

    args_list_df_mock.withColumn.return_value.select.return_value.collect.return_value = [
            ('2023-01-01', 'aero_1', 8.5),
            ('2023-01-02', 'aero_2', 7.2),
        ]

    # Ejecutar la función con el DataFrame mockeado
    result = new_correcction(args_list_df_mock, aerogeneradores_broadcast_mock, modelos_broadcast_mock)

    # Asegurarse de que la función fue llamada dos veces
    assert mock_correccion.call_count == 3

    # Verificar que el resultado final es el esperado
    assert len(result) == 2
    assert result[0] == ('2023-01-01', 'aero_1', 8.5)
    assert result[1] == ('2023-01-02', 'aero_2', 7.2)
