import unittest
import pandas as pd
import xarray as xr
import numpy as np

from utils.estructura_xarray import (
    crear_estructura_xarray_vectorizado,
    crear_estructura_curvas_xarray,
    crear_estructura_xarray
)
from utils.eolica.dataclasses_eolica import Aerogenerador, Modelo
from infraestructura.models.eolica.parametros import CurvasDelFabricante

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
        
        curvas_fabricante = CurvasDelFabricante(
            SerieVelocidad=1.0,
            SeriePotencia=2.0,
            SerieCoeficiente=0.5,
            SerieVcthCorregida=1.1,
        )

        aero1 = Aerogenerador(
            id_torre="torre1",
            id_aero=1,
            latitud=12.29263,
            longitud=-71.226417,
            elevacion=1,
            modelo="enercon",
            df=test_dataframe,
            curvas_fabricante=[curvas_fabricante]
        )
        aero2 = Aerogenerador(
            id_torre="torre1",
            id_aero=2,
            latitud=12.287679,
            longitud=-71.226417,
            elevacion=2,
            modelo="enercon",
            df=test_dataframe,
            curvas_fabricante=[curvas_fabricante]
        )
        aero3 = Aerogenerador(
            id_torre="torre1",
            id_aero=2,
            latitud=12.282725,
            longitud=-71.226417,
            elevacion=4,
            modelo="enercon",
            df=test_dataframe,
            curvas_fabricante=[curvas_fabricante]
        )
        self.aerogeneradores = {1: aero1, 2: aero2, 3: aero3}

        modelo_aerogenerador = Modelo(
            nombre="enercon",
            altura_buje=80.0,
            diametro_rotor=120.0,
            p_nominal=2000.0,
            v_nominal=15.0,
            den_nominal=1.225,
            v_min=3.0,
            v_max=25.0,
            t_min=-10.0,
            t_max=40.0,
            curvas_fabricante=[curvas_fabricante],
        )

        self.modelos_mock = {"enercon": modelo_aerogenerador}

    def test_crear_estructura_xarray_vectorizado(self):
        resultado = crear_estructura_xarray_vectorizado(self.aerogeneradores, self.serie_tiempo)

        coords_esperadas = ["tiempo", "turbina"]
        data_vars_esperadas = ["densidad", "temperatura_ambiente", "velocidad_viento", "direccion_viento"]

        assert isinstance(resultado, xr.Dataset)
        assert all(coord in resultado.coords for coord in coords_esperadas)
        assert all(data_var in resultado.data_vars for data_var in data_vars_esperadas)

    def test_crear_estructura_curvas_xarray(self):
        resultado = crear_estructura_curvas_xarray(self.aerogeneradores)

        coords_esperadas = ["turbina", "numero_curvas"]
        data_vars_esperadas = ["cur_vel", "cur_pot", "cur_coef"]

        assert isinstance(resultado, xr.Dataset)
        assert all(coord in resultado.coords for coord in coords_esperadas)
        assert all(data_var in resultado.data_vars for data_var in data_vars_esperadas)

    def test_crear_estructura_xarray(self):
        # Actuar
        lon_data, lat_data = crear_estructura_xarray(self.serie_tiempo, self.aerogeneradores)

        # Afirmar que las dimensiones son correctas
        self.assertEqual(lon_data.shape, (len(self.serie_tiempo), len(self.aerogeneradores)))
        self.assertEqual(lat_data.shape, (len(self.serie_tiempo), len(self.aerogeneradores)))

        # Afirmar que los nombres de las dimensiones son correctos
        self.assertListEqual(list(lon_data.dims), ["fecha", "aero_id"])
        self.assertListEqual(list(lat_data.dims), ["fecha", "aero_id"])

        # Afirmar que las coordenadas son correctas
        self.assertTrue(np.array_equal(lon_data.coords['fecha'], self.serie_tiempo))
        self.assertTrue(np.array_equal(lat_data.coords['fecha'], self.serie_tiempo))
        self.assertListEqual(list(lon_data.coords['aero_id']), list(self.aerogeneradores.keys()))
        self.assertListEqual(list(lat_data.coords['aero_id']), list(self.aerogeneradores.keys()))

        # Afirmar que los valores están inicializados a cero
        np.testing.assert_array_equal(lon_data.values, 0)
        np.testing.assert_array_equal(lat_data.values, 0)
