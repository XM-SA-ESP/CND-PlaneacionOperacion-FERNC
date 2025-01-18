import unittest
import pandas as pd
import xarray as xr
import numpy as np

from unittest.mock import MagicMock, patch

from utils.eolica import ajuste_potencia
from utils.eolica.ajuste_potencia import potencia_vectorizado_udf, calcular_potencia, calculate_pot
from utils.estructura_xarray import crear_estructura_xarray_vectorizado
from utils.eolica.dataclasses_eolica import Aerogenerador

class TestAjustePotencia(unittest.TestCase):
    def setUp(self):
        self.serie_tiempo = pd.date_range(start="2021-01-01", periods=3, freq="D")
        test_dataframe = pd.DataFrame({
            "VelocidadViento": [8.25, 8.1, 7.98],
            "DireccionViento": [75, 77, 78],
            "Ta": [10, 20, 30],
            "DenBuje": [1.1, 1.05, 1.6]
        })
        test_dataframe.index = self.serie_tiempo
        aero1 = Aerogenerador(
            id_torre="torre1",
            id_aero=1,
            latitud=12.29263,
            longitud=-71.226417,
            elevacion=1,
            modelo="enercon",
            df=test_dataframe,
        )
        aero2 = Aerogenerador(
            id_torre="torre1",
            id_aero=2,
            latitud=12.287679,
            longitud=-71.226417,
            elevacion=2,
            modelo="enercon",
            df=test_dataframe,
        )
        aero3 = Aerogenerador(
            id_torre="torre1",
            id_aero=2,
            latitud=12.282725,
            longitud=-71.226417,
            elevacion=4,
            modelo="enercon",
            df=test_dataframe,
        )
        aerogeneradores = {1: aero1, 2: aero2, 3: aero3}
        self.densidad_mock = pd.DataFrame({"Densidad": [1.1, 1.2, 1.3]}, index=[1, 2, 3])
        self.caracteristicas_mock = pd.DataFrame({
            "densidad": [1.2, 1.8, 1.6],
            "dist_pcc": [10, 20, 30],
            "t_min": [-10, -10, -10],
            "t_max": [45, 45, 45],
            "p_nominal": [2350, 2350, 2350],
        })
        self.curvas_ds_mock = xr.Dataset(
            data_vars={
                'cur_vel': xr.DataArray(np.array([1, 2, 3]), dims=['turbina'], attrs={'Descripción': 'Curvas velocidad.'}),
                'cur_pot': xr.DataArray(np.array([1, 2, 3]), dims=['turbina'], attrs={'Descripción': 'Curvas potencia.'}),
                'cur_coef': xr.DataArray(np.array([1, 2, 3]), dims=['turbina'], attrs={'Descripción': 'Curvas coeficiente.'}),
            },
            coords={
                'turbina': [1, 2, 3],
                'numero_curvas': np.arange(3),
            }
        )
        self.mock_params = MagicMock()
        self.mock_params.kpc.return_value = 0
        self.mock_params.kt.return_value = 0
        self.mock_params.kin.return_value = 0
        self.mock_params.voltaje.return_value = 36

        self.dataset_mock = crear_estructura_xarray_vectorizado(aerogeneradores, self.serie_tiempo)
        self.dataset_mock['velocidad_estela'] = (['turbina', 'tiempo'], np.array([[8.77, 9.1, 8.88], [8.77, 9.1, 8.88], [8.77, 9.1, 8.88]]).T)
    
    @patch("scipy.interpolate.splev")
    @patch("scipy.interpolate.splrep")
    @patch("utils.eolica.ajuste_potencia.perdidas_cableado")
    @patch("utils.eolica.ajuste_potencia.perdidas_frontera_comercial")
    def test_potencia_vectorizado(self, mock_perdidas, mock_perdidas_frontera,  mock_splrep, mock_splev):
        mock_splev.return_value = 1200
        mock_splrep.return_value = 2
        mock_perdidas.return_value = np.array([1200, 1300, 1400])
        mock_perdidas_frontera.return_value = np.array([1200, 1300, 1400])

        resultado = ajuste_potencia.potencia_vectorizado(
            self.caracteristicas_mock,
            self.dataset_mock,
            self.densidad_mock,
            self.curvas_ds_mock,
            3,
            3,
            self.mock_params,
            0.2
        )
        muestra_pot = resultado.sel(turbina=1)["potencia"].values[0]
        self.assertAlmostEqual(muestra_pot, 1200)
        assert mock_perdidas.call_count == 3
        assert mock_perdidas_frontera.call_count == 3
    
    def test_perdida_cableado(self):
        resultado = ajuste_potencia.perdidas_cableado(36, 0.2, 33, 150.86)
        self.assertAlmostEqual(resultado, -115750.128, places=2)

    def test_perdidas_frontera_comercial(self):
        resultado = ajuste_potencia.perdidas_frontera_comercial(150.86, 0.2, 0.5, 0)
        self.assertAlmostEqual(resultado, 149.8039, places=2)
    
    def mock_pandas_udf(arg1):

        keys = pd.Series([
            100.0,  # Altura promedio del buje en metros
            120.0,
        ])

        estructura_x_info = pd.Series([
            True,  # Indica si es un parque eólico offshore
            False,
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
                result = func(keys, estructura_x_info, densidades)
                # Convertir el resultado a listas, similar a pandas.Series
                return result
            return inner
        return wrapper

    @patch('XM_FERNC_API.utils.workers.pandas_udf', side_effect=mock_pandas_udf)
    @patch("scipy.interpolate.splev")
    @patch("scipy.interpolate.splrep")
    @patch("utils.eolica.ajuste_potencia.perdidas_cableado")
    @patch("utils.eolica.ajuste_potencia.perdidas_frontera_comercial")
    def test_potencia_vectorizado_udf(self, mock_perdidas, mock_perdidas_frontera,  mock_splrep, mock_splev, mock_pandas_udf):
        mock_splev.return_value = 1200
        mock_splrep.return_value = 2
        mock_perdidas.return_value = np.array([1200, 1300, 1400])
        mock_perdidas_frontera.return_value = np.array([1200, 1300, 1400])

        mock_result1 = MagicMock()
        mock_result1.result = ('2023-01-01', 'aero_1', 8.5)
        mock_result2 = MagicMock()
        mock_result2.result = ('2023-01-02', 'aero_2', 7.2)

        df_data = MagicMock()
        potencia_np = MagicMock()

        potencia_np.select.return_value.collect.return_value = [MagicMock(potencia=np.random.uniform(500, 1500, size=10)) for _ in range(5)]


        df_data.withColumn.return_value = potencia_np
        
        
        resultado = potencia_vectorizado_udf(
            df_data,
            self.caracteristicas_mock,
            self.densidad_mock,
            self.curvas_ds_mock,
            self.mock_params,
            0.2
        )
        print(resultado, type(resultado))
        self.assertEqual(resultado.shape, (3, 2))
    
    @patch('scipy.interpolate.splev')
    @patch('scipy.interpolate.splrep')
    def test_calcular_potencia(self, mock_splrep, mock_splev):
        # Datos de prueba
        turbina_id = 1
        temp_vel_ti = 8.0  # Velocidad del viento de prueba
        cur_vel = np.array([0, 5, 10, 15, 20])  # Curvas de velocidad de prueba
        cur_pot = np.array([0, 500, 1500, 2500, 3000])  # Curvas de potencia de prueba

        # Creación de un xarray con las curvas, sin .expand_dims
        curvas_xarray = xr.Dataset({
            "cur_vel": (["velocidad"], cur_vel),
            "cur_pot": (["velocidad"], cur_pot)
        }).assign_coords(turbina=[turbina_id])

        # Mock de splev y splrep
        mock_splrep.return_value = "mocked_tck"
        mock_splev.return_value = 1200.0  # Potencia esperada tras la interpolación

        # Llamada a la función
        result = calcular_potencia(temp_vel_ti, curvas_xarray, turbina_id)

        # Aserciones
        mock_splrep.assert_called_once_with(cur_vel, cur_pot, k=3)
        mock_splev.assert_called_once_with(x=temp_vel_ti, tck="mocked_tck")
        self.assertEqual(result, 1200.0)
    
    @patch('scipy.interpolate.splev')
    @patch('scipy.interpolate.splrep')
    def test_calculate_pot(self, mock_splrep, mock_splev):
        # Datos de prueba
        num_turbinas = 5
        temp_vel_ti = np.array([8.0, 9.0, 10.0, 11.0, 12.0])  # Velocidades del viento para 5 turbinas
        cur_vel = np.array([0, 5, 10, 15, 20])  # Curvas de velocidad de prueba
        cur_pot = np.array([0, 500, 1500, 2500, 3000])  # Curvas de potencia de prueba

        # Creación de un xarray con las curvas, sin .expand_dims
        curvas_xarray = xr.Dataset({
            "cur_vel": (["velocidad"], cur_vel),
            "cur_pot": (["velocidad"], cur_pot)
        }).assign_coords(turbina=list(range(1, num_turbinas + 1)))

        # Mock de splev y splrep
        mock_splrep.return_value = "mocked_tck"
        mock_splev.side_effect = [1200.0, 1300.0, 1400.0, 1500.0, 1600.0]  # Diferentes potencias esperadas para cada turbina

        # Llamada a la función
        result = calculate_pot(temp_vel_ti, curvas_xarray, num_turbinas)

        # Aserciones
        self.assertEqual(result.shape, (num_turbinas,))
        self.assertEqual(result.tolist(), [1200.0, 1300.0, 1400.0, 1500.0, 1600.0])

        # Asegura que se llamó a splrep y splev el número correcto de veces
        self.assertEqual(mock_splev.call_count, num_turbinas)
        mock_splrep.assert_called_with(cur_vel, cur_pot, k=3)
