import unittest
import numpy as np
import pandas as pd

from utils.eolica.caracterizacion_estela import Estela
from utils.eolica.funciones_ordenamiento import Ordenamiento
from utils.eolica.dataclasses_eolica import (
    Aerogenerador,
    Modelo,
    CurvasDelFabricante
)
from dominio.servicio.eolica.servicio_eolicas import ServicioEolicas

from utils.estructura_xarray import (
    crear_estructura_xarray_vectorizado,
    crear_estructura_curvas_xarray
)


class TestEstela(unittest.TestCase):
    def setUp(self):
        self.ordenamiento = Ordenamiento()
        self.servicio_eolica = ServicioEolicas()

        self.df_aero_mock_1 = pd.DataFrame({
            "DireccionViento": [75.25, 78.42, 76.89],
            "PresionAtmosferica": [990.62, 990.62, 990.62],
            "Ta": [28.11, 27.51, 26.88],
            "VelocidadViento": [8.66, 9.73, 9.62],
            "TaBuje": [27.98, 27.38, 26.75],
            "Pbuje": [988.4456646529, 988.4414689457, 988.4370459906],
            "PVapor": [3758.1907090835, 3618.3817199489, 3477.1764141461],
            "PVaporSaturacion": [3757.1799555829, 3627.931883521, 3496.4188680899],
            "DenBuje": [1.1295587332, 1.1324726019, 1.135513778],

        }, index=[
                "2008-01-01 0:00:00+00:00",
                "2008-01-01 02:00:00+00:00",
                "2008-01-01 03:00:00+00:00"
            ]
        )
        self.n_estampas = 3

        cf1 = CurvasDelFabricante(
                SerieVelocidad=1.0286687722951402,
                SeriePotencia=0.0,
                SerieCoeficiente=0.0,
                SerieVcthCorregida=1.0106559414990874
            )
        cf3 = CurvasDelFabricante(
                SerieVelocidad=8.229350178361122,
                SeriePotencia=975.8,
                SerieCoeficiente=0.83,
                SerieVcthCorregida=8.0852475319927
            )
        cf2 = CurvasDelFabricante(
                SerieVelocidad=4.114675089180561,
                SeriePotencia=3.6,
                SerieCoeficiente=1.0,
                SerieVcthCorregida=2.021311882998175
            )

        cf4 = CurvasDelFabricante(
                SerieVelocidad=10.345004101385411,
                SeriePotencia=1817.8,
                SerieCoeficiente=0.71,
                SerieVcthCorregida=10.142330956417958
            )

        self.aerogeneradores_con_df = {
            1: Aerogenerador(
                id_aero=1,
                id_torre="torre_1",
                latitud=12.29263,
                longitud=-71.22642,
                elevacion=1.0,
                modelo="modelo_1",
                dist_pcc=None,
                df=self.df_aero_mock_1,
                f_ordenamiento=0,
                curvas_fabricante=[cf1, cf2, cf3, cf4]
            ),
            2: Aerogenerador(
                id_aero=2,
                id_torre="torre_1",
                latitud=12.28768,
                longitud=-71.22642,
                elevacion=2.0,
                modelo="modelo_1",
                dist_pcc=None,
                df=self.df_aero_mock_1,
                f_ordenamiento=0,
                curvas_fabricante=[cf1, cf2, cf3, cf4]
            ),
        }

        self.modelo_dict = {
            "modelo_1": Modelo(
                nombre="modelo_1",
                altura_buje=80.0,
                diametro_rotor=120.0,
                p_nominal=2000.0,
                v_nominal=15.0,
                den_nominal=1.225,
                v_min=3.0,
                v_max=25.0,
                t_min=-10.0,
                t_max=40.0,
                curvas_fabricante=[cf1, cf2, cf3, cf4],
            ),
        }

    def test_efecto_estela_vectorizado(self):
        dict_ordenamiento = self.ordenamiento.ordenamiento_vectorizado(self.aerogeneradores_con_df, self.n_estampas)
        caracteristicas_df = self.servicio_eolica._ServicioEolicas__caracteristicas_tij(self.aerogeneradores_con_df, self.modelo_dict)
        densidad = pd.DataFrame({key: value.df['DenBuje'] for key, value in self.aerogeneradores_con_df.items()})
        serie_tiempo = self.servicio_eolica.manipulador_df.obtener_serie_tiempo_eolica(self.df_aero_mock_1)
        estructura_xarray = crear_estructura_xarray_vectorizado(self.aerogeneradores_con_df, serie_tiempo)
        n_turbinas = len(self.aerogeneradores_con_df.keys())
        curvas_xarray = crear_estructura_curvas_xarray(self.aerogeneradores_con_df)

        vectores_velocidades = self.servicio_eolica._ServicioEolicas__crear_lista_vectores_velocidades(self.aerogeneradores_con_df, serie_tiempo)
        estructura_xarray["velocidad_grandes_parques"] = (["turbina", "tiempo"], np.array(vectores_velocidades).T, {"Descripción": "Velocidad del viento perturbada por efecto de grandes parques en [m/s]."})

        estela = Estela(True,
                0.02,
                caracteristicas_df,
                densidad,
                estructura_xarray,
                n_turbinas,
                curvas_xarray,
                (1, dict_ordenamiento['2008-01-01 0:00:00+00:00']))

        resultado = estela.efecto_estela_vectorizado()

        resultado_esperado = np.array([9.73, 9.73])
        self.assertTrue(np.allclose(resultado, resultado_esperado))
