import unittest

import pandas as pd
import numpy as np

from utils.eolica.dataclasses_eolica import Aerogenerador
from utils.eolica.funciones_ordenamiento import Ordenamiento
from unittest.mock import patch, MagicMock 


class TestFuncionesOrdenamiento(unittest.TestCase):
    def setUp(self) -> None:
        self.df_aero_mock_1 = pd.DataFrame(
            {"DireccionViento": [71.5, 73.0, 75.8, 77.2]},
            index=["2008-01-01", "2008-02-01", "2008-03-01", "2008-04-01"],
        )
        self.n_estampas = 4
        self.instancia_ordenamiento = Ordenamiento()

        self.ordenamiento_instancia = Ordenamiento()
        self.aerogeneradores_con_df = {
            1: Aerogenerador(
                id_aero=1,
                id_torre="torre_1",
                latitud=12.29263,
                longitud=-71.22642,
                elevacion=1.0,
                modelo="Enercon E92/2.3MW",
                dist_pcc=None,
                df=self.df_aero_mock_1,
                f_ordenamiento=0,
            ),
            2: Aerogenerador(
                id_aero=2,
                id_torre="torre_1",
                latitud=12.28768,
                longitud=-71.22642,
                elevacion=2.0,
                modelo="Enercon E92/2.3MW",
                dist_pcc=None,
                df=self.df_aero_mock_1,
                f_ordenamiento=0,
            ),
        }

    def test_ordenamineto_vectorizado(self):
        resultado = self.instancia_ordenamiento.ordenamiento_vectorizado(
            self.aerogeneradores_con_df, self.n_estampas
        )

        for df in resultado.values():
            assert isinstance(df, pd.DataFrame)

        self.assertAlmostEqual(
            resultado["2008-03-01"]["factor_reordenamiento"][2], -533.597, places=3
        )

    def test_organizacion(self):
        lat1 = -550.41
        lon1 = 0.0
        tj_longitud = np.array([-71.22642, -71.22642])
        tj_latitud = np.array([12.29263, 12.28768])

        resultado_esperado = (
            np.array([-7770414.23629659, -7770414.23629659]),
            np.array([17490669.51853202, 17491219.93341891]),
        )

        resultado = self.instancia_ordenamiento._organizacion(
            lat1, lon1, tj_longitud, tj_latitud
        )

        np.testing.assert_almost_equal(resultado[0], resultado_esperado[0])
        np.testing.assert_almost_equal(resultado[1], resultado_esperado[1])

    @patch('utils.eolica.funciones_ordenamiento.Ordenamiento._recorrer_estampas')  # Mockear la función interna
    @patch('utils.eolica.funciones_ordenamiento.SparkSession')  # Mockear SparkSession
    def test_ordenamiento_vectorizado_pyspark(self, mock_spark_session, mock_recorrer_estampas):
        # Crear una instancia de Ordenamiento
        ordenamiento = Ordenamiento()

        # Crear mocks de los aerogeneradores
        mock_aerogenerador = MagicMock()
        mock_aerogenerador.id_aero = 1
        mock_aerogenerador.longitud = -58.0
        mock_aerogenerador.latitud = -34.0
        mock_aerogenerador.elevacion = 100.0
        mock_aerogenerador.df = MagicMock()
        mock_aerogenerador.df.select.return_value = MagicMock()

        aerogeneradores = {1: mock_aerogenerador}

        # Configurar el mock para el dataframe
        mock_dataframe = MagicMock()
        mock_dataframe.select.return_value.rdd.flatMap.return_value.collect.return_value = [45.0]

        mock_spark_session.createDataFrame.return_value = mock_dataframe

        # Mockear el comportamiento de _recorrer_estampas
        mock_recorrer_estampas.return_value = mock_dataframe

        # Llamar a la función ordenamiento_vectorizado_pyspark
        result = ordenamiento.ordenamiento_vectorizado_pyspark(aerogeneradores, n_estampas=1, ss=mock_spark_session)

        # Verificar los resultados
        mock_recorrer_estampas.assert_called_once()
        self.assertIsInstance(result, dict)
        #self.assertEqual(list(result.keys()), [45.0])  # Dirección de viento mockeada
        #self.assertEqual(result[45.0], mock_dataframe.collect())

    @patch('utils.eolica.funciones_ordenamiento.haversine')
    def test_organizacion(self, mock_haversine):
        ordenamiento = Ordenamiento()

        # Configurar mock para haversine
        mock_haversine.side_effect = [10.0, 20.0]

        lat_t1 = -34.0
        lon_t1 = -58.0
        tj_longitud = np.array([-58.1, -58.2])
        tj_latitud = np.array([-34.1, -34.2])

        # Llamar a la función _organizacion
        longitud_m, latitud_m = ordenamiento._organizacion(lat_t1, lon_t1, tj_longitud, tj_latitud)

        print(longitud_m, latitud_m)
        # Verificar que los cálculos sean correctos
        self.assertEqual(mock_haversine.call_count, 2)
        self.assertTrue(np.array_equal(longitud_m, np.array([-10000.0, -10000.0])))
        self.assertTrue(np.array_equal(latitud_m, np.array([-20000.0, -20000.0])))

    @patch('utils.eolica.funciones_ordenamiento.Ordenamiento._organizacion')
    def test_recorrer_estampas(self, mock_organizacion):
        ordenamiento = Ordenamiento()

        # Configura los mocks para latitudes y longitudes
        aux_latitud = np.array([-34.0, -34.1])
        aux_longitud = np.array([-58.0, -58.1])
        dir_promedio = [45.0]  # Dirección promedio mockeada

        # Mockear el DataFrame de parque reorganizado
        mock_parque_reorganizado = MagicMock()
        mock_parque_reorganizado.withColumn = MagicMock(return_value=mock_parque_reorganizado)
        mock_parque_reorganizado.orderBy = MagicMock(return_value=mock_parque_reorganizado)

        # Configurar mock para _organizacion
        mock_organizacion.return_value = (np.array([-10000.0, -10000.0]), np.array([-20000.0, -20000.0]))

        # Llamar a la función _recorrer_estampas
        result = ordenamiento._recorrer_estampas(0, aux_latitud, aux_longitud, dir_promedio, mock_parque_reorganizado)

        # Verificar que se llamó a _organizacion
        mock_organizacion.assert_called_once_with(
            lat_t1=aux_latitud[0],
            lon_t1=aux_longitud[0],
            tj_longitud=aux_longitud,
            tj_latitud=aux_latitud
        )

        # Verificar que las nuevas columnas fueron añadidas correctamente
        #mock_parque_reorganizado.withColumn.assert_any_call("longitud_m", MagicMock())
        #mock_parque_reorganizado.withColumn.assert_any_call("latitud_m", MagicMock())
        
        # Verificar que se llama a withColumn para theta_j
        theta_j = (90 - dir_promedio[0]) * (np.pi / 180)
        #mock_parque_reorganizado.withColumn.assert_any_call("theta_j", theta_j)

        # Verificar que se llama a withColumn para factor_reordenamiento
        self.assertTrue(mock_parque_reorganizado.withColumn.call_count >= 4)  # Se esperan al menos 4 llamadas a withColumn

        # Comprobar si el DataFrame fue ordenado correctamente
        mock_parque_reorganizado.orderBy.assert_called_once_with(mock_parque_reorganizado["factor_reordenamiento"].desc())
