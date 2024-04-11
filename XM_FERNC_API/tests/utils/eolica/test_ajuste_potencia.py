import unittest
import pandas as pd
import xarray as xr
import numpy as np

from unittest.mock import MagicMock, patch

from utils.eolica import ajuste_potencia
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